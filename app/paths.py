"""Every file and folder the app reads or writes.

Use these as `paths.X` at call time (`from app import paths`), never
`from app.paths import X`: tests replace the attributes.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MATCHES = DATA / "matches"
HISTORY = MATCHES / "history.txt"
GAMEBOOKS_TXT = DATA / "gamebooks" / "txt"
GAMEBOOKS_PDF = DATA / "gamebooks" / "pdf"
EXPORTS = DATA / "exports"
CLOCK_LOGS = DATA / "clock_logs"
VIDEO = ROOT / "video"


def match_file(match_id: str) -> Path:
  return MATCHES / f"{match_id}.txt"
