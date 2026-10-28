"""Tests for the live in-line game clock in event_input().

These drive the real prompt_toolkit prompt through a pseudo-terminal in a child
process, with a fake tracker whose clock advances, and assert on the text the
prompt finally returns.

Run from the repository root:

    venv/bin/python -m unittest discover -s tests -v
"""

import os
import pty
import select
import shutil
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))

HISTORY_LINES = [
    "11", "Home", "Away", "2024-01-01", "20:00", "Hall",
    "1;2;3", "4;5;6",
    "10955aH5",
    "10950rH7",
]


class _FakeSample:
    def __init__(self, event_time):
        self.event_time = event_time
        self.clock = None if event_time is None else f"{event_time[:2]}:{event_time[2:]}"
        self.video_seconds, self.past_end, self.message = 29.5, False, None

    @property
    def usable(self):
        return self.event_time is not None

    def describe(self):
        return f"video {self.video_seconds}s - game clock {self.clock}"


class _FakeTracker:
    """Yields a new clock value every `tick` seconds, mimicking a playing video."""

    def __init__(self, values, tick=0.6):
        self.values, self.tick, self.start = values, tick, time.monotonic()

    def sample(self):
        index = int((time.monotonic() - self.start) / self.tick)
        value = self.values[min(index, len(self.values) - 1)]
        return _FakeSample(value)


class _StaticTracker:
    def __init__(self, value):
        self.value = value

    def sample(self):
        return _FakeSample(self.value)


class _PhasedTracker:
    """Holds a value until a set time, then switches. Deterministic for edits."""

    def __init__(self, phases):
        self.phases, self.start = phases, time.monotonic()

    def sample(self):
        elapsed = time.monotonic() - self.start
        value = self.phases[0][1]
        for after, candidate in self.phases:
            if elapsed >= after:
                value = candidate
        return _FakeSample(value)


def run_prompt(tracker_factory, keystrokes, quarter="1", settle=1.2, timeout=12):
    """Run event_input() in a pty child; return (result, child_exit_code)."""
    workdir = Path(tempfile.mkdtemp(prefix="evt-"))
    (workdir / "matches").mkdir()
    (workdir / "matches/history.txt").write_text("\n".join(HISTORY_LINES) + "\n")

    read_fd, write_fd = os.pipe()
    pid, master = pty.fork()
    if pid == 0:
        os.close(read_fd)
        try:
            os.chdir(workdir)
            import main as app
            result = app.event_input(quarter, tracker_factory())
            os.write(write_fd, result.encode())
        except BaseException as exc:  # noqa: BLE001 - surfaced to the parent
            import traceback
            os.write(write_fd, f"ERROR:{exc!r}\n{traceback.format_exc()}".encode())
        finally:
            os._exit(0)

    os.close(write_fd)
    stop = threading.Event()
    screen = []

    def drain():
        while not stop.is_set():
            try:
                ready, _, _ = select.select([master], [], [], 0.1)
            except (OSError, ValueError):
                return
            if not ready:
                continue
            try:
                chunk = os.read(master, 4096)
            except OSError:
                return
            if not chunk:
                return
            screen.append(chunk.decode(errors="replace"))

    threading.Thread(target=drain, daemon=True).start()
    time.sleep(settle)
    for keys, pause in keystrokes:
        try:
            os.write(master, keys)
        except OSError:
            break
        time.sleep(pause)

    out = b""
    deadline = time.time() + timeout
    while time.time() < deadline:
        ready, _, _ = select.select([read_fd], [], [], 0.2)
        if ready:
            chunk = os.read(read_fd, 8192)
            if chunk:
                out += chunk
            break

    status = 0
    try:
        _, status = os.waitpid(pid, 0)
    except ChildProcessError:
        pass
    stop.set()
    for fd in (master, read_fd):
        try:
            os.close(fd)
        except OSError:
            pass
    shutil.rmtree(workdir, ignore_errors=True)

    text = out.decode()
    if text.startswith("ERROR:"):
        raise AssertionError(f"prompt raised:\n{text}\nscreen:\n{''.join(screen)}")
    return text, status


ENTER = (b"\r", 0.4)


