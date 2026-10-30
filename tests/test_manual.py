import contextlib
import io
import re
import unittest
from unittest import mock

from app import cli, manual
from app.cli import ask_quarters, normalize_event_line, parse_args
from app.model.event import Event


def run_app(*inputs):
  """Drive the menus with scripted input and return everything printed."""
  out = io.StringIO()
  with (
    contextlib.redirect_stdout(out),
    mock.patch("sys.stdin", io.StringIO()),
    mock.patch("builtins.input", side_effect=list(inputs)),
  ):
    cli._run_app(parse_args([]), {})
  return out.getvalue()


class HelpWordTests(unittest.TestCase):
  def test_menu_help_words(self):
    for word in ["help", "HELP", " ? ", "h"]:
      self.assertTrue(manual.is_help(word), word)
    for word in ["", "hel", "open", "exit"]:
      self.assertFalse(manual.is_help(word), word)

  def test_event_help_ignores_the_prefilled_clock(self):
    for line in ["1help", "10839help", "1?", "help", "1 help"]:
      self.assertTrue(manual.is_event_help(line), line)
    for line in ["1", "108392mA12", "1end", "10839h"]:
      self.assertFalse(manual.is_event_help(line), line)


class EventHelpTests(unittest.TestCase):
  def test_every_example_is_a_valid_event(self):
    for quarter in "12345678":
      text = manual.event_help(quarter)
      examples = re.findall(rf"\b{quarter}[0-9]{{4}}[a-zA-Z0-9]+", text)
      self.assertGreater(len(examples), 20)
      for example in examples:
        with self.subTest(quarter=quarter, example=example):
          self.assertIsNotNone(Event.parse(example))


class MenuHelpTests(unittest.TestCase):
  def test_start_menu_mentions_help(self):
    output = run_app("exit")
    self.assertIn("help", output)

  def test_start_menu_help_explains_commands(self):
    output = run_app("help", "exit")
    self.assertIn(manual.TOPICS["start"], output)

  def test_unknown_command_is_reported(self):
    output = run_app("selct", "exit")
    self.assertIn("unknown command 'selct'", output)

  def test_empty_command_just_shows_the_menu_again(self):
    output = run_app("", "exit")
    self.assertNotIn("unknown command", output)


class AskQuartersTests(unittest.TestCase):
  def setUp(self):
    self.match = mock.Mock()
    self.match.all_quarters.return_value = ["1", "2"]

  def ask(self, reply):
    out = io.StringIO()
    with (
      contextlib.redirect_stdout(out),
      mock.patch("builtins.input", return_value=reply),
    ):
      return ask_quarters(self.match), out.getvalue()

  def test_empty_reply_means_all_quarters(self):
    self.assertEqual(self.ask("")[0], ["1", "2"])

  def test_comma_separated_quarters(self):
    self.assertEqual(self.ask("2, 1")[0], ["2", "1"])

  def test_unknown_quarter_is_reported(self):
    quarters, output = self.ask("1,3")
    self.assertIsNone(quarters)
    self.assertIn("3", output)
    self.assertIn("1,2", output)


class NormalizeEventLineTests(unittest.TestCase):
  def test_end_with_prefilled_clock(self):
    self.assertEqual(normalize_event_line("10839end", "1"), "1end")
    self.assertEqual(normalize_event_line(" 1end ", "1"), "1end")

  def test_oncourt_with_prefilled_clock(self):
    self.assertEqual(normalize_event_line("10839oncourt", "1"), "1oncourt")

  def test_end_of_another_quarter_is_left_alone(self):
    self.assertEqual(normalize_event_line("20839end", "1"), "20839end")

  def test_events_are_left_alone(self):
    self.assertEqual(normalize_event_line("108392mA12aA4", "1"), "108392mA12aA4")


class CommandLineHelpTests(unittest.TestCase):
  def test_help_shows_a_quick_start(self):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), self.assertRaises(SystemExit):
      parse_args(["--help"])
    self.assertIn("quick start", out.getvalue().lower())


if __name__ == "__main__":
  unittest.main()
