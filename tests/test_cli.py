import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app import paths
from app.cli import cmd_select


class SelectTests(unittest.TestCase):
  def test_select_creates_missing_history_file(self):
    with tempfile.TemporaryDirectory() as tmp:
      matches = Path(tmp)
      history = matches / "history.txt"
      match = matches / "1234.txt"
      home = ";".join(f"{number},Home {number}" for number in range(1, 7))
      away = ";".join(f"{number},Away {number}" for number in range(1, 7))
      contents = "\n".join(
        ["1234", "Home", "Away", "date", "time", "location", home, away]
      )
      match.write_text(contents + "\n")

      with (
        mock.patch.object(paths, "MATCHES", matches),
        mock.patch.object(paths, "HISTORY", history),
        mock.patch("builtins.input", return_value="1234"),
      ):
        self.assertFalse(history.exists())
        selected = cmd_select()

      self.assertEqual(selected.matchID, "1234")
      self.assertEqual(history.read_text(), contents + "\n")


if __name__ == "__main__":
  unittest.main()
