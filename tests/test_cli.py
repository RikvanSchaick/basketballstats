import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app import paths
from app.cli import cmd_open


class SelectTests(unittest.TestCase):
  def test_open_creates_missing_history_file(self):
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
        selected = cmd_open()

      self.assertEqual(selected.matchID, "1234")
      self.assertEqual(history.read_text(), contents + "\n")

  def test_open_warns_about_invalid_lines(self):
    with tempfile.TemporaryDirectory() as tmp:
      matches = Path(tmp)
      history = matches / "history.txt"
      match = matches / "1234.txt"
      home = ";".join(f"{number},Home {number}" for number in range(1, 7))
      away = ";".join(f"{number},Away {number}" for number in range(1, 7))
      lines = ["1234", "Home", "Away", "date", "time", "location", home, away]
      lines += ["edit1", "H1,2,3,4,5", "A1,2,3,4,5", "10528out1inA11", "11000jH"]
      match.write_text("\n".join(lines) + "\n")

      with (
        mock.patch.object(paths, "MATCHES", matches),
        mock.patch.object(paths, "HISTORY", history),
        mock.patch("builtins.input", return_value="1234"),
        mock.patch("builtins.print") as printed,
      ):
        cmd_open()

      output = "\n".join(str(call.args[0]) for call in printed.call_args_list)
      self.assertIn("line 12: 10528out1inA11", output)
      self.assertNotIn("11000jH", output)


if __name__ == "__main__":
  unittest.main()
