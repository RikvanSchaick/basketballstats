import tempfile
import unittest
from pathlib import Path
from unittest import mock

import paths
from data_export import Data


class FilesTests(unittest.TestCase):
  def test_skips_history_and_test_files(self):
    with tempfile.TemporaryDirectory() as tmp:
      for name in ["261017D1.txt", "5617.txt", "history.txt", "test.txt", "notes.md"]:
        (Path(tmp) / name).write_text("")
      with mock.patch.object(paths, "MATCHES", Path(tmp)):
        self.assertEqual(Data().files(), ["5617.txt", "261017D1.txt"])


if __name__ == "__main__":
  unittest.main()
