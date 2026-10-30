# Step 6 — Small cleanups

> **Recommended model:** a faster, cheaper model from the Copilot model picker is
> enough. The tasks are small and mechanical, and the checks catch mistakes. Use
> Claude Opus 5.5 if the `history.txt` part causes trouble.
>
> **Commits:** the agent does not commit. `git rm --cached` is allowed (it only
> stages). You review and commit (see docs/README.md).

## Goal

Three loose ends that are left after the restructure.

## Tasks

1. **Merge `players` into `team`.** `app/model/players.py` (about 20 lines) is only
   used by `team.py`.
   - Move the `Players` class into `app/model/team.py`.
   - Remove `players.py` with `git rm`.
   - Update imports: `grep -rn "players import" app tests`.
2. **`scoreboard.py` → `tools/scoreboard.py`.** It's experimental (OpenCV, unfinished)
   and isn't used by the app.
   - `git mv code/scoreboard.py tools/scoreboard.py`.
   - Its video path comes from `paths.VIDEO`. `tools/` isn't a package, so at the top
     add `sys.path.insert(0, str(Path(__file__).resolve().parents[1]))` with a one-line
     comment. Alternatively keep `video/` as a relative path; it's a test script.
   - In `requirements.txt`, change the comment above `opencv-python` to `tools/scoreboard.py`.
   - Make sure ruff covers `tools/` (it does by default).
3. **Stop tracking `history.txt`.** It's the app's working file and changes every session.
   - `git rm --cached data/matches/history.txt`.
   - In `.gitignore`, remove `!/data/matches/history.txt`.
   - In `app/history.py` (or wherever `read_history` lives): if the file is missing, the
     app must work as before. `create` writes it with `write_history`. `select` creates
     it with `shutil.copyfile`, which creates the file already. Check where the app
     _reads_ it without a `create`/`select` first (for example `edit` straight from the
     menu isn't possible without a match). Add a test that `select` works when
     `history.txt` doesn't exist.
4. **Empty `code/`.** Only `code.md` is left. Move it with
   `git mv code/code.md docs/code.md`; step 7 folds it into the README. Then delete `code/`.

## Done when

- The checks in docs/README.md pass.
- The `code/` folder is gone.
- After `git rm --cached`, `git status` shows `history.txt` as deleted from git and the
  file still exists locally.
