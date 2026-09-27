"""Tests for game-clock autofill: CSV lookup, event prefix, and fallbacks.

Run from the repository root:

    venv/bin/python -m unittest discover -s tests -v
"""

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))

from event import event  # noqa: E402
from gameclock import (  # noqa: E402
    ClockLogError,
    GameClockSample,
    GameClockTracker,
    clock_to_event_time,
    tracker,  # the shared tracker module, loaded by gameclock
)

SAMPLE_CSV = ROOT / "quicktime_timestamp" / "time_B.O.B.VSE-1.csv"


def build_map(anchor_video_seconds, anchor_clock="09:59"):
    times, clocks = tracker.load_clock_log(SAMPLE_CSV)
    real = tracker.find_anchor_real_time(times, clocks, anchor_clock)
    return tracker.ClockMap(times, clocks, real - anchor_video_seconds)


class ClockLookupTests(unittest.TestCase):
    """CSV -> game clock, including the stoppage the acceptance check calls out."""

    def setUp(self):
        # Anchor so that video 10.000s is the frame showing 09:59.
        self.map = build_map(10.0)

    def video_at(self, wall_clock):
        return tracker.parse_wall_clock(wall_clock) - self.map.offset

    def test_clock_held_during_stoppage(self):
        # 09:41 is logged at 13:53:43.410 and holds until 13:53:50.209.
        self.assertEqual(self.map.lookup(self.video_at("13:53:45.000")).text, "09:41")

    def test_clock_advances_after_stoppage(self):
        self.assertEqual(self.map.lookup(self.video_at("13:53:50.500")).text, "09:40")

    def test_row_boundaries_are_inclusive_at_start(self):
        self.assertEqual(self.map.lookup(self.video_at("13:53:43.410")).text, "09:41")
        self.assertEqual(self.map.lookup(self.video_at("13:53:50.208")).text, "09:41")
        self.assertEqual(self.map.lookup(self.video_at("13:53:50.209")).text, "09:40")

    def test_anchor_frame_maps_to_anchor_clock(self):
        self.assertEqual(self.map.lookup(10.0).text, "09:59")

    def test_before_log_returns_none(self):
        self.assertIsNone(self.map.lookup(self.video_at("13:00:00.000")))

    def test_after_log_returns_last_value_marked_past_end(self):
        reading = self.map.lookup(self.video_at("14:30:00.000"))
        self.assertEqual(reading.text, "08:55")
        self.assertTrue(reading.past_end)

    def test_last_row_itself_is_marked_past_end(self):
        reading = self.map.lookup(self.video_at("13:54:52.399"))
        self.assertEqual(reading.text, "08:55")
        self.assertTrue(reading.past_end)

    def test_seeking_backwards_returns_earlier_value(self):
        later = self.map.lookup(self.video_at("13:53:50.500")).text
        earlier = self.map.lookup(self.video_at("13:53:45.000")).text
        self.assertEqual((later, earlier), ("09:40", "09:41"))


class EventTimeConversionTests(unittest.TestCase):
    """MM:SS -> the four digits event.get_time() stores."""

    def test_typical_value(self):
        self.assertEqual(clock_to_event_time("09:41"), "0941")

    def test_zero_padding(self):
        self.assertEqual(clock_to_event_time("0:07"), "0007")
        self.assertEqual(clock_to_event_time("00:00"), "0000")

    def test_upper_bound_allowed(self):
        self.assertEqual(clock_to_event_time("10:00"), "1000")

    def test_values_above_ten_minutes_rejected(self):
        for value in ("10:01", "11:00", "12:00", "99:59"):
            with self.subTest(value=value):
                self.assertIsNone(clock_to_event_time(value))

    def test_malformed_values_rejected(self):
        for value in ("", "941", "09:4", "09:60", "ab:cd", "09:41:00", None, 941,
                      "-1:00", "09;41", "  ", "09:-1"):
            with self.subTest(value=value):
                self.assertIsNone(clock_to_event_time(value))

    def test_whitespace_tolerated(self):
        self.assertEqual(clock_to_event_time(" 09:41 "), "0941")


class EventStringPrefixTests(unittest.TestCase):
    """The produced prefix must satisfy the real event parser."""

    def assert_prefix_accepted(self, quarter, clock, expected_prefix):
        prefix = f"{quarter}{clock_to_event_time(clock)}"
        self.assertEqual(prefix, expected_prefix)
        e = event()
        self.assertTrue(e.get_quarter(prefix + "2H5"))
        self.assertTrue(e.get_time(prefix + "2H5"))
        self.assertEqual(e.quarter, str(quarter))
        self.assertEqual(e.time, expected_prefix[1:])

    def test_documented_example(self):
        # Quarter 1 at 09:41 must produce "10941".
        self.assert_prefix_accepted(1, "09:41", "10941")

    def test_all_supported_periods(self):
        for quarter in range(1, 9):
            with self.subTest(quarter=quarter):
                self.assert_prefix_accepted(quarter, "09:41", f"{quarter}0941")

    def test_full_event_string_round_trips(self):
        e = event()
        self.assertTrue(e.extract_eventstring("10941" + "2H5"))
        self.assertEqual((e.quarter, e.time), ("1", "0941"))

    def test_ten_minute_prefix_accepted_by_event(self):
        e = event()
        self.assertTrue(e.get_time("11000" + "2H5"))
        self.assertEqual(e.time, "1000")

    def test_every_csv_clock_value_is_a_valid_event_time(self):
        _, clocks = tracker.load_clock_log(SAMPLE_CSV)
        for clock in clocks:
            with self.subTest(clock=clock):
                digits = clock_to_event_time(clock)
                self.assertIsNotNone(digits)
                e = event()
                self.assertTrue(e.get_time(f"1{digits}2H5"))


