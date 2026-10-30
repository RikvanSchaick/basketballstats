# Step 7 — README (in English)

> **Recommended model:** Claude Opus 5.5. It needs to translate the Dutch sources
> into clear English, and every event-grammar example has to be checked against the parser.
>
> **Commits:** the agent does not commit. You review and commit (see docs/README.md).

## Goal

One complete `README.md` in English. **Every README and `.md` file in the repo is in
English**, including the per-folder placeholders. The scattered docs get folded into it:

- `docs/code.md` (formerly `code/code.md`, Dutch, per-file description and gameclock
  workflow): translate and fold in, then delete.
- `docs/quicktime.md` (formerly the QuickTime README, already English): keep it in
  English as a technical appendix and link to it from the README. Fix stale references
  (`code/code.md`) and duplicated sections.
- Per-folder `.md` files (`data/data.md`, `data/matches/matches.md`,
  `data/gamebooks/**.md`, `video/video.md`): keep as short placeholders (git needs a
  file to keep a folder). Rewrite them in English, cut them to 1–3 lines and link to
  the README.
- Leave the `docs/0N-*.md` migration files; whether to delete them is up to you afterwards.

## README contents

1. **What it is**: entering basketball events per game, boxscores and
   gamebooks (txt/pdf), season stats, optional game clock from QuickTime.
2. **Installation**: Python ≥ 3.10, `python3 -m venv .venv`,
   `.venv/bin/pip install -r requirements.txt`; for development
   `requirements-dev.txt`. macOS is only needed for the QuickTime clock.
3. **Running it**: `python -m app` from the repo root. Flags (from `parse_args` in
   `app/cli.py`): `--csv`, `--anchor-clock`, `--anchor`, `--no-video-clock`, plus
   `python -m app.clock` for the standalone tracker.
4. **Menus**: take them from `prints()` in `app/cli.py`:
   - start menu: `create`, `select`, `stats`, `exit`;
   - match menu: `edit<N>`, `summary`, `log`, `box`, `save`, `export`, `exit`;
   - stats menu: `team`, `player`, `exit`.

   Explain the rosters at `create` (`number,name;number,name;…`, at least 6 per team)
   and the starters (`4,5,6,7,9`, exactly 5).

5. **Entering events**: in `edit<N>`, close with `<N>end`; `<N>oncourt` shows who is
   on the court. Keys: ↑/↓ browse previous lines, Tab cycles the time prefix / last line.
6. **Event grammar**: the most important section. Take it from `_GRAMMAR` in
   `app/model/event.py` and check every example with `Event.parse`:
   - Structure `Q MMSS action team player`: quarter 1–8 (5–8 = extra time),
     clock `MMSS` from `1000` down to `0000`, team `H`/`A`, player number 1–2 digits.
   - Table with code, meaning, form, example, for: `2m 3m 1m` (+ `a` assist from a
     teammate), `2 3` (+ `b` block by an opponent), `1`, `t` (team or player, + `s`/`b`
     by an opponent), `r` / `ft` (team or player), `j` / `to` (team only),
     `f0`–`f3` (foul + number of free throws), `fu`, `fd`, `a`/`s`/`b` standalone,
     `out…in…` (substitution within the same team), `edit<N>` / `<N>end`.
   - Note that lines with extra characters or an opponent as assister are rejected.
7. **Game clock from QuickTime**: translate the "Werking en instellingen" part from
   `docs/code.md` (sync per quarter, `09:59` anchor, CSV per match in
   `data/clock_logs/<gameId>.csv`, fallback to typing it yourself).
8. **Folders**: short tree of `app/`, `data/` (matches, gamebooks, exports, clock_logs),
   `video/`, `tools/`, `tests/`, `docs/`, with one line per subpackage. Take the
   per-file descriptions from `docs/code.md`, updated to the new names.
9. **Development**: `pytest`, `ruff check`, `ruff format` (2 spaces), and that
   `tests/test_replay.py` compares gamebooks against `data/gamebooks/txt/`. Tests are
   skipped when the git-ignored data is missing.

## Rules

- Every command in the README must actually work: run it, or for the QuickTime parts,
  check the code.
- Every event example must be accepted by `Event.parse` (or deliberately rejected, if
  that's what the example shows). Check it with a small one-off script, not a new test.

## Done when

- The checks in docs/README.md pass. The docs don't touch any code, so this is a sanity check.
- No Dutch prose is left in any `.md` outside the migration files `docs/0N-*.md`.
- `docs/code.md` is gone, and nothing outside the migration files refers to `code/` or
  `quicktime_timestamp/` any more:
  `grep -rn "code/\|quicktime_timestamp" --include=*.md . | grep -v "docs/0[0-7]-"`.
