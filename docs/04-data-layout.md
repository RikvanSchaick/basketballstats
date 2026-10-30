# Step 4 — Data under `data/`

> **Recommended model:** Claude Opus 5.5. Git-ignored data can't be restored from
> git, and the `.gitignore` re-include rules are tricky. This step needs the most care.
>
> **Commits:** the agent does not commit. You review and commit (see docs/README.md).

## Goal

All user data lives under `data/`, and code and data are no longer mixed at the repo root:

| Now                                                         | After                                        |
| ----------------------------------------------------------- | -------------------------------------------- |
| `matches/`                                                  | `data/matches/`                              |
| `gamebooks/txt/`, `gamebooks/pdf/`                          | `data/gamebooks/txt/`, `data/gamebooks/pdf/` |
| `data/*.csv`, `data/*.json`, stats PDFs (`data/{name}.pdf`) | `data/exports/`                              |
| `quicktime_timestamp/gameclock_logs/`                       | `data/clock_logs/`                           |
| `video/`                                                    | stays put                                    |

Thanks to step 1, the code only changes in `app/paths.py`, plus the clock lookup below.

## Watch out: most data is git-ignored

Only `matches/history.txt`, `matches/{5617,6552,7619,11179}.txt` and the `*.md`
placeholders are tracked. The rest exists only on this machine.

- Move tracked files with `git mv`, everything else with `mv`.
- Before you start, make sure the backup from step 0 is still there, or make a new one.

## Tasks

1. Create the folders and move:
   ```sh
   mkdir -p data/matches data/gamebooks data/exports data/clock_logs
   git mv matches/history.txt matches/5617.txt matches/6552.txt matches/7619.txt matches/11179.txt matches/matches.md data/matches/
   mv matches/*.txt data/matches/                      # the rest (ignored)
   git mv gamebooks/gamebooks.md data/gamebooks/
   git mv gamebooks/txt/txt.md gamebooks/pdf/pdf.md …  # into data/gamebooks/{txt,pdf}/
   mv gamebooks/txt/*.txt data/gamebooks/txt/ && mv gamebooks/pdf/*.pdf data/gamebooks/pdf/
   mv data/*.csv data/*.json data/exports/             # plus any stats PDFs in data/
   mv quicktime_timestamp/gameclock_logs/*.csv data/clock_logs/
   ```
   Then remove the empty old folders.
2. `app/paths.py`: `MATCHES = ROOT/"data"/"matches"`,
   `GAMEBOOKS_TXT/PDF = ROOT/"data"/"gamebooks"/…`, `EXPORTS = ROOT/"data"/"exports"`,
   and a new `CLOCK_LOGS = ROOT/"data"/"clock_logs"`.
3. Clock logs. `tracker.discover_csv(explicit, directory, match_id)` looks in
   `directory/"gameclock_logs"/{match_id}.csv` and `directory.glob("time_*.csv")`.
   - Change it to look in `directory/f"{match_id}.csv"` and `directory.glob("time_*.csv")`.
   - Make `GameClockTracker`'s default `base_dir` `paths.CLOCK_LOGS`.
   - `quicktime_timestamp/main.py` calls `discover_csv(args.csv, Path(__file__).parent)`.
     Point that to `<repo>/data/clock_logs` (relative to its own file; it doesn't import `app`).
   - Update the `--csv` help text in `cli.py` and `quicktime_timestamp/main.py`.
4. `.gitignore`: replace the `data/*`, `gamebooks/*`, `matches/*` and `gameclock_logs`
   rules. A file can only be re-included if its parent folder isn't excluded, so:
   ```gitignore
   /data/*
   !/data/data.md
   !/data/matches/
   /data/matches/*
   !/data/matches/matches.md
   !/data/matches/history.txt
   !/data/matches/5617.txt
   !/data/matches/6552.txt
   !/data/matches/7619.txt
   !/data/matches/11179.txt
   !/data/gamebooks/
   /data/gamebooks/*/*
   !/data/gamebooks/*/*.md
   ```
   `history.txt` stays tracked for now; step 6 changes that.
5. Tests: update `tests/test_gameclock.py` (`SAMPLE_CSV`, and the tests for
   `discover_csv` / `base_dir`), `tests/test_replay.py`, and `tests/test_event.py`
   (`ROOT / "matches"`). Use `paths.MATCHES` etc. instead of building paths again.
6. Update the paths mentioned in the per-folder `.md` files (no rewrite; that's step 7).

## Done when

- The checks in docs/README.md pass, with **no skipped tests** in `test_replay.py` and
  `test_gameclock.py`; skips would mean the data wasn't found.
- `git status` only shows renames (`R`) and the new `.gitignore`. No previously ignored
  files are suddenly untracked or new.
- `git check-ignore -v data/matches/260919D1.txt data/gamebooks/txt/260919D1_gamebook.txt data/exports/match_data_dump.csv data/clock_logs/260926M1.csv`
  marks all four as ignored.
- Smoke test: `select` lists the same matches as before; `export` writes to `data/gamebooks/`.