class LivePrefixTests(unittest.TestCase):
    """The first five characters follow the video; the suffix does not."""

    def test_prefix_updates_while_prompt_is_open(self):
        # Clock walks 09:41 -> 09:40 -> 09:39 while we simply wait.
        result, _ = run_prompt(
            lambda: _FakeTracker(["0941", "0940", "0939"]),
            [(b"", 2.0), ENTER])
        self.assertEqual(result, "10939")

    def test_typed_suffix_is_preserved_while_prefix_updates(self):
        result, _ = run_prompt(
            lambda: _FakeTracker(["0941", "0940", "0939"]),
            [(b"rH10", 0.3), (b"", 1.8), ENTER])
        self.assertTrue(result.endswith("rH10"), result)
        self.assertEqual(len(result), 9, result)
        self.assertNotEqual(result[:5], "10941")

    def test_only_the_prefix_changes(self):
        result, _ = run_prompt(
            lambda: _FakeTracker(["0941", "0940"]),
            [(b"2H5", 0.3), (b"", 1.2), ENTER])
        self.assertEqual(result[5:], "2H5")
        self.assertEqual(result[0], "1")
        self.assertTrue(result[1:5].isdigit(), result)

    def test_cursor_stays_in_the_suffix(self):
        # Type "rH10", move left twice, wait for a tick, then insert "X".
        # The insert must land inside the suffix, not somewhere shifted.
        result, _ = run_prompt(
            lambda: _FakeTracker(["0941", "0940"]),
            [(b"rH10", 0.3), (b"\x1b[D\x1b[D", 0.3), (b"", 1.2), (b"X", 0.3), ENTER])
        self.assertEqual(result[5:], "rHX10", result)

    def test_static_clock_produces_stable_prefix(self):
        result, _ = run_prompt(lambda: _StaticTracker("0941"),
                               [(b"2H5", 0.3), (b"", 1.0), ENTER])
        self.assertEqual(result, "109412H5")


class ManualEditTests(unittest.TestCase):
    """Editing the clock yourself switches the automatic updates off."""

    # Stays on 09:41 long enough to edit, then jumps, so the assertions below
    # do not depend on how fast the prompt starts.
    PHASES = [(0.0, "0941"), (4.0, "0900")]

    def test_clock_would_otherwise_have_changed(self):
        """Control: without a manual edit the prefix follows the jump."""
        result, _ = run_prompt(lambda: _PhasedTracker(self.PHASES),
                               [(b"2H5", 0.3), (b"", 4.5), ENTER])
        self.assertEqual(result, "109002H5")

    def test_editing_prefix_stops_updates(self):
        # Backspace over the whole 5-char prefix and type a different one.
        result, _ = run_prompt(
            lambda: _PhasedTracker(self.PHASES),
            [(b"\x7f" * 5, 0.4), (b"10855", 0.4), (b"", 4.0), (b"2H5", 0.3), ENTER])
        self.assertEqual(result, "108552H5")

    def test_editing_one_prefix_digit_stops_updates(self):
        # Move into the prefix, change its last digit, then wait past the jump.
        result, _ = run_prompt(
            lambda: _PhasedTracker(self.PHASES),
            [(b"\x1b[D", 0.3), (b"\x7f", 0.3), (b"7", 0.3), (b"", 4.5), ENTER])
        self.assertEqual(result, "10971", result)

    def test_suffix_edits_do_not_stop_updates(self):
        result, _ = run_prompt(
            lambda: _PhasedTracker(self.PHASES),
            [(b"rH1", 0.3), (b"\x7f", 0.3), (b"2", 0.3), (b"", 4.0), ENTER])
        self.assertEqual(result, "10900rH2")


