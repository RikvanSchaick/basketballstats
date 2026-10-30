# Step 0 — Baseline _(done 2026-10-30)_

## Goal

A fully green test suite before the restructure, so `tests/test_replay.py` can catch
any output change in the steps that follow.

## What was done

- Backup outside the repo: `~/basketballstats-backup-20261030/`, containing
  `gamebooks/txt`, `gamebooks/pdf` and `data/` as they were before regenerating.
- After the `f1` fix in `points_off_turnovers` (commit `8747be0`), regenerated:
  - `gamebooks/txt/260926M1_gamebook.txt` and `gamebooks/pdf/260926M1_gamebook.pdf`;
  - `data/*_dump.csv`, and for the first time `data/*.json`, which used to be written
    to `~/Downloads`.
- Differences from the backup: only "TO PTS" (points off turnovers).
  - 7619: away 17 → 18, home 10 → 11
  - 11179: away 11 → 12
  - 260926M1: home 24 → 25

  The player and play-by-play CSVs are unchanged.

## Result

`pytest`: 135 passed, 0 failed.

## Restore (only if needed)

```sh
cp -Rp ~/basketballstats-backup-20261030/gamebooks/txt ~/basketballstats-backup-20261030/gamebooks/pdf gamebooks/
cp -Rp ~/basketballstats-backup-20261030/data/. data/
```
