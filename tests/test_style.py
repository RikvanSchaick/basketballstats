import contextlib
import io
import os
import unittest
from types import SimpleNamespace
from unittest import mock

from app import cli, manual, prompt, style

# Built from the constants, so changing a color in style.py keeps tests green.
TITLE = f"\033[1;{style.color_code(style.TITLE_COLOR)}m"
BODY = f"\033[3;{style.color_code(style.BODY_COLOR)}m"
COMMAND = f"\033[{style.color_code(style.COMMAND_COLOR)}m"


class _Terminal(io.StringIO):
  def isatty(self):
    return True


def capture(func, *args, terminal=True, env=None):
  """Run func with stdout as a (fake) terminal; return what it printed."""
  out = _Terminal() if terminal else io.StringIO()
  env = {"NO_COLOR": "", "FORCE_COLOR": "", "TERM": "xterm-256color", **(env or {})}
  with contextlib.redirect_stdout(out), mock.patch.dict(os.environ, env):
    func(*args)
  return out.getvalue()


class EnabledTests(unittest.TestCase):
  def test_hex_colors_become_24_bit_codes(self):
    self.assertEqual(style.color_code("#4969B3"), "38;2;73;105;179")
    self.assertEqual(style.color_code("#ba3901"), "38;2;186;57;1")

  def test_styled_on_a_terminal(self):
    self.assertIn("\033[", capture(cli.prints, "intro"))

  def test_plain_when_output_is_not_a_terminal(self):
    self.assertNotIn("\033[", capture(cli.prints, "intro", terminal=False))

  def test_no_color_turns_styling_off(self):
    self.assertNotIn("\033[", capture(cli.prints, "intro", env={"NO_COLOR": "1"}))

  def test_dumb_terminal_gets_plain_text(self):
    self.assertNotIn("\033[", capture(cli.prints, "intro", env={"TERM": "dumb"}))

  def test_force_color_styles_redirected_output(self):
    output = capture(cli.prints, "intro", terminal=False, env={"FORCE_COLOR": "1"})
    self.assertIn("\033[", output)


class StyledTextTests(unittest.TestCase):
  def test_styling_never_changes_the_words(self):
    texts = list(manual.TOPICS.values()) + [cli.QUICK_START]
    for text in texts:
      self.assertEqual(
        style.strip(capture(lambda: print(style.manual(text)))), text + "\n"
      )
    for quarter in "15":
      styled = capture(lambda: print(cli.event_help(quarter)))
      self.assertEqual(style.strip(styled), manual.event_help(quarter) + "\n")
    for menu in cli.MENUS:
      plain = capture(cli.prints, menu, terminal=False)
      self.assertEqual(style.strip(capture(cli.prints, menu)), plain)

  def test_menu_titles_are_bold_and_descriptions_italic(self):
    output = capture(cli.prints, "intro")
    self.assertIn(f"{TITLE}START MENU", output)
    self.assertIn(f"{BODY}create a new game", output)
    self.assertIn(f"{COMMAND}create\033[0m", output)

  def test_help_headings_commands_and_quoted_commands(self):
    output = capture(lambda: print(style.manual(manual.TOPICS["start"])))
    self.assertIn(f"{TITLE}HOW IT WORKS", output)
    self.assertIn(f"{COMMAND}open\033[0m     ", output)
    self.assertIn(f"{COMMAND}'create'\033[0m", output)

  def test_event_codes_stand_out(self):
    output = capture(lambda: print(cli.event_help("2")))
    for code in ["204392mA12aA4", "20439outH7inH11", "2end", "2oncourt"]:
      self.assertIn(f"{COMMAND}{code}\033[0m", output)
    self.assertIn(f"{TITLE}EVENT CODES", output)


class EventHelpInEditTests(unittest.TestCase):
  def edit(self, quarter, *lines):
    """Run edit<quarter> with scripted event lines; return what it printed."""
    m = mock.Mock(events=[], matchID="test")
    m.count_events.return_value = 2
    rebuilt = mock.Mock()
    rebuilt.check_boxscore.return_value = False
    options = SimpleNamespace(no_video_clock=True)
    out = _Terminal()
    self.append_history = mock.Mock()
    with (
      contextlib.redirect_stdout(out),
      mock.patch.dict(os.environ, {"NO_COLOR": "", "FORCE_COLOR": "", "TERM": "xterm"}),
      mock.patch.object(cli, "read_history", return_value=[f"edit{quarter}"]),
      mock.patch.object(cli, "append_history", self.append_history),
      mock.patch.object(cli, "event_input", side_effect=list(lines)),
      mock.patch.object(cli.Match, "from_history", return_value=rebuilt),
    ):
      cli.cmd_edit(m, f"edit{quarter}", options, {})
    return out.getvalue()

  def test_help_while_entering_events_shows_the_codes(self):
    output = style.strip(self.edit("1", "10839help", "1end"))
    self.assertIn(manual.event_help("1"), output)
    self.assertNotIn(mock.call("10839help"), self.append_history.call_args_list)

  def test_add_events_title_with_instruction_below(self):
    output = self.edit("1", "1end")
    self.assertIn(f"{TITLE}ADD EVENTS\033[0m\n{BODY}enter 'end' to stop\033[0m", output)

  def test_invalid_event_points_to_help_of_this_quarter(self):
    output = self.edit("3", "3nonsense", "3end")
    self.assertIn(f"{BODY}{manual.invalid_event('3')}\033[0m", output)
    self.assertIn("'3help'", manual.invalid_event("3"))


class GameClockMessageTests(unittest.TestCase):
  def test_title_then_each_line_italic(self):
    output = capture(lambda: print(style.message("GAME CLOCK", "a\nb", "c")))
    expected = (
      f"{TITLE}GAME CLOCK\033[0m\n{BODY}a\033[0m\n{BODY}b\033[0m\n{BODY}c\033[0m\n"
    )
    self.assertEqual(output, expected)

  def test_missing_csv_is_reported_below_the_title(self):
    options = SimpleNamespace(
      no_video_clock=False, csv=None, anchor_clock="10:00", anchor=None
    )
    error = prompt.ClockLogError("No time_*.csv found in /x. Pass one with --csv PATH.")
    tracker = mock.Mock()
    tracker.load_csv.side_effect = error
    with mock.patch.object(prompt, "GameClockTracker", return_value=tracker):
      output = capture(prompt.setup_tracker, options, "1")
    self.assertIn(
      f"\n{TITLE}GAME CLOCK\033[0m\n{BODY}No time_*.csv found in /x. Pass one with "
      f"--csv PATH.\033[0m\n{BODY}Continuing without automatic clock times; "
      "type them yourself.\033[0m",
      output,
    )
    self.assertNotIn("GAME CLOCK:", style.strip(output))


if __name__ == "__main__":
  unittest.main()
