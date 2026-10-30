# Step 3 — Split `cli.py` into menus and event input

> **Recommended model:** Claude Opus 5.5. The risks are circular imports between
> `cli` and `prompt`, and the slow pseudo-terminal tests that patch the moved functions.
>
> **Commits:** the agent does not commit. You review and commit (see docs/README.md).

## Goal

`app/cli.py` (formerly `main.py`, about 590 lines) currently mixes three things:

1. the menus and commands (`cmd_*`, `_run_app`, `main`, `parse_args`, `prints`);
2. the history helpers (`read_history`, `write_history`, `append_history`);
3. event input with the live game clock (`event_input`, `_clock_prefix`, `PREFIX_LEN`,
   `LIVE_CLOCK_INTERVAL`) and the clock setup (`setup_tracker`, `print_anchor`,
   `ask_sync`, `anchor_quarter`, `sync_quarter`).

After this step:

- `app/prompt.py`: `event_input` and its helpers/constants, plus the clock setup and
  synchronisation (everything that talks to the `GameClockTracker` or `prompt_toolkit`).
- `app/cli.py`: menus, commands, `parse_args`, `main`, and the history helpers.

Move the code unchanged.

## Tasks

1. Create `app/prompt.py` and move the functions listed above into it. Give it the
   imports it needs (`asyncio`, `sys`, `prompt_toolkit`, `from app.clock.gameclock
import …`, `from app import paths` if it reads the history).
   - `event_input` reads the history. Import `read_history` from `cli`, or move the
     three history helpers to `app/history.py` and import them from both modules,
     which avoids a circular import. **Prefer `app/history.py`.**
2. In `cli.py`, import what it uses from `app.prompt` (`event_input`, `setup_tracker`,
   `sync_quarter`).
3. Tests:
   - `tests/test_event_input.py`: `from app import prompt`, and call
     `prompt.event_input`. Patch `prompt.PromptSession` (`SpySession`).
   - `tests/test_quarter_sync.py`: `ask_sync`, `sync_quarter`, `setup_tracker` now live
     in `app.prompt`. Patch `prompt.print` and `prompt.sys`.
   - Tests that drive the whole menu through `cli` must replace `cli.event_input`,
     because `cli` imports the name.
4. `ruff check` must not report unused imports in `cli.py` after the move.

## Out of scope

Changing any behaviour of the prompt or the clock.

## Done when

- The checks in docs/README.md pass, including the about-80-s pseudo-terminal tests in
  `tests/test_event_input.py`.
- Manual check with QuickTime: `edit1` shows the live clock prefix and still follows the video.