class SampleFallbackTests(unittest.TestCase):
    """GameClockSample reports usability and a human-readable reason."""

    def test_usable_sample(self):
        s = GameClockSample(29.5, clock="09:41", event_time="0941")
        self.assertTrue(s.usable)
        self.assertIn("09:41", s.describe())

    def test_before_log_is_not_usable(self):
        s = GameClockSample(1.0)
        self.assertFalse(s.usable)
        self.assertIn("before the clock log", s.describe())

    def test_past_end_is_still_usable_but_flagged(self):
        s = GameClockSample(99.0, clock="08:55", event_time="0855", past_end=True)
        self.assertTrue(s.usable)
        self.assertIn("end of log", s.describe())

    def test_error_message_wins(self):
        s = GameClockSample(None, message="QuickTime Player is not running")
        self.assertFalse(s.usable)
        self.assertEqual(s.describe(), "QuickTime Player is not running")

    def test_out_of_range_clock_is_not_usable(self):
        s = GameClockSample(5.0, clock="12:00", event_time=clock_to_event_time("12:00"))
        self.assertFalse(s.usable)
        self.assertIn("not a valid event time", s.describe())


class TrackerFallbackTests(unittest.TestCase):
    """Tracker behaviour when QuickTime or the anchor is unavailable."""

    def make_tracker(self):
        t = GameClockTracker(csv_path=SAMPLE_CSV)
        t.load_csv()
        return t

    def test_sample_without_any_reading(self):
        self.assertIsNone(self.make_tracker().sample())

    def test_sample_reports_quicktime_error(self):
        t = self.make_tracker()
        t._latest = tracker.Status("error", message=tracker.MSG_NOT_RUNNING)
        s = t.sample()
        self.assertFalse(s.usable)
        self.assertEqual(s.describe(), tracker.MSG_NOT_RUNNING)

    def test_sample_before_anchoring(self):
        t = self.make_tracker()
        t._latest = tracker.Status("ok", seconds=10.0, name="a.mov")
        s = t.sample()
        self.assertFalse(s.usable)
        self.assertIn("not anchored", s.describe())

    def test_sample_after_anchoring(self):
        t = self.make_tracker()
        t.clock_map = build_map(10.0)
        t.anchor_document = "a.mov"
        t._latest = tracker.Status("ok", seconds=10.0, name="a.mov")
        s = t.sample()
        self.assertTrue(s.usable)
        self.assertEqual((s.clock, s.event_time), ("09:59", "0959"))

    def test_changed_video_refuses_to_reuse_offset(self):
        t = self.make_tracker()
        t.clock_map = build_map(10.0)
        t.anchor_document = "a.mov"
        t._latest = tracker.Status("ok", seconds=10.0, name="other.mov")
        s = t.sample()
        self.assertFalse(s.usable)
        self.assertIn("re-anchor", s.describe())
        self.assertTrue(t.document_changed())

    def test_invalidate_anchor_clears_state(self):
        t = self.make_tracker()
        t.clock_map = build_map(10.0)
        t.anchor_document = "a.mov"
        t.invalidate_anchor()
        self.assertFalse(t.ready)
        self.assertIsNone(t.anchor_document)

    def test_missing_anchor_clock_raises(self):
        t = self.make_tracker()
        t.anchor_clock = "99:99"
        with self.assertRaises(ClockLogError):
            t.anchor_to_video(retries=1)

    def test_stop_is_safe_without_start(self):
        self.make_tracker().stop()


class CsvDiscoveryTests(unittest.TestCase):
    """Discovery and malformed-file handling surface clear errors."""

    def test_explicit_path(self):
        t = GameClockTracker(csv_path=SAMPLE_CSV)
        self.assertEqual(t.load_csv().name, SAMPLE_CSV.name)

    def test_missing_file(self):
        with self.assertRaises(ClockLogError):
            GameClockTracker(csv_path="/nope/missing.csv").load_csv()

    def test_no_csv_in_directory(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ClockLogError) as ctx:
                GameClockTracker(base_dir=d).load_csv()
            self.assertIn("No time_*.csv", str(ctx.exception))

    def test_several_files_listed_when_non_interactive(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("time_a.csv", "time_b.csv"):
                (Path(d) / name).write_text(SAMPLE_CSV.read_text())
            with self.assertRaises(ClockLogError) as ctx:
                GameClockTracker(base_dir=d).load_csv()
            self.assertIn("time_a.csv", str(ctx.exception))
            self.assertIn("time_b.csv", str(ctx.exception))

    def test_malformed_csv_rejected(self):
        bad = {
            "empty": "real_time,game_clock\n",
            "missing column": "real_time,clock\n13:00:00.000,10:00\n",
            "bad time": "real_time,game_clock\n13:00:00.000,10:00\nnope,09:59\n",
            "blank cell": "real_time,game_clock\n13:00:00.000,\n",
        }
        with tempfile.TemporaryDirectory() as d:
            for label, body in bad.items():
                path = Path(d) / f"{label.replace(' ', '_')}.csv"
                path.write_text(body)
                with self.subTest(label=label):
                    with self.assertRaises(ClockLogError):
                        GameClockTracker(csv_path=path).load_csv()

    def test_midnight_wrap_stays_monotonic(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "time_wrap.csv"
            path.write_text("real_time,game_clock\n"
                            "23:59:58.000,10:00\n"
                            "23:59:59.500,09:59\n"
                            "00:00:01.250,09:58\n")
            t = GameClockTracker(csv_path=path)
            t.load_csv()
            self.assertEqual(t.times, sorted(t.times))
            self.assertAlmostEqual(t.times[-1] - t.times[0], 3.25, places=3)


if __name__ == "__main__":
    unittest.main()
