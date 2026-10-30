import contextlib
import io
import unittest
from unittest import mock

from app import cli, prompt
from app.cli import menu_choices
from app.prompt import read_key, read_menu_choice


class _Terminal(io.StringIO):
  def isatty(self):
    return True


def run_app(*inputs):
  """Drive the menus with scripted lines (no terminal); return the output."""
  out = io.StringIO()
  with (
    contextlib.redirect_stdout(out),
    mock.patch("sys.stdin", io.StringIO()),
    mock.patch("builtins.input", side_effect=list(inputs)),
  ):
    cli._run_app(cli.parse_args([]), {})
  return out.getvalue()


class MenuChoicesTests(unittest.TestCase):
  def test_start_menu_keys(self):
    self.assertEqual(
      menu_choices("intro"),
      {"c": "create", "o": "open", "s": "stats", "h": "help", "e": "exit"},
    )

  def test_stats_menu_keys(self):
    self.assertEqual(
      menu_choices("stats"),
      {"t": "team", "p": "player", "b": "back", "h": "help", "e": "exit"},
    )

  def test_game_menu_numbers_open_that_quarter(self):
    choices = menu_choices("match")
    for quarter in "12345678":
      self.assertEqual(choices[quarter], f"edit{quarter}")
    self.assertEqual(choices["r"], "report")
    self.assertEqual(choices["x"], "boxscore")
    self.assertEqual(choices["b"], "back")
    self.assertEqual(choices["e"], "exit")

  def test_keys_are_unique_within_every_menu(self):
    for menu, (_, items) in cli.MENUS.items():
      keys = [key for key, _, _ in items]
      self.assertEqual(len(keys), len(set(keys)), menu)


class ReadMenuChoiceTests(unittest.TestCase):
  choices = {"o": "open", "e": "exit"}

  def press(self, *raw):
    """Simulate key presses on a terminal; return (choice, output)."""
    out = io.StringIO()
    with (
      contextlib.redirect_stdout(out),
      mock.patch("sys.stdin", _Terminal()),
      mock.patch.object(prompt, "_read_raw", side_effect=list(raw)),
      mock.patch("builtins.input") as line_input,
    ):
      choice = read_menu_choice(self.choices)
    line_input.assert_not_called()
    return choice, out.getvalue()

  def test_one_key_picks_the_option_without_enter(self):
    choice, output = self.press("o")
    self.assertEqual(choice, "open")
    self.assertIn("open", output)

  def test_uppercase_key_works_too(self):
    self.assertEqual(self.press("E")[0], "exit")

  def test_unknown_key_is_returned_as_is(self):
    self.assertEqual(self.press("q")[0], "q")

  def test_enter_and_arrow_keys_are_skipped(self):
    self.assertEqual(self.press("\n", "\x1b[A", " ", "o")[0], "open")

  def test_without_a_terminal_a_line_is_read(self):
    for line, expected in [
      ("o", "open"),
      ("open", "open"),
      (" E ", "exit"),
      ("x", "x"),
    ]:
      with (
        mock.patch("sys.stdin", io.StringIO()),
        mock.patch("builtins.input", return_value=line),
      ):
        self.assertEqual(read_menu_choice(self.choices), expected, line)

  def test_read_key_returns_lowercase(self):
    with mock.patch.object(prompt, "_read_raw", side_effect=["\x04", "C"]):
      self.assertEqual(read_key(), "c")


class MenuKeyFlowTests(unittest.TestCase):
  def test_back_returns_from_stats_to_start_menu(self):
    with mock.patch.object(cli, "Data") as data:
      data.return_value.n_exports.return_value = True
      output = run_app("s", "b", "h", "e")
    self.assertIn("STATS MENU", output)
    self.assertIn("HOW IT WORKS", output)
    self.assertEqual(output.splitlines().count("START MENU"), 4)
    self.assertNotIn("unknown command", output)

  def test_back_returns_from_match_to_start_and_allows_another_match(self):
    with mock.patch.object(cli, "cmd_open", return_value=cli.Match()):
      output = run_app("o", "b", "h", "o", "b", "e")
    self.assertEqual(output.count("GAME MENU"), 2)
    self.assertIn("HOW IT WORKS", output)
    self.assertNotIn("unknown command", output)

  def test_full_back_command_returns_to_start_menu(self):
    with mock.patch.object(cli, "cmd_open", return_value=cli.Match()):
      output = run_app("open", "back", "exit")
    self.assertEqual(output.splitlines().count("START MENU"), 2)
    self.assertNotIn("unknown command", output)

  def test_boxscore_uses_x_instead_of_b(self):
    with mock.patch.object(cli, "cmd_open", return_value=cli.Match()):
      output = run_app("o", "x", "e")
    self.assertIn("no events", output)
    self.assertNotIn("unknown command", output)

  def test_exit_from_submenus_still_quits_the_program(self):
    with (
      mock.patch.object(cli, "Data") as data,
      mock.patch.object(cli, "cmd_open", return_value=cli.Match()),
    ):
      data.return_value.n_exports.return_value = True
      for command in ("o", "s"):
        with self.subTest(command=command):
          self.assertEqual(run_app(command, "e").splitlines().count("START MENU"), 1)

  def test_back_clears_the_match_clock_tracker(self):
    tracker = mock.Mock()
    holder = {"tracker": tracker}
    with (
      mock.patch.object(cli, "cmd_open", return_value=cli.Match()),
      mock.patch("sys.stdin", io.StringIO()),
      mock.patch("builtins.input", side_effect=["o", "b", "e"]),
      contextlib.redirect_stdout(io.StringIO()),
    ):
      cli._run_app(cli.parse_args([]), holder)
    self.assertIsNone(holder.get("tracker"))
    tracker.stop.assert_called_once()

  def test_e_exits_the_start_menu(self):
    self.assertIn("START MENU", run_app("e"))

  def test_h_shows_the_start_help(self):
    self.assertIn("HOW IT WORKS", run_app("h", "e"))

  def test_game_menu_keys_reach_their_commands(self):
    match = mock.Mock()
    overview = mock.Mock()
    with (
      mock.patch.object(cli, "cmd_open", return_value=match) as cmd_open,
      mock.patch.object(cli, "cmd_edit", return_value=match) as cmd_edit,
      mock.patch.dict(cli.MATCH_COMMANDS, {"overview": overview}),
    ):
      output = run_app("o", "3", "o", "e")
    cmd_open.assert_called_once()
    self.assertEqual(cmd_edit.call_args.args[1], "edit3")
    overview.assert_called_once_with(match)
    self.assertIn("GAME MENU", output)

  def test_stats_menu_keys(self):
    data = mock.Mock()
    data.n_exports.return_value = True
    with (
      mock.patch.object(cli, "Data", return_value=data),
      mock.patch.object(cli, "StatsReport") as report,
    ):
      output = run_app("s", "t", "p", "z", "e")
    report.return_value.export_team_stats.assert_called_once()
    report.return_value.export_player_stats.assert_called_once()
    self.assertIn("unknown command 'z'", output)


if __name__ == "__main__":
  unittest.main()
