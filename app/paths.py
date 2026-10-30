"""Every file and folder the app reads or writes.

Use these as `paths.X` at call time (`from app import paths`), never
`from app.paths import X`: tests replace the attributes.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MATCHES = ROOT / "matches"
HISTORY = MATCHES / "history.txt"
GAMEBOOKS_TXT = ROOT / "gamebooks" / "txt"
GAMEBOOKS_PDF = ROOT / "gamebooks" / "pdf"
EXPORTS = ROOT / "data"
VIDEO = ROOT / "video"


def match_file(match_id: str) -> Path:
  return MATCHES / f"{match_id}.txt"
