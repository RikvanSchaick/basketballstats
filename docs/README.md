# Migration: restructure `code/` into a package, then write the README

This folder splits the restructure into small steps. Do them **one at a time, in
order**. After each step you review the changes and commit them yourself before
starting the next.

| Step | File                                       | Result                                                                        | Recommended model |
| ---- | ------------------------------------------ | ----------------------------------------------------------------------------- | ----------------- |
| 0    | [00-baseline.md](00-baseline.md)           | Green test suite as the starting point _(done)_                               | —                 |
| 1    | [01-central-paths.md](01-central-paths.md) | All file paths in one module; the app works from any directory                | Claude Opus 5.5   |
| 2    | [02-package.md](02-package.md)             | `code/` becomes the `app/` package, started with `python -m app`              | Claude Opus 5.5   |
| 3    | [03-split-cli.md](03-split-cli.md)         | Menus (`cli.py`) separated from event input with the live clock (`prompt.py`) | Claude Opus 5.5   |
| 4    | [04-data-layout.md](04-data-layout.md)     | `matches/`, `gamebooks/`, exports and clock logs under `data/`                | Claude Opus 5.5   |
| 5    | [05-clock.md](05-clock.md)                 | QuickTime tracker inside `app/clock/`, no more loading by file path           | Claude Opus 5.5   |
| 6    | [06-cleanups.md](06-cleanups.md)           | `players` merged into `team`, `scoreboard` moved to `tools/`                  | Faster model      |
| 7    | [07-readme.md](07-readme.md)               | Dutch `README.md`; `code/code.md` and the QuickTime README folded in          | Claude Opus 5.5   |

Each step says why it needs that model. "Faster model" means any quicker, cheaper
model from the Copilot model picker; that step is small and mechanical.

## Target layout (after step 7)

```
app/
  __init__.py
  __main__.py          python -m app
  paths.py             every file and folder the app reads or writes
  cli.py               menus and commands
  prompt.py            event_input() with the live game clock
  model/               event, match, team (+ players), gamelog, boxscore, terminology, formulas
  clock/               gameclock, tracker, __main__ (standalone QuickTime tool: python -m app.clock)
  reports/gamebook.py  GameReport (txt + pdf gamebooks)
  stats/               export.py (Data), stats.py (Stats), report.py (StatsReport)
tools/scoreboard.py    experimental, not part of the app
data/
  matches/             <gameId>.txt + history.txt (working file, untracked)
  gamebooks/txt/  gamebooks/pdf/
  exports/             CSV/JSON dumps and stats PDFs
  clock_logs/          game-clock CSVs per match
video/
docs/
tests/
```

The package is called `app` so the name stays generic. To use another name (for
example `src`), replace `app` throughout these files before step 2.

## Rules for every step

- **The agent never commits.** It must not run `git commit`, `git push`, `git reset`,
  `git stash`, `git rebase`, `git checkout`/`git restore` on files, or anything else
  that creates or rewrites history or throws away changes. `git mv` and
  `git rm --cached` are allowed, because a step needs them; they only stage changes.
  The agent ends with a report and `git status`, and you commit.
- Only do what the step describes. Don't change behaviour, stats logic or output.
  Note anything suspicious in the step report instead of fixing it.
- Use `git mv` for tracked files so history is kept. Use a plain `mv` for git-ignored
  data, and check it with `git status` / `git check-ignore -v`.
- Keep the code style: 2-space indentation, `ruff format`.

## Checks after every step

Run from the repo root:

```sh
.venv/bin/ruff check
.venv/bin/ruff format --check
.venv/bin/python -m pytest          # about 80 s; must be fully green
```

- `tests/test_replay.py` regenerates every saved gamebook and compares it byte for
  byte. That's the main guard that output hasn't changed.
- From step 2 on, also do a manual smoke test with `python -m app --no-video-clock`
  (before step 2: `python code/main.py --no-video-clock`):
  `select` → a match ID → `summary` (`1,2,3,4`) → `box` (`1,2,3,4`) → `exit`.
- After a step that touches the clock (3 and 5), also check by hand with a video
  open in QuickTime Player. The tests mock AppleScript.

After review, commit each step yourself, for example
`git commit -m "Migration step 1: central paths"`.

To throw away an uncommitted step: `git restore --staged . && git restore .`, and
delete any new files (`git status` lists them). For an already committed step, use
`git reset --hard HEAD~1` before pushing. Data moves in step 4 also need the `mv`
commands reversed for git-ignored files.

## Running a step with an agent

Pick the model from the table above and give it: _"Execute docs/0N-….md. Follow
docs/README.md. Do not commit. Stop when the checks pass and report what changed,
ending with `git status`."_
