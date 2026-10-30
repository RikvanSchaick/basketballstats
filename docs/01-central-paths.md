# Step 1 — Central paths

> **Recommended model:** Claude Opus 5.5. Replacing the paths is simple, but the
> tests that fork a pseudo-terminal child and patch paths there are easy to get subtly
> wrong; a mistake would make them read the real `history.txt`.
>
> **Commits:** the agent does not commit. You review and commit (see docs/README.md).

## Goal

Every file and folder the app reads or writes is defined once, in `code/paths.py`, as
an absolute path based on the repo root. The app then works from any directory. Paths
still point to the **current** locations; they only move in step 4.

## Current hard-coded paths (relative to the working directory)

| File                   | Path(s)                                                                                                                                                                  |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `code/main.py`         | `HISTORY = "matches/history.txt"`, `os.listdir("matches")`, `f"matches/{id}.txt"` (select, save)                                                                         |
| `code/data_export.py`  | `os.listdir("matches")`, `"matches/" + filename`, `data/match_data_dump.csv` (read + write), `data/player_data_dump.csv`, `data/playbyplay_data_dump.csv`, `data/*.json` |
| `code/stats.py`        | the three `data/*_dump.csv` files                                                                                                                                        |
| `code/stats_export.py` | `f"data/{name}.pdf"`                                                                                                                                                     |
| `code/gamereport.py`   | `gamebooks/txt/{id}_gamebook.txt`, `gamebooks/pdf/{id}_gamebook.pdf`                                                                                                     |
| `code/scoreboard.py`   | `f"video/{name}.mov"`                                                                                                                                                    |
| `code/gameclock.py`    | default `base_dir` = folder of `quicktime_timestamp/tracker.py` (leave this one until step 5)                                                                            |

Find any others with: `grep -nE '"(matches|data|gamebooks|video)/' code/*.py`

## Tasks

1. Create `code/paths.py`:

   ```python
   from pathlib import Path

   ROOT = Path(__file__).resolve().parent.parent
   MATCHES = ROOT / "matches"
   HISTORY = MATCHES / "history.txt"
   GAMEBOOKS_TXT = ROOT / "gamebooks" / "txt"
   GAMEBOOKS_PDF = ROOT / "gamebooks" / "pdf"
   EXPORTS = ROOT / "data"
   VIDEO = ROOT / "video"
   ```

   Add small helpers only where a pattern repeats, e.g. `match_file(match_id)`.

2. Replace every path in the table with these constants.
   **Always access them as `paths.X` when the code runs** (`import paths`, then
   `paths.HISTORY`), never `from paths import HISTORY`. The tests replace these
   attributes, which only works for lookups made at call time.
3. Tests that relied on `os.chdir` into a temp folder now have to patch paths instead:
   - `tests/test_event_input.py`: in both forked children, set `paths.HISTORY` to the
     temp `history.txt`. Otherwise the test reads the real `matches/history.txt`.
   - `tests/test_replay.py` (`GamebookTests`): patch `paths.GAMEBOOKS_TXT` to the temp
     folder instead of `os.chdir`.
   - Search for other uses: `grep -n "chdir" tests/*.py`.
4. `code/code.md` and the per-folder `.md` files say to start the app "from the right
   working directory". Leave them; the docs are rewritten in step 7.

## Out of scope

Moving folders (step 4) and the clock `base_dir` (step 5).

## Done when

- The checks in docs/README.md pass.
- `cd /tmp && <repo>/.venv/bin/python <repo>/code/main.py --no-video-clock` → `select`
  works from outside the repo.
- `grep -nE '"(matches|data|gamebooks|video)/' code/*.py` finds nothing outside
  `paths.py`.
