# Step 2 — `code/` becomes the `app` package

> **Recommended model:** Claude Opus 5.5. Many files and imports change at once, and
> the tests patch module attributes (`print`, `sys`, `PromptSession`), whose targets
> have to be exactly right.
>
> **Commits:** the agent does not commit. You review and commit (see docs/README.md).

## Goal

Replace the flat `code/` folder with an importable package, `app/`, grouped by concern.
The program starts with `python -m app`. Only files move and imports change; the code
stays the same. `main.py` moves as a whole to `app/cli.py` and is split in step 3.

## File mapping (use `git mv`)

| From `code/`                                                                                                  | To                                                                                      |
| ------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `main.py`                                                                                                     | `app/cli.py`                                                                            |
| `paths.py`                                                                                                    | `app/paths.py` (fix `ROOT`: now `parent.parent` of `app/paths.py`, still the repo root) |
| `event.py`, `match.py`, `team.py`, `players.py`, `gamelog.py`, `boxscore.py`, `terminology.py`, `formulas.py` | `app/model/`                                                                            |
| `gameclock.py`                                                                                                | `app/clock/gameclock.py` (tracker follows in step 5)                                    |
| `gamereport.py`                                                                                               | `app/reports/gamebook.py`                                                               |
| `data_export.py`                                                                                              | `app/stats/export.py`                                                                   |
| `stats.py`                                                                                                    | `app/stats/stats.py`                                                                    |
| `stats_export.py`                                                                                             | `app/stats/report.py`                                                                   |
| `scoreboard.py`                                                                                               | stays in `code/` for now (moves in step 6)                                              |
| `code.md`                                                                                                     | stays for now (step 7)                                                                  |

New files: `app/__init__.py`, `app/model/__init__.py`, `app/clock/__init__.py`,
`app/reports/__init__.py`, `app/stats/__init__.py` (all empty), plus `app/__main__.py`:

```python
from app.cli import main

main()
```

Remove the `if __name__ == "__main__": main()` block from `cli.py`.

## Tasks

1. Do the `git mv`s above.
2. Rewrite every internal import as an absolute package import, for example
   `from match import Match` → `from app.model.match import Match`, and
   `import paths` → `from app import paths`. Class names don't change.
3. `gameclock.py` finds `tracker.py` through `Path(__file__).resolve().parent.parent`.
   After the move that must become `parents[2] / "quicktime_timestamp" / "tracker.py"`.
   Check it, because step 5 replaces this.
4. `pyproject.toml`:
   - `[tool.pytest.ini_options] pythonpath = ["."]`
   - `[tool.ruff] src = ["."]`
5. Tests:
   - Replace `import main as app` with `from app import cli`, and rename every `app.`
     inside the tests to `cli.` (the variable `app` would hide the package):
     `tests/test_quarter_sync.py`, and both places in `tests/test_event_input.py`.
   - Patch targets become `cli.print`, `cli.sys`, `cli.PromptSession`.
   - Other imports: `from app.model.event import Event`, `from app.model.match import
Match`, `from app.reports.gamebook import GameReport`, `from app.clock.gameclock
import …`, `from app import paths`.
6. Text that tells people to run `python code/main.py` (the argparse help in `cli.py`,
   docstrings) → `python -m app`. Leave `code/code.md` for step 7.
7. Delete `code/__pycache__`. `code/` should then only hold `scoreboard.py` and `code.md`.

## Out of scope

Splitting `cli.py` (step 3), moving data (step 4), the tracker (step 5).

## Done when

- The checks in docs/README.md pass.
- The smoke test passes with `python -m app --no-video-clock`, run from the repo root.
- `grep -rnE "^from (event|match|team|players|gamelog|boxscore|terminology|formulas|gameclock|gamereport|data_export|stats|stats_export|paths) import" app tests` finds nothing.
