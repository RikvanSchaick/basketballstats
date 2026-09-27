"""Supplies event times to the basketball app from a video open in QuickTime Player.

Wraps the reusable tracker in ``quicktime_timestamp/tracker.py``: a background
thread keeps the latest QuickTime sample, and :meth:`GameClockTracker.sample`
converts it into the four-digit MMSS value ``event.get_time()`` expects.

Nothing here prints continuously; the caller decides what to show and when.
"""

from __future__ import annotations

import importlib.util
import queue
import sys
import threading
import time
from pathlib import Path

# Loaded by path rather than via sys.path: quicktime_timestamp/ contains its own
# main.py, which would shadow this app's main module if that directory were added
# to sys.path.
_TRACKER_PATH = (Path(__file__).resolve().parent.parent
                 / "quicktime_timestamp" / "tracker.py")


def _load_tracker():
    spec = importlib.util.spec_from_file_location("qt_tracker", _TRACKER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load the QuickTime tracker from {_TRACKER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["qt_tracker"] = module
    spec.loader.exec_module(module)
    return module


tracker = _load_tracker()

DEFAULT_ANCHOR_CLOCK = tracker.DEFAULT_ANCHOR_CLOCK
DEFAULT_INTERVAL = tracker.DEFAULT_INTERVAL
RECOVERABLE_MESSAGES = tracker.RECOVERABLE_MESSAGES
STALE_TIMEOUT = tracker.STALE_TIMEOUT
ClockLogError = tracker.ClockLogError
ClockMap = tracker.ClockMap
Poller = tracker.Poller
discover_csv = tracker.discover_csv
find_anchor_real_time = tracker.find_anchor_real_time
format_wall_clock = tracker.format_wall_clock
load_clock_log = tracker.load_clock_log
parse_anchor_value = tracker.parse_anchor_value
parse_line = tracker.parse_line
read_once = tracker.read_once

__all__ = [
    "ClockLogError",
    "GameClockSample",
    "GameClockTracker",
    "clock_to_event_time",
    "parse_anchor_value",
    "tracker",
    "DEFAULT_ANCHOR_CLOCK",
]

# event.get_time() accepts 00:00-09:59 plus exactly 10:00, so a mapped clock
# outside that range must not be auto-filled into an event string.
MAX_EVENT_TIME = "1000"


def clock_to_event_time(clock):
    """Convert a ``MM:SS`` game clock into the four digits events store.

    Returns ``None`` when the value cannot be represented, so callers fall back
    to manual entry instead of writing an event that fails validation.
    """
    if not isinstance(clock, str):
        return None
    parts = clock.strip().split(":")
    if len(parts) != 2:
        return None
    minutes, seconds = parts[0].strip(), parts[1].strip()
    if not (minutes.isdigit() and seconds.isdigit()):
        return None
    if not 1 <= len(minutes) <= 2 or len(seconds) != 2:
        return None
    if int(seconds) > 59:
        return None
    digits = f"{int(minutes):02d}{seconds}"
    # Mirrors event.get_time(): anything above 10:00 is not a valid game clock.
    if len(digits) != 4 or digits > MAX_EVENT_TIME:
        return None
    return digits


class GameClockSample:
    """One reading of the video, already mapped onto the game clock."""

    def __init__(self, video_seconds, clock=None, event_time=None,
                 past_end=False, document=None, message=None):
        self.video_seconds = video_seconds
        self.clock = clock
        self.event_time = event_time
        self.past_end = past_end
        self.document = document
        self.message = message

    @property
    def usable(self):
        return self.event_time is not None

    def describe(self):
        """Short one-line summary, suitable for a prompt toolbar."""
        if self.message:
            return self.message
        if self.video_seconds is None:
            return "no reading from QuickTime Player"
        if self.clock is None:
            return (f"video {self.video_seconds:.1f}s - before the clock log "
                    "(type the time yourself)")
        suffix = " (end of log)" if self.past_end else ""
        if self.event_time is None:
            return (f"video {self.video_seconds:.1f}s - clock {self.clock}{suffix} "
                    "is not a valid event time")
        return f"video {self.video_seconds:.1f}s - game clock {self.clock}{suffix}"


class GameClockTracker:
    """Background QuickTime poller that hands out game-clock event times."""

    def __init__(self, csv_path=None, anchor_clock=DEFAULT_ANCHOR_CLOCK,
                 anchor=None, interval=DEFAULT_INTERVAL, base_dir=None):
        self.csv_path = csv_path
        self.anchor_clock = anchor_clock
        self.anchor = anchor
        self.interval = interval
        self.base_dir = Path(base_dir) if base_dir else _TRACKER_PATH.parent

        self.times = None
        self.clocks = None
        self.clock_map = None
        self.source_name = None
        self.anchor_document = None

        self._poller = None
        self._thread = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._latest = None
        self._latest_at = 0.0

    # ------------------------------------------------------------------ setup

    def load_csv(self):
        """Resolve and parse the clock log. Raises :class:`ClockLogError`."""
        path = discover_csv(self.csv_path, self.base_dir)
        self.times, self.clocks = load_clock_log(path)
        self.csv_path = path
        self.source_name = path.name
        return path

    def anchor_to_video(self, on_wait=None, retries=None, wait_seconds=2.0):
        """Ask QuickTime for the anchor frame and build the :class:`ClockMap`.

        Waits for QuickTime to have a document open, reporting progress through
        ``on_wait`` so the caller keeps control of the terminal.
        """
        if self.times is None:
            self.load_csv()
        real_time = find_anchor_real_time(self.times, self.clocks, self.anchor_clock)

        status = self._wait_for_document(on_wait, retries, wait_seconds)
        document = status.name

        if self.anchor is not None:
            video_seconds = self.anchor
        else:
            video_seconds, document = self._prompt_for_anchor(retries)

        self.clock_map = ClockMap(self.times, self.clocks, real_time - video_seconds)
        self.anchor_document = document
        return {
            "document": document,
            "video_seconds": video_seconds,
            "real_time": real_time,
            "real_time_text": format_wall_clock(real_time),
            "offset": self.clock_map.offset,
            "csv": self.source_name,
        }

    def _wait_for_document(self, on_wait, retries, wait_seconds):
        attempts = 0
        while True:
            status = read_once()
            if status.kind == "ok":
                return status
            # Only the states the user can clear are worth waiting on.
            if status.message not in RECOVERABLE_MESSAGES:
                raise ClockLogError(status.message)
            attempts += 1
            if retries is not None and attempts >= retries:
                raise ClockLogError(status.message)
            if on_wait:
                on_wait(f"{status.message} - waiting for a video...")
            time.sleep(wait_seconds)

    def _prompt_for_anchor(self, retries):
        attempts = 0
        while True:
            print(f"\nScrub the video to the frame where the game clock first "
                  f"shows {self.anchor_clock},")
            print("pause there, then press Enter.")
            try:
                input()
            except EOFError as exc:
                raise ClockLogError("Anchoring cancelled.") from exc
            # Read fresh after Enter so the value matches what is on screen now.
            status = read_once()
            if status.kind == "ok":
                return status.seconds, status.name
            if status.message not in RECOVERABLE_MESSAGES:
                raise ClockLogError(status.message)
            attempts += 1
            if retries is not None and attempts >= retries:
                raise ClockLogError(status.message)
            print(f"  {status.message} - try again.")

    @property
    def ready(self):
        return self.clock_map is not None

    # ---------------------------------------------------------------- polling

    def start(self):
        if self._thread is not None:
            return
        self._stop.clear()
        self._poller = Poller(self.interval)
        self._poller.start()
        self._latest_at = time.monotonic()
        self._thread = threading.Thread(target=self._consume, daemon=True)
        self._thread.start()

    def _consume(self):
        """Drain the poller, keeping only the most recent sample."""
        while not self._stop.is_set():
            try:
                generation, line = self._poller.queue.get(timeout=0.25)
            except queue.Empty:
                if time.monotonic() - self._latest_at > STALE_TIMEOUT:
                    self._poller.restart()
                    self._latest_at = time.monotonic()
                continue
            if generation != self._poller.generation:
                continue
            if line is None:
                self._poller.restart()
                self._latest_at = time.monotonic()
                continue
            self._latest_at = time.monotonic()
            with self._lock:
                self._latest = parse_line(line)

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None
        if self._poller is not None:
            self._poller.stop()
            self._poller = None
        with self._lock:
            self._latest = None

    # ----------------------------------------------------------------- lookup

    def sample(self):
        """Map the newest QuickTime reading onto a :class:`GameClockSample`.

        Returns ``None`` when the poller has not produced anything yet.
        """
        with self._lock:
            status = self._latest

        if status is None:
            return None
        if status.kind != "ok":
            return GameClockSample(None, message=status.message)
        if not self.ready:
            return GameClockSample(status.seconds, document=status.name,
                                   message="game clock is not anchored yet")
        # A different document means the offset we computed no longer applies.
        if self.anchor_document is not None and status.name != self.anchor_document:
            return GameClockSample(
                status.seconds, document=status.name,
                message=f"video changed to {status.name} - re-anchor needed")

        reading = self.clock_map.lookup(status.seconds)
        if reading is None:
            # Before the first logged row: tracker semantics say "unknown".
            return GameClockSample(status.seconds, document=status.name)
        return GameClockSample(
            status.seconds,
            clock=reading.text,
            event_time=clock_to_event_time(reading.text),
            past_end=reading.past_end,
            document=status.name,
        )

    def document_changed(self):
        """True when QuickTime is showing a different video than we anchored to."""
        with self._lock:
            status = self._latest
        if status is None or status.kind != "ok" or self.anchor_document is None:
            return False
        return status.name != self.anchor_document

    def invalidate_anchor(self):
        self.clock_map = None
        self.anchor_document = None
        self.anchor = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc):
        self.stop()
        return False
