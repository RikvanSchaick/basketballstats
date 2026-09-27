#!/usr/bin/env python3
"""Reusable QuickTime Player playback tracking and game-clock mapping.

The video is never opened or decoded in Python. A long-lived ``osascript`` helper
process polls QuickTime Player over Apple events and streams the result back.

This module holds everything reusable: the AppleScript queries, the CSV clock log
parsing, :class:`ClockMap` and the background :class:`Poller`. ``main.py`` builds
the standalone terminal tracker on top of it, and ``code/gameclock.py`` reuses it
for the basketball event-entry workflow.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import math
import queue
import shutil
import statistics
import subprocess
import sys
import threading
import time
from pathlib import Path

DEFAULT_INTERVAL = 0.1
DEFAULT_ANCHOR_CLOCK = "09:59"
STALE_TIMEOUT = 3.0
RESTART_DELAY = 0.5

# Each poll costs an Apple event round trip (~60 ms) on top of the scripted delay,
# so the delay is trimmed once at runtime to hit the requested rate.
CALIBRATION_SAMPLES = 10
CALIBRATION_WARMUP = 2
CALIBRATION_THRESHOLD = 0.005

# AppleScript error numbers worth translating into human readable advice.
ERR_NOT_AUTHORIZED = -1743
ERR_APP_NOT_RUNNING = -600
ERR_CONNECTION_INVALID = -609
ERR_NO_OBJECT = -1728

AUTOMATION_HINT = (
    "Not allowed to control QuickTime Player. Grant Automation access in "
    "System Settings > Privacy & Security > Automation, then restart this program."
)

# The only two states a user can clear by acting in QuickTime and trying again.
# Anything else is reported and aborts rather than looping on the anchor prompt.
MSG_NOT_RUNNING = "QuickTime Player is not running"
MSG_NO_DOCUMENT = "No video is open in QuickTime Player"
RECOVERABLE_MESSAGES = (MSG_NOT_RUNNING, MSG_NO_DOCUMENT)

# Timestamps are streamed as integer milliseconds on purpose. AppleScript renders
# reals using the system locale (on a nl_NL Mac "83.45" becomes "83,45") and falls
# back to scientific notation for small values, neither of which float() accepts.
QUERY_BODY = """\
\t\tset payload to ""
\t\ttry
\t\t\tif application "QuickTime Player" is running then
\t\t\t\ttell application "QuickTime Player"
\t\t\t\t\tif (count of documents) is 0 then
\t\t\t\t\t\tset payload to "NODOC"
\t\t\t\t\telse
\t\t\t\t\t\ttell document 1
\t\t\t\t\t\t\tset tMs to (round ((current time) * 1000))
\t\t\t\t\t\t\tset dMs to (round ((duration) * 1000))
\t\t\t\t\t\t\tset isPlaying to playing
\t\t\t\t\t\t\tset docName to name
\t\t\t\t\t\tend tell
\t\t\t\t\t\tif isPlaying then
\t\t\t\t\t\t\tset pFlag to "1"
\t\t\t\t\t\telse
\t\t\t\t\t\t\tset pFlag to "0"
\t\t\t\t\t\tend if
\t\t\t\t\t\tset payload to "OK" & tab & (tMs as string) & tab & pFlag & ¬
\t\t\t\t\t\t\ttab & (dMs as string) & tab & docName
\t\t\t\t\tend if
\t\t\t\tend tell
\t\t\telse
\t\t\t\tset payload to "NOTRUNNING"
\t\t\tend if
\t\ton error errMsg number errNum
\t\t\tset payload to "ERR" & tab & (errNum as string) & tab & errMsg
\t\tend try
"""

APPLESCRIPT = "\non run\n\trepeat\n" + QUERY_BODY + """\t\tlog payload
\t\tdelay INTERVAL
\tend repeat
end run
"""

# Same query, run once, used to capture the anchor timestamp without waiting on
# (and possibly reading a stale sample from) the streaming poller.
ONE_SHOT_APPLESCRIPT = "\non run\n" + QUERY_BODY + "\treturn payload\nend run\n"


class Status:
    """A single parsed sample coming back from QuickTime Player."""

    def __init__(self, kind, seconds=None, playing=False, duration=None, name=None,
                 message=None, clock=None):
        self.kind = kind
        self.seconds = seconds
        self.playing = playing
        self.duration = duration
        self.name = name
        self.message = message
        self.clock = clock

    def render(self):
        if self.kind != "ok":
            return self.message
        state = "playing" if self.playing else "paused"
        if self.clock is None:
            clock_text = "--:--"
        elif self.clock.past_end:
            clock_text = f"{self.clock.text} (end of log)"
        else:
            clock_text = self.clock.text
        return (
            f"Current timestamp: {self.seconds:.3f}s  |  "
            f"Game clock: {clock_text}  [{state}]"
        )


def parse_line(line):
    """Turn one helper output line into a :class:`Status`."""
    parts = line.split("\t")
    tag = parts[0]

    if tag == "OK" and len(parts) >= 5:
        try:
            time_ms = int(parts[1])
            duration_ms = int(parts[3])
        except ValueError:
            return Status("error", message="Received an unreadable timestamp from QuickTime Player")
        return Status(
            "ok",
            seconds=time_ms / 1000.0,
            playing=parts[2] == "1",
            duration=duration_ms / 1000.0,
            name=parts[4],
        )

    if tag == "NOTRUNNING":
        return Status("error", message=MSG_NOT_RUNNING)

    if tag == "NODOC":
        return Status("error", message=MSG_NO_DOCUMENT)

    if tag == "ERR" and len(parts) >= 3:
        try:
            number = int(parts[1])
        except ValueError:
            number = 0
        detail = parts[2].strip()
        if number == ERR_NOT_AUTHORIZED:
            return Status("error", message=AUTOMATION_HINT)
        if number == ERR_APP_NOT_RUNNING or number == ERR_CONNECTION_INVALID:
            return Status("error", message=MSG_NOT_RUNNING)
        if number == ERR_NO_OBJECT:
            return Status("error", message=MSG_NO_DOCUMENT)
        return Status("error", message=f"QuickTime Player error {number}: {detail}")

    return Status("error", message="QuickTime Player is temporarily unavailable")


def build_script(interval):
    # Fixed-point on purpose: repr() would emit "1e-05" for small values, which
    # AppleScript cannot parse as a number.
    return APPLESCRIPT.replace("INTERVAL", f"{float(interval):.6f}")


class ClockLogError(Exception):
    """Raised when the game-clock CSV cannot be used."""


def parse_wall_clock(value):
    """Parse ``HH:MM:SS.mmm`` into seconds since midnight."""
    parts = value.strip().split(":")
    if len(parts) != 3:
        raise ValueError(f"expected HH:MM:SS.mmm, got {value!r}")
    hours, minutes = int(parts[0]), int(parts[1])
    seconds = float(parts[2])
    if not (0 <= hours < 24 and 0 <= minutes < 60 and 0 <= seconds < 60):
        raise ValueError(f"out-of-range time {value!r}")
    return hours * 3600 + minutes * 60 + seconds


def parse_anchor_value(value):
    """Accept plain seconds, ``MM:SS.mmm`` or ``HH:MM:SS.mmm`` for --anchor."""
    text = value.strip()
    parts = text.split(":")
    seconds = None
    try:
        if len(parts) == 1:
            seconds = float(parts[0])
        elif len(parts) == 2:
            minutes, rest = int(parts[0]), float(parts[1])
            if minutes < 0 or not 0 <= rest < 60:
                raise ValueError
            seconds = minutes * 60 + rest
        elif len(parts) == 3:
            seconds = parse_wall_clock(text)
    except ValueError:
        seconds = None

    # math.isfinite guards against "nan"/"inf", which float() happily accepts and
    # which would silently poison every later bisect lookup.
    if seconds is None or not math.isfinite(seconds) or seconds < 0:
        raise ValueError(
            f"cannot read {value!r} as a non-negative seconds, MM:SS.mmm or "
            "HH:MM:SS.mmm value"
        )
    return seconds


def load_clock_log(path):
    """Read the CSV into parallel (times, clocks) lists, handling a midnight wrap."""
    try:
        with open(path, newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
    except OSError as exc:
        raise ClockLogError(f"Could not read {path}: {exc}") from exc

    if not rows:
        raise ClockLogError(f"{path} contains no rows")

    fields = rows[0].keys()
    for column in ("real_time", "game_clock"):
        if column not in fields:
            raise ClockLogError(
                f"{path} is missing the '{column}' column "
                f"(found: {', '.join(str(f) for f in fields)})"
            )

    times, clocks = [], []
    wrap = 0.0
    previous = None
    for number, row in enumerate(rows, start=2):
        raw_time = (row.get("real_time") or "").strip()
        clock = (row.get("game_clock") or "").strip()
        if not raw_time or not clock:
            raise ClockLogError(f"{path} line {number}: empty real_time or game_clock")
        try:
            seconds = parse_wall_clock(raw_time)
        except ValueError as exc:
            raise ClockLogError(f"{path} line {number}: {exc}") from exc

        # A row earlier than its predecessor means the recording crossed midnight.
        if previous is not None and seconds + wrap < previous:
            wrap += 86400.0
        seconds += wrap
        if previous is not None and seconds < previous:
            raise ClockLogError(
                f"{path} line {number}: real_time {raw_time} still goes backwards "
                "after midnight-wrap handling"
            )
        previous = seconds
        times.append(seconds)
        clocks.append(clock)

    return times, clocks


def discover_csv(explicit, directory):
    """Resolve --csv, or find the single time_*.csv sitting next to main.py."""
    if explicit:
        path = Path(explicit).expanduser()
        if not path.is_file():
            raise ClockLogError(f"CSV not found: {path}")
        return path

    candidates = sorted(directory.glob("time_*.csv"))
    if not candidates:
        raise ClockLogError(
            f"No time_*.csv found in {directory}. Pass one with --csv PATH."
        )
    if len(candidates) == 1:
        return candidates[0]

    if not sys.stdin.isatty():
        listing = "\n".join(f"  {c.name}" for c in candidates)
        raise ClockLogError(
            f"Several game-clock files found in {directory}:\n{listing}\n"
            "Choose one with --csv PATH."
        )

    print("Several game-clock files found:")
    for index, candidate in enumerate(candidates, start=1):
        print(f"  {index}. {candidate.name}")
    while True:
        try:
            reply = input(f"Pick one [1-{len(candidates)}]: ").strip()
        except EOFError as exc:
            raise ClockLogError("No CSV selected.") from exc
        if reply.isdigit() and 1 <= int(reply) <= len(candidates):
            return candidates[int(reply) - 1]
        print("Please enter one of the listed numbers.")


class ClockReading:
    """A game clock value plus whether it sits past the end of the log."""

    def __init__(self, text, past_end=False):
        self.text = text
        self.past_end = past_end


class ClockMap:
    """Maps a video timestamp onto the game clock that was showing at that moment."""

    def __init__(self, times, clocks, offset):
        self.times = times
        self.clocks = clocks
        self.offset = offset

    def lookup(self, video_seconds):
        index = bisect.bisect_right(self.times, video_seconds + self.offset) - 1
        if index < 0:
            return None
        return ClockReading(self.clocks[index], past_end=index == len(self.clocks) - 1)


def find_anchor_real_time(times, clocks, anchor_clock):
    """Real time of the first row showing ``anchor_clock``."""
    for seconds, clock in zip(times, clocks):
        if clock == anchor_clock:
            return seconds
    raise ClockLogError(
        f"Game clock {anchor_clock!r} never appears in the CSV. "
        "Pick a value that does with --anchor-clock."
    )


class Poller:
    """Owns the ``osascript`` helper process and exposes its output as a queue."""

    def __init__(self, interval):
        self.interval = interval
        self.delay = interval
        self.queue = queue.Queue()
        self.process = None
        self.reader = None
        self.generation = 0

    def start(self):
        self.generation += 1
        generation = self.generation
        self.process = subprocess.Popen(
            ["osascript", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.process.stdin.write(build_script(self.delay))
        self.process.stdin.close()

        self.reader = threading.Thread(
            target=self._pump, args=(self.process, generation), daemon=True
        )
        self.reader.start()

    def _pump(self, process, generation):
        for line in process.stderr:
            line = line.rstrip("\n")
            if line:
                self.queue.put((generation, line))
        self.queue.put((generation, None))

    def stop(self):
        if self.process is None:
            return
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
        self.process = None

    def restart(self, pause=True):
        self.stop()
        # Samples still queued by the previous reader belong to an old generation
        # and are filtered out by the caller, so only the pacing matters here.
        if pause:
            time.sleep(RESTART_DELAY)
        self.start()

    def calibrate(self, periods):
        """Trim the scripted delay so the observed rate matches the requested one."""
        overhead = statistics.median(periods) - self.delay
        corrected = min(max(self.interval - overhead, 0.0), self.interval)
        if abs(corrected - self.delay) < CALIBRATION_THRESHOLD:
            return False
        self.delay = corrected
        self.restart(pause=False)
        return True


def read_once(timeout=10.0):
    """Run a single osascript query and return the resulting :class:`Status`."""
    try:
        result = subprocess.run(
            ["osascript", "-"],
            input=ONE_SHOT_APPLESCRIPT,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return Status("error", message="QuickTime Player did not answer in time")
    except OSError as exc:
        return Status("error", message=f"Could not run osascript: {exc}")

    payload = result.stdout.strip()
    if not payload:
        detail = result.stderr.strip() or "no response"
        return Status("error", message=f"QuickTime Player is unavailable ({detail})")
    return parse_line(payload)


def resolve_anchor(anchor, anchor_clock, times, clocks):
    """Work out the offset between video time and the CSV's wall clock."""
    real_time = find_anchor_real_time(times, clocks, anchor_clock)

    if anchor is not None:
        video_seconds = anchor
    else:
        if not sys.stdin.isatty():
            raise ClockLogError(
                "No terminal available to prompt for the anchor. Pass --anchor SECONDS."
            )
        prompt = (
            f"Scrub the video to the frame where the game clock first shows "
            f"{anchor_clock},\npause there, then press Enter."
        )
        while True:
            print(prompt)
            try:
                input()
            except EOFError as exc:
                raise ClockLogError("Anchoring cancelled.") from exc
            status = read_once()
            if status.kind == "ok":
                video_seconds = status.seconds
                break
            # Only re-prompt for states the user can clear in QuickTime. Anything
            # else (denied permission, a timeout, a failed osascript run) cannot be
            # fixed by pressing Enter again, so report it instead of looping.
            if status.message not in RECOVERABLE_MESSAGES:
                raise ClockLogError(status.message)
            print(f"  {status.message} - try again.\n")

    offset = real_time - video_seconds
    print(
        f"Anchored: video {video_seconds:.3f}s = game clock {anchor_clock} "
        f"at {format_wall_clock(real_time)} (offset {offset:+.3f}s)"
    )
    return ClockMap(times, clocks, offset)


def format_wall_clock(seconds):
    seconds %= 86400.0
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{secs:06.3f}"

def ensure_osascript():
    if shutil.which("osascript") is None:
        print("osascript was not found. This program only runs on macOS.", file=sys.stderr)
        return False
    return True

