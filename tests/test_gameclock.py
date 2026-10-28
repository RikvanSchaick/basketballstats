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
    find_quarter_anchor,
    normalise_period,
    tracker,  # the shared tracker module, loaded by gameclock
)

SAMPLE_CSV = ROOT / "quicktime_timestamp" / "260926M1.csv"

# A miniature log with the same shape as the real one: a quarter that opens on a
# static value, ticks, is interrupted by a Timeout with its own countdown, then
# resumes and hands over to the next quarter through a Break.
PERIOD_CSV = """\
real_time,game_clock,period
19:00:00.000,10:00,Pregame
19:00:10.000,10:00,1
19:00:11.000,09:59,1
19:00:12.000,09:58,1
19:00:13.000,09:57,1
19:00:20.000,01:00,Timeout
19:00:21.000,00:59,Timeout
19:00:30.000,09:57,1
19:00:31.000,09:56,1
19:00:40.000,02:00,Break
19:00:41.000,01:59,Break
19:00:50.000,05:00,2
19:00:51.000,04:59,2
19:00:52.000,04:58,2
"""

NO_PERIOD_CSV = """\
real_time,game_clock
19:00:10.000,10:00
19:00:11.000,09:59
19:00:12.000,09:58
"""


def write_csv(directory, name, body):
    path = Path(directory) / name
    path.write_text(body)
    return path


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
        # 07:55 is logged at 19:36:40.258 and holds until 19:37:18.061.
        self.assertEqual(self.map.lookup(self.video_at("19:37:00.000")).text, "07:55")

    def test_clock_advances_after_stoppage(self):
        self.assertEqual(self.map.lookup(self.video_at("19:37:18.500")).text, "07:54")

    def test_row_boundaries_are_inclusive_at_start(self):
        self.assertEqual(self.map.lookup(self.video_at("19:36:40.258")).text, "07:55")
        self.assertEqual(self.map.lookup(self.video_at("19:37:18.061")).text, "07:55")
        self.assertEqual(self.map.lookup(self.video_at("19:37:18.062")).text, "07:54")

    def test_anchor_frame_maps_to_anchor_clock(self):
        self.assertEqual(self.map.lookup(10.0).text, "09:59")

    def test_before_log_returns_none(self):
        self.assertIsNone(self.map.lookup(self.video_at("13:00:00.000")))

    def test_after_log_returns_last_value_marked_past_end(self):
        reading = self.map.lookup(self.video_at("23:00:00.000"))
        self.assertEqual(reading.text, "05:00")
        self.assertTrue(reading.past_end)

    def test_last_row_itself_is_marked_past_end(self):
        reading = self.map.lookup(self.video_at("21:11:16.927"))
        self.assertEqual(reading.text, "05:00")
        self.assertTrue(reading.past_end)

    def test_seeking_backwards_returns_earlier_value(self):
        later = self.map.lookup(self.video_at("19:37:18.500")).text
        earlier = self.map.lookup(self.video_at("19:37:00.000")).text
        self.assertEqual((later, earlier), ("07:54", "07:55"))