class HistoryNavigationTests(unittest.TestCase):
    """Recalled entries must not be overwritten by the clock."""

    def test_up_arrow_entry_is_not_overwritten(self):
        result, _ = run_prompt(
            lambda: _FakeTracker(["0941", "0940", "0939"]),
            [(b"\x1b[A", 0.4), (b"", 1.8), ENTER])
        self.assertEqual(result, HISTORY_LINES[-1])

    def test_tab_prefix_recall_is_not_overwritten(self):
        result, _ = run_prompt(
            lambda: _FakeTracker(["0941", "0940", "0939"]),
            [(b"\t", 0.4), (b"", 1.8), ENTER])
        self.assertEqual(result, HISTORY_LINES[-1][:5])

    def test_tab_full_recall_is_not_overwritten(self):
        result, _ = run_prompt(
            lambda: _FakeTracker(["0941", "0940", "0939"]),
            [(b"\t\t", 0.5), (b"", 1.6), ENTER])
        self.assertEqual(result, HISTORY_LINES[-1])

    def test_tab_back_to_new_event_resumes_the_clock(self):
        # Three tabs cycle back to the new-event state, which follows again.
        result, _ = run_prompt(
            lambda: _FakeTracker(["0941", "0940", "0939"]),
            [(b"\t\t\t", 0.6), (b"", 1.6), ENTER])
        self.assertEqual(result[0], "1")
        self.assertTrue(result[1:5].isdigit(), result)
        self.assertNotIn("a", result)


class ManualFallbackTests(unittest.TestCase):
    """Without usable clock data the prompt stays exactly as it was."""

    def test_no_tracker_keeps_quarter_only(self):
        result, _ = run_prompt(lambda: None, [(b"09412H5", 0.4), ENTER])
        self.assertEqual(result, "109412H5")

    def test_unusable_sample_keeps_quarter_only(self):
        result, _ = run_prompt(lambda: _StaticTracker(None),
                               [(b"09412H5", 0.4), (b"", 0.8), ENTER])
        self.assertEqual(result, "109412H5")

    def test_late_sample_upgrades_untouched_line(self):
        # No reading at first, then one arrives: an untouched line picks it up.
        result, _ = run_prompt(lambda: _FakeTracker([None, None, "0941"], tick=0.5),
                               [(b"", 2.2), ENTER])
        self.assertEqual(result, "10941")

    def test_late_sample_does_not_corrupt_typed_text(self):
        # The user typed the time by hand before a reading appeared; the live
        # updater must leave that line alone rather than splicing a prefix in.
        # The tick has to outlast run_prompt's settle, otherwise the reading
        # lands before the keystrokes and the premise no longer holds.
        result, _ = run_prompt(lambda: _FakeTracker([None, None, "0941"], tick=1.0),
                               [(b"09412H5", 0.4), (b"", 2.4), ENTER])
        self.assertEqual(result, "109412H5")


class TaskCleanupTests(unittest.TestCase):
    """The background task must not keep the prompt or process alive."""

    def test_child_exits_cleanly_after_prompt_returns(self):
        result, status = run_prompt(lambda: _FakeTracker(["0941", "0940"]),
                                    [(b"2H5", 0.3), (b"", 1.0), ENTER])
        self.assertTrue(result.endswith("2H5"))
        self.assertEqual(os.waitstatus_to_exitcode(status), 0)

    def test_no_background_tasks_remain_registered(self):
        """After prompt() returns, the app has no live background tasks."""
        import main as app

        workdir = Path(tempfile.mkdtemp(prefix="evt-"))
        (workdir / "matches").mkdir()
        (workdir / "matches/history.txt").write_text("\n".join(HISTORY_LINES) + "\n")
        cwd = os.getcwd()
        captured = {}

        real_session_cls = app.PromptSession

        class SpySession(real_session_cls):
            def prompt(self, *a, **kw):
                captured["app"] = self.app
                return super().prompt(*a, **kw)

        read_fd, write_fd = os.pipe()
        pid, master = pty.fork()
        if pid == 0:
            try:
                os.chdir(workdir)
                app.PromptSession = SpySession
                app.event_input("1", _StaticTracker("0941"))
                pending = [t for t in captured["app"]._background_tasks
                           if not t.done()]
                os.write(write_fd, str(len(pending)).encode())
            except BaseException:
                os.write(write_fd, b"99")
            finally:
                os._exit(0)

        os.close(write_fd)
        time.sleep(1.5)
        os.write(master, b"2H5\r")
        out = b""
        deadline = time.time() + 10
        while time.time() < deadline:
            ready, _, _ = select.select([read_fd], [], [], 0.2)
            if ready:
                out = os.read(read_fd, 64)
                break
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            pass
        for fd in (master, read_fd):
            try:
                os.close(fd)
            except OSError:
                pass
        os.chdir(cwd)
        shutil.rmtree(workdir, ignore_errors=True)
        self.assertEqual(out.decode(), "0", "background task still pending")


if __name__ == "__main__":
    unittest.main()
