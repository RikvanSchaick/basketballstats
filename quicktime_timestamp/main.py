#!/usr/bin/env python3
"""Standalone terminal tracker: prints QuickTime's timestamp and the game clock.

All of the QuickTime, CSV and mapping logic lives in :mod:`tracker`; this module
is only the command line front end.
"""

from __future__ import annotations

import argparse
import queue
import sys
import time
from pathlib import Path

from tracker import (
    CALIBRATION_SAMPLES,
    CALIBRATION_WARMUP,
    DEFAULT_ANCHOR_CLOCK,
    DEFAULT_INTERVAL,
    STALE_TIMEOUT,
    ClockLogError,
    Poller,
    Status,
    discover_csv,
    ensure_osascript,
    load_clock_log,
    parse_anchor_value,
    parse_line,
    resolve_anchor,
)


class Printer:
    """Writes updates to the terminal, reusing one line when attached to a TTY."""

    def __init__(self, stream, source_name=None):
        self.stream = stream
        self.source_name = source_name
        self.interactive = stream.isatty()
        self.width = 0
        self.last_text = None
        self.last_document = None

    def announce_document(self, status):
        if status.kind != "ok" or status.name is None:
            return
        marker = (status.name, status.duration)
        if marker == self.last_document:
            return
        self.last_document = marker
        self._finish_line()
        line = f"Tracking: {status.name} (duration {status.duration:.3f}s)"
        if self.source_name:
            line += f" against {self.source_name}"
        self.stream.write(line + "\n")
        self.stream.flush()

    def update(self, status):
        self.announce_document(status)
        if status.kind != "ok":
            self.last_document = None

        text = status.render()
        if self.interactive:
            padding = " " * max(0, self.width - len(text))
            self.stream.write("\r" + text + padding)
            self.stream.flush()
            self.width = len(text)
        elif text != self.last_text:
            # Without a TTY, only log real changes so piped output stays readable.
            self.stream.write(text + "\n")
            self.stream.flush()
        self.last_text = text

    def _finish_line(self):
        if self.interactive and self.width:
            self.stream.write("\n")
            self.width = 0

    def close(self):
        self._finish_line()
        self.stream.flush()


def run(interval, clock_map, source_name):
    if not ensure_osascript():
        return 1

    printer = Printer(sys.stdout, source_name=source_name)
    poller = Poller(interval)
    poller.start()
    last_sample = time.monotonic()
    calibrated = False
    sample_times = []

    try:
        while True:
            try:
                generation, line = poller.queue.get(timeout=0.25)
            except queue.Empty:
                if time.monotonic() - last_sample > STALE_TIMEOUT:
                    printer.update(Status("error", message="QuickTime Player is not responding, reconnecting..."))
                    poller.restart()
                    last_sample = time.monotonic()
                    sample_times.clear()
                continue

            if generation != poller.generation:
                continue

            if line is None:
                printer.update(Status("error", message="Lost the connection to QuickTime Player, reconnecting..."))
                poller.restart()
                last_sample = time.monotonic()
                sample_times.clear()
                continue

            last_sample = time.monotonic()
            status = parse_line(line)
            if status.kind == "ok":
                status.clock = clock_map.lookup(status.seconds)
            printer.update(status)

            # Calibrate on a steady run of real samples, then leave the rate alone.
            if calibrated:
                continue
            if status.kind != "ok":
                sample_times.clear()
                continue
            sample_times.append(last_sample)
            if len(sample_times) >= CALIBRATION_SAMPLES:
                periods = [b - a for a, b in zip(sample_times, sample_times[1:])]
                poller.calibrate(periods[CALIBRATION_WARMUP:])
                calibrated = True
                sample_times.clear()
    except KeyboardInterrupt:
        return 0
    finally:
        printer.close()
        poller.stop()


def main():
    parser = argparse.ArgumentParser(
        description="Print the current playback timestamp and game clock of the "
                    "video open in QuickTime Player."
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_INTERVAL,
        help="Seconds between polls (default: %(default)s, about 10 updates per second).",
    )
    parser.add_argument(
        "--csv",
        help="Game-clock CSV. Defaults to the single time_*.csv next to main.py.",
    )
    parser.add_argument(
        "--anchor-clock",
        default=DEFAULT_ANCHOR_CLOCK,
        help="Game clock value used to line the CSV up with the video "
             "(default: %(default)s).",
    )
    parser.add_argument(
        "--anchor",
        help="Video timestamp showing --anchor-clock, as seconds, MM:SS.mmm or "
             "HH:MM:SS.mmm. Prompts interactively when omitted.",
    )
    args = parser.parse_args()

    if args.interval <= 0:
        parser.error("--interval must be greater than 0")

    anchor = None
    if args.anchor is not None:
        try:
            anchor = parse_anchor_value(args.anchor)
        except ValueError as exc:
            parser.error(f"--anchor: {exc}")

    # Assumes the video runs at real-time speed with no cuts, so a single anchor
    # is enough to map the whole recording onto the logged wall clock.
    if not ensure_osascript():
        return 1

    try:
        csv_path = discover_csv(args.csv, Path(__file__).resolve().parent)
        times, clocks = load_clock_log(csv_path)
        clock_map = resolve_anchor(anchor, args.anchor_clock, times, clocks)
    except ClockLogError as exc:
        print(exc, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 0

    return run(args.interval, clock_map, csv_path.name)


if __name__ == "__main__":
    sys.exit(main())