class PeriodColumnTests(unittest.TestCase):
    """The optional 'period' column is parsed, normalised and stays optional."""

    def test_quarter_numbers_become_ints(self):
        self.assertEqual(normalise_period("1"), 1)
        self.assertEqual(normalise_period(" 4 "), 4)

    def test_context_labels_stay_strings(self):
        for label in tracker.PERIOD_CONTEXTS:
            with self.subTest(label=label):
                self.assertEqual(normalise_period(label), label)

    def test_empty_cell_is_none(self):
        for value in ("", "   ", None):
            with self.subTest(value=value):
                self.assertIsNone(normalise_period(value))

    def test_periods_are_loaded(self):
        with tempfile.TemporaryDirectory() as d:
            path = write_csv(d, "time_p.csv", PERIOD_CSV)
            times, clocks, periods = tracker.load_clock_log(path, with_periods=True)
            self.assertEqual(len(times), len(clocks))
            self.assertEqual(len(periods), len(clocks))
            self.assertEqual(periods[0], "Pregame")
            self.assertEqual(periods[1], 1)
            self.assertEqual(periods[5], "Timeout")
            self.assertEqual(periods[-1], 2)

    def test_csv_without_the_column_still_loads(self):
        with tempfile.TemporaryDirectory() as d:
            path = write_csv(d, "time_n.csv", NO_PERIOD_CSV)
            times, clocks, periods = tracker.load_clock_log(path, with_periods=True)
            self.assertEqual(clocks, ["10:00", "09:59", "09:58"])
            self.assertEqual(periods, [None, None, None])
            self.assertFalse(tracker.ClockMap(times, clocks, 0.0,
                                              periods=periods).has_periods)

    def test_default_return_is_still_a_pair(self):
        with tempfile.TemporaryDirectory() as d:
            path = write_csv(d, "time_p.csv", PERIOD_CSV)
            self.assertEqual(len(tracker.load_clock_log(path)), 2)

    def test_real_csv_carries_periods(self):
        _, _, periods = tracker.load_clock_log(SAMPLE_CSV, with_periods=True)
        self.assertIn(1, periods)
        self.assertIn("Timeout", periods)
        self.assertIn("Half Time", periods)


class QuarterAnchorTests(unittest.TestCase):
    """Anchoring uses the first tick after a quarter starts, not its opener."""

    def setUp(self):
        self.times, self.clocks, self.periods = tracker.load_clock_log(
            SAMPLE_CSV, with_periods=True)

    def anchor(self, quarter):
        return find_quarter_anchor(self.times, self.clocks, self.periods, quarter)

    def test_regulation_quarter(self):
        clock, _ = self.anchor(1)
        self.assertEqual(clock, "09:59")

    def test_every_regulation_quarter_starts_at_the_same_tick(self):
        for quarter in (1, 2, 3, 4):
            with self.subTest(quarter=quarter):
                self.assertEqual(self.anchor(quarter)[0], "09:59")

    def test_later_quarters_anchor_later_in_the_log(self):
        reals = [self.anchor(q)[1] for q in (1, 2, 3, 4)]
        self.assertEqual(reals, sorted(reals))

    def test_stoppage_rows_are_skipped(self):
        # Quarter 2 is preceded by a Break counting 02:00 down; the anchor must
        # not land on one of those rows.
        _, real = self.anchor(2)
        index = self.times.index(real)
        self.assertEqual(self.periods[index], 2)

    def test_overtime_uses_its_own_opening_value(self):
        # The log stops right after overtime tips off, so only 05:00 exists.
        clock, _ = self.anchor(5)
        self.assertEqual(clock, "05:00")

    def test_short_overtime_anchors_on_its_first_tick(self):
        with tempfile.TemporaryDirectory() as d:
            path = write_csv(d, "time_p.csv", PERIOD_CSV)
            times, clocks, periods = tracker.load_clock_log(path, with_periods=True)
            self.assertEqual(find_quarter_anchor(times, clocks, periods, 2)[0],
                             "04:59")

    def test_string_quarter_accepted(self):
        self.assertEqual(self.anchor("3")[0], self.anchor(3)[0])

    def test_missing_quarter_raises(self):
        with self.assertRaises(ClockLogError) as ctx:
            self.anchor(9)
        self.assertIn("Quarter 9", str(ctx.exception))

    def test_non_numeric_quarter_raises(self):
        with self.assertRaises(ClockLogError):
            self.anchor("half")

    def test_missing_period_column_raises(self):
        with self.assertRaises(ClockLogError):
            find_quarter_anchor(self.times, self.clocks, [None] * len(self.times), 1)


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
        """No CSV value may produce an event string the parser would reject.

        The real log contains the odd scoreboard glitch (a stray 40:00), so the
        rule is not "everything converts" but "whatever converts is accepted,
        and the rest is refused outright rather than silently mistyped".
        """
        _, clocks = tracker.load_clock_log(SAMPLE_CSV)
        converted = 0
        for clock in set(clocks):
            with self.subTest(clock=clock):
                digits = clock_to_event_time(clock)
                if digits is None:
                    self.assertFalse(GameClockSample(1.0, clock=clock).usable)
                    continue
                converted += 1
                e = event()
                self.assertTrue(e.get_time(f"1{digits}2H5"))
        self.assertGreater(converted, 100)


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


