"""Tests for the per-quarter video sync step in edit-mode.

Entering ``edit<N>`` asks whether the video still lines up with the CSV. Only an
explicit "y" re-anchors; anything else keeps the offset that was already in use.

Run from the repository root:

    venv/bin/python -m unittest discover -s tests -v
"""

import builtins
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))

import main as app  # noqa: E402
from gameclock import ClockLogError  # noqa: E402


class _Options:
    def __init__(self, anchor=None, no_video_clock=False):
        self.anchor = anchor
        self.no_video_clock = no_video_clock
        self.csv = None
        self.anchor_clock = "09:59"


class _FakeTracker:
    """Records how it was driven, without touching QuickTime."""

    def __init__(self, ready=True, changed=False, fail=False):
        self._ready = ready
        self._changed = changed
        self.fail = fail
        self.quarters = []
        self.anchored = []
        self.invalidated = 0
        self.stopped = 0

    @property
    def ready(self):
        return self._ready

    def set_quarter(self, quarter):
        self.quarters.append(quarter)
        return int(quarter)

    def document_changed(self):
        return self._changed

    def invalidate_anchor(self):
        self.invalidated += 1
        self._ready = False

    def anchor_to_video(self, quarter=None, on_wait=None):
        if self.fail:
            raise ClockLogError("no video")
        self.anchored.append(quarter)
        self._ready = True
        self._changed = False
        return {
            "document": "game.mov",
            "video_seconds": 12.5,
            "real_time": 70406.0,
            "real_time_text": "19:33:26.046",
            "offset": 70393.5,
            "csv": "log.csv",
            "anchor_clock": "09:59",
            "quarter": int(quarter) if quarter is not None else None,
        }

    def stop(self):
        self.stopped += 1


class SyncPromptBase(unittest.TestCase):
    def setUp(self):
        self.answers = []
        self.asked = []
        self.printed = []

        def fake_input(prompt=""):
            self.asked.append(prompt)
            if not self.answers:
                raise EOFError
            return self.answers.pop(0)

        def fake_print(*args, **kwargs):
            self.printed.append(" ".join(str(a) for a in args))

        self.enter(mock.patch.object(builtins, "input", fake_input))
        # main.py calls the builtin print; a module-level name shadows it.
        self.enter(mock.patch.object(app, "print", fake_print, create=True))
        self.set_tty(True)

    def enter(self, patcher):
        patcher.start()
        self.addCleanup(patcher.stop)

    def set_tty(self, value):
        self.enter(mock.patch.object(app.sys, "stdin", _Stdin(value)))

    def output(self):
        return "\n".join(self.printed)


class _Stdin:
    def __init__(self, tty):
        self._tty = tty

    def isatty(self):
        return self._tty


class AskSyncTests(SyncPromptBase):
    """Only a typed "y" means "re-sync"."""

    def answer(self, text):
        self.answers = [text]
        return app.ask_sync(2)

    def test_y_triggers_a_sync(self):
        self.assertTrue(self.answer("y"))

    def test_y_is_case_and_space_insensitive(self):
        for text in ("Y", " y ", "y\t"):
            with self.subTest(text=text):
                self.assertTrue(self.answer(text))

    def test_n_skips(self):
        self.assertFalse(self.answer("n"))

    def test_empty_answer_skips(self):
        self.assertFalse(self.answer(""))

    def test_arbitrary_text_skips(self):
        for text in ("yes", "no", "maybe", "1", "yy"):
            with self.subTest(text=text):
                self.assertFalse(self.answer(text))

    def test_eof_skips(self):
        self.answers = []
        self.assertFalse(app.ask_sync(2))

    def test_prompt_names_the_quarter(self):
        self.answer("n")
        self.assertIn("quarter 2", self.asked[-1])


class SyncQuarterTests(SyncPromptBase):
    """The answer decides whether the offset is recomputed."""

    def test_yes_re_anchors_on_that_quarter(self):
        t = _FakeTracker()
        self.answers = ["y"]
        self.assertIs(app.sync_quarter(t, "3", _Options()), t)
        self.assertEqual(t.anchored, ["3"])
        self.assertEqual(t.invalidated, 1)

    def test_no_keeps_the_previous_sync(self):
        t = _FakeTracker()
        self.answers = ["n"]
        self.assertIs(app.sync_quarter(t, "3", _Options()), t)
        self.assertEqual(t.anchored, [])
        self.assertEqual(t.invalidated, 0)
        self.assertIn("keeping the current sync", self.output())

    def test_empty_and_arbitrary_answers_keep_the_previous_sync(self):
        for text in ("", "no", "yes", "x"):
            with self.subTest(text=text):
                t = _FakeTracker()
                self.answers = [text]
                app.sync_quarter(t, "2", _Options())
                self.assertEqual(t.anchored, [])

    def test_quarter_is_handed_to_the_tracker_either_way(self):
        for text in ("y", "n"):
            with self.subTest(text=text):
                t = _FakeTracker()
                self.answers = [text]
                app.sync_quarter(t, "4", _Options())
                self.assertEqual(t.quarters, ["4"])

    def test_unanchored_tracker_syncs_without_asking(self):
        t = _FakeTracker(ready=False)
        app.sync_quarter(t, "1", _Options())
        self.assertEqual(self.asked, [])
        self.assertEqual(t.anchored, ["1"])

    def test_changed_video_syncs_without_asking(self):
        t = _FakeTracker(changed=True)
        app.sync_quarter(t, "2", _Options())
        self.assertEqual(self.asked, [])
        self.assertEqual(t.anchored, ["2"])
        self.assertIn("different video", self.output())

    def test_explicit_anchor_option_skips_the_question(self):
        t = _FakeTracker()
        self.assertIs(app.sync_quarter(t, "2", _Options(anchor=12.0)), t)
        self.assertEqual(self.asked, [])
        self.assertEqual(t.anchored, [])

    def test_non_interactive_stdin_skips_the_question(self):
        self.set_tty(False)
        t = _FakeTracker()
        self.assertIs(app.sync_quarter(t, "2", _Options()), t)
        self.assertEqual(self.asked, [])
        self.assertEqual(t.anchored, [])

    def test_failed_sync_falls_back_to_manual(self):
        t = _FakeTracker(fail=True)
        self.answers = ["y"]
        self.assertIsNone(app.sync_quarter(t, "2", _Options()))
        self.assertEqual(t.stopped, 1)
        self.assertIn("type the times yourself", self.output())

    def test_failed_forced_sync_does_not_raise(self):
        t = _FakeTracker(ready=False, fail=True)
        self.assertIsNone(app.sync_quarter(t, "2", _Options()))
        self.assertEqual(t.stopped, 1)

    def test_cancelled_sync_falls_back_to_manual(self):
        class Cancelling(_FakeTracker):
            def anchor_to_video(self, quarter=None, on_wait=None):
                raise KeyboardInterrupt

        t = Cancelling()
        self.answers = ["y"]
        self.assertIsNone(app.sync_quarter(t, "2", _Options()))
        self.assertEqual(t.stopped, 1)


class SetupTrackerTests(SyncPromptBase):
    """The first quarter of a session anchors without asking anything."""

    def test_no_video_clock_returns_none(self):
        self.assertIsNone(app.setup_tracker(_Options(no_video_clock=True), "1"))
        self.assertEqual(self.asked, [])


if __name__ == "__main__":
    unittest.main()
