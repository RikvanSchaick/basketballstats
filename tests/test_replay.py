"""Replay saved matches and compare against the saved gamebooks.

data/matches/*.txt and data/gamebooks/txt/ are mostly git-ignored, so these tests cover
whatever is present locally and skip when nothing is. The `test` match is a
scratch file for manual testing and is left out.
"""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app import paths
from app.reports.gamebook import GameReport
from app.model.match import Match

IGNORED = {"history", "test"}
MATCHES = sorted(p for p in paths.MATCHES.glob("*.txt") if p.stem not in IGNORED)
GAMEBOOKS = sorted(
  p
  for p in paths.GAMEBOOKS_TXT.glob("*_gamebook.txt")
  if p.name.split("_")[0] not in IGNORED
)


def load(match_id):
  return Match.from_history(paths.match_file(match_id).read_text().splitlines())


def gamebook_final_score(text):
  """FINAL column of the first PERIOD SCORES table (the full-game box score)."""
  lines = text.splitlines()
  i = next(n for n, line in enumerate(lines) if line.startswith("PERIOD SCORES"))
  return [int(lines[i + 1].split()[-1]), int(lines[i + 2].split()[-1])]


class ReplayTests(unittest.TestCase):
  def setUp(self):
    if not MATCHES:
      self.skipTest("no saved matches")

  def test_quarter_scores_add_up_to_the_final_score(self):
    for path in MATCHES:
      with self.subTest(match=path.stem):
        m = load(path.stem)
        _, home, away = m.score_by_period(m.all_quarters())
        self.assertEqual([home[-1], away[-1]], m.score)
        self.assertEqual(m.events[-1].score, m.score)

  def test_box_scores_match_the_score(self):
    for path in MATCHES:
      with self.subTest(match=path.stem):
        m = load(path.stem)
        self.assertIs(m.check_boxscore(m.all_quarters()), True)


class GamebookTests(unittest.TestCase):
  def setUp(self):
    if not GAMEBOOKS:
      self.skipTest("no saved gamebooks in gamebooks/txt/")
    self.tmp = tempfile.TemporaryDirectory()
    self.addCleanup(self.tmp.cleanup)
    self.out = Path(self.tmp.name)
    patcher = mock.patch.object(paths, "GAMEBOOKS_TXT", self.out)
    patcher.start()
    self.addCleanup(patcher.stop)

  def test_final_score_matches_gamebook(self):
    for path in GAMEBOOKS:
      match_id = path.name.split("_")[0]
      with self.subTest(match=match_id):
        self.assertEqual(load(match_id).score, gamebook_final_score(path.read_text()))

  def test_regenerated_gamebook_is_identical(self):
    for path in GAMEBOOKS:
      match_id = path.name.split("_")[0]
      with self.subTest(match=match_id):
        m = load(match_id)
        GameReport(m).make_txt(m.all_quarters())
        self.assertEqual((self.out / path.name).read_text(), path.read_text())


if __name__ == "__main__":
  unittest.main()