class QuarterMappingTests(unittest.TestCase):
    """Only rows belonging to the quarter being edited may fill an event time."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        path = write_csv(self.dir.name, "time_p.csv", PERIOD_CSV)
        self.t = GameClockTracker(csv_path=path)
        self.t.load_csv()
        # Anchor so a video timestamp equals its wall-clock second in the log.
        self.t.clock_map = tracker.ClockMap(self.t.times, self.t.clocks, 0.0,
                                            periods=self.t.periods)
        self.t.anchor_document = "a.mov"

    def sample_at(self, wall_clock, quarter):
        self.t.set_quarter(quarter)
        self.t._latest = tracker.Status(
            "ok", seconds=tracker.parse_wall_clock(wall_clock), name="a.mov")
        return self.t.sample()

    def test_row_in_the_edited_quarter_is_used(self):
        s = self.sample_at("19:00:12.500", 1)
        self.assertTrue(s.usable)
        self.assertEqual((s.clock, s.event_time), ("09:58", "0958"))

    def test_timeout_uses_the_frozen_game_clock_not_the_countdown(self):
        # The row itself reads 00:59 (the timeout's own countdown); the clock
        # the scorer needs is the 09:57 the quarter was stopped at.
        s = self.sample_at("19:00:21.500", 1)
        self.assertTrue(s.usable)
        self.assertEqual((s.clock, s.event_time), ("09:57", "0957"))

    def test_break_before_the_next_quarter_belongs_to_the_previous_one(self):
        s = self.sample_at("19:00:41.500", 1)
        self.assertTrue(s.usable)
        self.assertEqual(s.clock, "09:56")

    def test_stoppage_of_another_quarter_is_refused(self):
        s = self.sample_at("19:00:21.500", 2)
        self.assertFalse(s.usable)
        self.assertIn("not quarter 2", s.describe())

    def test_row_of_another_quarter_is_refused(self):
        s = self.sample_at("19:00:51.500", 1)
        self.assertFalse(s.usable)
        self.assertIn("not quarter 1", s.describe())

    def test_pregame_before_any_quarter_is_refused(self):
        s = self.sample_at("19:00:05.000", 1)
        self.assertFalse(s.usable)
        self.assertIn("before quarter 1", s.describe())

    def test_without_a_quarter_the_raw_row_is_used(self):
        # Standalone / legacy behaviour: no quarter set, so no filtering.
        s = self.sample_at("19:00:21.500", None)
        self.assertTrue(s.usable)
        self.assertEqual(s.clock, "00:59")

    def test_csv_without_periods_is_never_filtered(self):
        path = write_csv(self.dir.name, "time_n.csv", NO_PERIOD_CSV)
        t = GameClockTracker(csv_path=path)
        t.load_csv()
        self.assertFalse(t.has_periods)
        t.clock_map = tracker.ClockMap(t.times, t.clocks, 0.0, periods=t.periods)
        t.anchor_document = "a.mov"
        t.set_quarter(3)
        t._latest = tracker.Status(
            "ok", seconds=tracker.parse_wall_clock("19:00:11.500"), name="a.mov")
        s = t.sample()
        self.assertTrue(s.usable)
        self.assertEqual(s.clock, "09:59")

    def test_set_quarter_normalises(self):
        self.assertEqual(self.t.set_quarter("4"), 4)
        self.assertIsNone(self.t.set_quarter(None))
        self.assertIsNone(self.t.set_quarter("end"))

    def test_anchor_row_is_quarter_specific(self):
        self.t.set_quarter(2)
        self.assertEqual(self.t.anchor_row()[0], "04:59")

    def test_anchor_row_falls_back_without_a_quarter(self):
        self.t.set_quarter(None)
        self.assertEqual(self.t.anchor_row()[0], self.t.anchor_clock)


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
