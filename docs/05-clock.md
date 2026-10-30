# Step 5 — QuickTime tracker inside `app/clock/`

> **Recommended model:** Claude Opus 5.5. Replacing the `importlib` loading changes
> module identity, so tests that patch `tracker.*` have to patch the same module object
> that `gameclock` uses.
>
> **Commits:** the agent does not commit. You review and commit (see docs/README.md).

## Goal

`app/clock/gameclock.py` now loads `quicktime_timestamp/tracker.py` with
`importlib.util.spec_from_file_location` from a hard-coded path. Afterwards:

| Now                                             | After                                                   |
| ----------------------------------------------- | ------------------------------------------------------- |
| `quicktime_timestamp/tracker.py`                | `app/clock/tracker.py`                                  |
| `quicktime_timestamp/main.py` (standalone tool) | `app/clock/__main__.py` → `python -m app.clock`         |
| `quicktime_timestamp/README.md`                 | `docs/quicktime.md` (content only; rewritten in step 7) |

The `quicktime_timestamp/` folder disappears.

## Tasks

1. `git mv quicktime_timestamp/tracker.py app/clock/tracker.py`
   and `git mv quicktime_timestamp/main.py app/clock/__main__.py`
   and `git mv quicktime_timestamp/README.md docs/quicktime.md`.
2. `gameclock.py`:
   - Remove the `importlib` block (`_TRACKER_PATH`, `spec_from_file_location`, the
     `qt_tracker` registration in `sys.modules`).
   - Replace it with `from app.clock import tracker`, keeping the existing names
     (`discover_csv = tracker.discover_csv` etc.).
   - Remove `_TRACKER_PATH` from the default `base_dir`; that's `paths.CLOCK_LOGS` since step 4.
3. `app/clock/__main__.py`:
   - `from tracker import …` becomes `from app.clock.tracker import …`.
   - Point the default CSV folder to `paths.CLOCK_LOGS`.
   - `tracker.py` and `__main__.py` used to need only the standard library; keep it
     that way. Don't import `app.cli` or `prompt_toolkit`.
4. Error messages and `ClockLogError`: the class name stays. Exceptions show
   `app.clock.tracker.ClockLogError` instead of `qt_tracker.ClockLogError`. Check that
   no test compares that text.
5. Tests: `tests/test_gameclock.py` imports `tracker` through `gameclock`; switch to
   `from app.clock import tracker` where needed. Also check that patches of `tracker.*`
   affect the same module object that `gameclock` uses.
6. `docs/quicktime.md`: only fix the commands (`python -m app.clock`, CSV location
   `data/clock_logs/`); rewriting the content comes in step 7.

## Out of scope

Changing how the tracker or clock works.

## Done when

- The checks in docs/README.md pass.
- `grep -rn "spec_from_file_location\|quicktime_timestamp\|qt_tracker" app tests` finds nothing.
- Manual check with a video open in QuickTime Player:
  - `python -m app.clock --csv data/clock_logs/<id>.csv` shows the line with the
    timestamp and game clock;
  - in the app, `edit1` with the clock follows the video as before.
