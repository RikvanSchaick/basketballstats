"""Tests for Event.parse(), the history-line grammar.

Run from the repository root:

    .venv/bin/python -m pytest tests/test_event.py
"""

import unittest
from pathlib import Path

from event import Event

ROOT = Path(__file__).resolve().parent.parent

FIELDS = ("quarter", "time", "actionID", "actionID2", "team", "playerID", "playerID2")

VALID = {
  "edit1": ("1", "1000", "start", None, None, None, None),
  "edit5": ("5", "0500", "start", None, None, None, None),
  "4end": ("4", "0000", "end", None, None, None, None),
  "11000jA": ("1", "1000", "j", None, "A", None, None),
  "20500toH": ("2", "0500", "to", None, "H", None, None),
  "10624rA": ("1", "0624", "r", None, "A", None, None),
  "10813rA12": ("1", "0813", "r", None, "A", "12", None),
  "30100ftH": ("3", "0100", "ft", None, "H", None, None),
  "30100ftH5": ("3", "0100", "ft", None, "H", "5", None),
  "10425tH": ("1", "0425", "t", None, "H", None, None),
  "10956tA12": ("1", "0956", "t", None, "A", "12", None),
  "10827tH13sA11": ("1", "0827", "t", "s", "H", "13", "11"),
  "10827tH13bA11": ("1", "0827", "t", "b", "H", "13", "11"),
  "109363H5": ("1", "0936", "3", None, "H", "5", None),
  "104412H8bA17": ("1", "0441", "2", "b", "H", "8", "17"),
  "108392mA12aA4": ("1", "0839", "2m", "a", "A", "12", "4"),
  "103271mH6aH8": ("1", "0327", "1m", "a", "H", "6", "8"),
  "103271mH6": ("1", "0327", "1m", None, "H", "6", None),
  "107581H5": ("1", "0758", "1", None, "H", "5", None),
  "10758f1A11": ("1", "0758", "f1", None, "A", "11", None),
  "50100fdH4": ("5", "0100", "fd", None, "H", "4", None),
  "10624outH7inH11": ("1", "0624", "out", "in", "H", "7", "11"),
}

INVALID = [
  "",
  "edit",
  "edit9",
  "edit1x",
  "9end",
  "1endx",
  "00941rH5",
  "90941rH5",  # quarter outside 1-8
  "11001rH5",
  "10970rH5",
  "1094rH5",  # bad clock
  "10941toH5",
  "10941jA12",  # team-only actions take no player
  "10941f1H",
  "10941outH5",  # player required / missing "in"
  "10941rH123",
  "10941rH5x",  # trailing characters
  "109412mH5aA6",  # assist by an opponent
  "109412H5bH6",
  "10941tH5sH6",  # block/steal by a teammate
  "10941outH5inA6",  # substitution across teams
  "109412H5aH6",
  "109412mH5bA6",  # second action not allowed for this action
  "H5,6,7,9,13",  # starters line, not an event
]


class ParseTests(unittest.TestCase):
  def test_valid_lines(self):
    for line, expected in VALID.items():
      with self.subTest(line=line):
        e = Event.parse(line)
        self.assertIsNotNone(e)
        self.assertEqual(tuple(getattr(e, f) for f in FIELDS), expected)
        self.assertEqual(e.eventstring(), line)

  def test_invalid_lines(self):
    for line in INVALID:
      with self.subTest(line=line):
        self.assertIsNone(Event.parse(line))

  def test_every_saved_match_line_is_an_event_or_a_starters_line(self):
    for path in sorted((ROOT / "matches").glob("*.txt")):
      for line in path.read_text().splitlines()[8:]:
        with self.subTest(match=path.name, line=line):
          self.assertTrue(Event.parse(line) is not None or line[:1] in {"H", "A"})


if __name__ == "__main__":
  unittest.main()
