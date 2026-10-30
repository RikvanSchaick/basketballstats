# basketballstats

A terminal program for recording basketball games event by event. From those events it
builds:

- **boxscores, game logs and summaries** per quarter, right in the terminal;
- **gamebooks** per game, as `txt` and `pdf`;
- **season stats** per team and per player, exported to CSV/JSON and PDF;
- optionally, **event times read from the game clock** of a video open in QuickTime
  Player, so you only have to type the action.

## Installation

Requires Python 3.10 or newer. From the repo root:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt       # running the app
.venv/bin/pip install -r requirements-dev.txt   # development: adds pytest and ruff
```

macOS is only needed for the QuickTime game clock. Everything else runs anywhere.

## Running it

From the repo root:

```sh
.venv/bin/python -m app                       # start the program
.venv/bin/python -m app --no-video-clock      # type every event time yourself
```

| Flag                   | Meaning                                                                                                                           |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `--csv PATH`           | Game-clock CSV. Defaults to `data/clock_logs/<gameId>.csv`, else the single `time_*.csv` there; you pick one if there are several. |
| `--anchor-clock MM:SS` | Game-clock value used to line the video up with the CSV (default `09:59`).                                                        |
| `--anchor TIME`        | Video timestamp that shows `--anchor-clock`, as seconds, `MM:SS.mmm` or `HH:MM:SS.mmm`. Skips the anchor prompt.                  |
| `--no-video-clock`     | No QuickTime autofill.                                                                                                            |

The QuickTime tracker also runs on its own, without the rest of the app:
`python -m app.clock` (see [docs/quicktime.md](docs/quicktime.md)).

## Menus

**Start menu**

| Command  | What it does                                                                         |
| -------- | ------------------------------------------------------------------------------------ |
| `create` | Create a new game: game ID, home team, away team, date, time, location and rosters.  |
| `select` | Load a saved game from `data/matches/<gameId>.txt`.                                  |
| `stats`  | Season stats (see the stats menu). Leaving that menu ends the program.               |
| `exit`   | Quit.                                                                                |

With `create` you enter the rosters per team as `number,name;number,name;…`, with **at
least 6 players** per team, for example `4,Jan;5,Piet;6,Kees;7,Joost;9,Bas;12,Tim`. The
name may be empty (`4,;5,;…`).

**Game menu** (after `create` or `select`)

| Command   | What it does                                                                          |
| --------- | ------------------------------------------------------------------------------------- |
| `edit<N>` | Enter events for quarter `N` (`1`–`4`, `5`–`8` for overtime). See below.              |
| `summary` | Summary of the chosen quarters (`1,2,3,4`).                                           |
| `log`     | Game log (all events) of the chosen quarters.                                         |
| `box`     | Boxscore of the chosen quarters.                                                      |
| `save`    | Save the game as `data/matches/<gameId>.txt` (asks before overwriting).               |
| `export`  | Make a gamebook in `data/gamebooks/txt/` and `data/gamebooks/pdf/`.                   |
| `exit`    | Quit.                                                                                 |

**Stats menu**

| Command  | What it does                                           |
| -------- | ------------------------------------------------------ |
| `team`   | Stats of a chosen team, as a PDF in `data/exports/`.   |
| `player` | Stats of a chosen player, as a PDF in `data/exports/`. |
| `exit`   | Quit.                                                  |

When the number of saved games in `data/matches/` doesn't match the export, `stats`
first re-exports all games to `data/exports/` (`*_data_dump.csv` and `*_data.json`).

## Entering events

1. Type `edit<N>`, for example `edit1`.
2. If the quarter has no starters yet, you are asked for them per team: exactly
   **5 numbers**, comma-separated, for example `4,5,6,7,9`.
3. Type events one per line (see the grammar below). Invalid lines get
   `invalid event`; events that don't fit the game (for example a player who isn't on
   the court) get a message and are not saved.
4. `<N>oncourt` (for example `1oncourt`) shows who is on the court.
5. Close the quarter with `<N>end` (for example `1end`). Typing `edit<N>` again
   reopens a closed quarter.

Each entered line is added straight away to the working file
`data/matches/history.txt`. Use `save` to store it under the game ID.

Keys on the input line:

- **↑ / ↓**: browse earlier lines of the game.
- **Tab**: cycles through *time of the last line* (quarter + MMSS) → *the whole last
  line* → back to the empty start.

## Event grammar

Every event is a single line with no spaces:

```
Q MMSS action team player [action2 team2 player2]
```

| Part      | Values                                                                        |
| --------- | ----------------------------------------------------------------------------- |
| `Q`       | Quarter `1`–`8`; `5`–`8` are overtimes.                                       |
| `MMSS`    | Game clock without a colon, from `1000` (10:00) down to `0000`. Overtime starts at `0500`. |
| `team`    | `H` (home) or `A` (away).                                                     |
| `player`  | Shirt number, 1 or 2 digits.                                                  |

So `108392mA12aA4` reads as: quarter `1`, clock `08:39`, `2m` (made 2), team `A`,
player `12`, assist (`a`) by `A4`.

| Code             | Meaning                                    | Form                                     | Example           |
| ---------------- | ------------------------------------------ | ---------------------------------------- | ----------------- |
| `2m` `3m` `1m`   | Made 2-pointer / 3-pointer / free throw    | player, optional `a` + teammate          | `108392mA12aA4`, `109153mH7`, `107451mH5` |
| `2` `3`          | Missed 2-pointer / 3-pointer               | player, optional `b` + opponent (block)  | `104412H8bA17`, `103303A9` |
| `1`              | Missed free throw                          | player                                   | `102101H5`        |
| `t`              | Turnover                                   | team, or player with optional `s`/`b` + opponent | `10425tH`, `10827tH13sA11` |
| `r`              | Rebound                                    | team or player                           | `10624rA`, `10813rA12` |
| `ft`             | Technical foul                             | team or player                           | `10700ftH`, `10700ftH4` |
| `j`              | Possession after the jump ball             | team only                                | `11000jA`         |
| `to`             | Timeout                                    | team only                                | `10500toH`        |
| `f0`–`f3`        | Personal foul + number of free throws (0–3) | player                                  | `10650f2H4`       |
| `fu`             | Unsportsmanlike foul                       | player                                   | `10600fuA8`       |
| `fd`             | Disqualifying foul                         | player                                   | `10600fdA8`       |
| `a` `s` `b`      | Assist / steal / block on its own          | player                                   | `10550aH4`, `10550sA3`, `10550bH9` |
| `out…in…`        | Substitution within the same team          | player `out` + player `in`               | `10624outH7inH11` |
| `edit<N>` `<N>end` | Start / end of quarter `N`               | —                                        | `edit1`, `1end`   |

These lines are **rejected**:

- extra characters after the event: `11000jA5`, `108392mA12x`;
- an assist from the opponent: `108392mA12aH4`;
- a block or steal by a teammate: `104412H8bH17`, `10425tH13sH11`;
- a substitution between two teams: `10624outH7inA11`;
- a team code without a team: `10500to`;
- a quarter or time out of range: `91000jA`, `11060jA`, `11001jA`.

## Game clock from QuickTime (macOS)

When editing a quarter (`edit1` to `edit8`), the app can read the event time from the
video open in **QuickTime Player**, so you only type the action. Tracking and
anchoring live in `app/clock/`; details and macOS permissions are in
[docs/quicktime.md](docs/quicktime.md).

**What you need:** a game-clock CSV per game in `data/clock_logs/<gameId>.csv`
(`real_time,game_clock,period`) and the game video open in QuickTime Player. Without
QuickTime, without a usable CSV or with `--no-video-clock`, everything stays manual;
the arrow keys and Tab work the same.

How it works and what you can set:

- The clock is set up when you open the first quarter with `edit<N>`, so you can
  create or select a game first.
- On **every** `edit<N>` the app asks: `Sync video for quarter N? (y/n):`. Only a typed
  `y` starts syncing; `n`, an empty line or anything else keeps the current sync for
  that quarter.
- After `y`, scrub the video to the frame where the game clock of *that* quarter first
  shows `09:59` (`04:59` for a five-minute overtime), then press Enter. The right frame
  per quarter comes from the CSV's `period` column.
- With no sync yet, or with a different video open in QuickTime Player, the app syncs
  straight away without asking: without an offset there is nothing to keep.
- With `--anchor`, without a terminal, or with `--no-video-clock`, the question is
  skipped.
- The `period` column holds the quarter number per row (`1`, `2`, …) or the context
  (`Pregame`, `Timeout`, `Break`, `Half Time`). During a stoppage `game_clock` logs the
  stoppage's own countdown; the game clock is then the last value of the interrupted
  quarter, and that is what gets filled in.
- If the video is in a *different* quarter than the one you are entering, no time is
  filled in and only the quarter digit remains. That's the signal to sync again.
- The time updates live on the input line: the first five characters (quarter + MMSS)
  follow the video as long as the prompt is open, so the saved time is the game clock
  at the moment you press Enter. Pause the video on the action to record an exact time.
- Only those five characters change; the action you type and the cursor position stay.
- If you change the time yourself, the automatic updates stop for that line. Changes to
  the action don't stop them.
- A CSV without a `period` column still works, but without per-quarter anchoring.

## Folders

```
app/                    the program (python -m app)
  __main__.py           entry point
  cli.py                menus and commands (create, select, edit<N>, box, export, stats, …)
  prompt.py             event input line with the live game clock and per-quarter sync
  history.py            reading and writing the working file data/matches/history.txt
  paths.py              every file and folder the app reads or writes
  model/                a game and its parts
    match.py            Match: teams, starters, who is on court, events, checks
    event.py            Event: one event line; Event.parse() reads the grammar above
    team.py             Team and Players: roster, names and starters per quarter
    boxscore.py         BoxScore: boxscore per quarter, built on gamelog.py
    gamelog.py          GameLog: running tally of points, fouls, shots and other stats
    terminology.py      display text per action code (for example "AST" and "assist")
    formulas.py         formulas for advanced stats
  reports/gamebook.py   GameReport: gamebook of one game as txt and pdf
  stats/                season stats
    export.py           Data: exports all saved games to CSV/JSON in data/exports/
    stats.py            Stats: stats per team and player from those exports
    report.py           StatsReport: stats as a PDF
  clock/                game clock from QuickTime Player
    tracker.py          AppleScript queries, CSV loading, ClockMap, anchoring, background poller
    gameclock.py        GameClockTracker: game clock → event time for the app
    __main__.py         standalone tracker: python -m app.clock
data/                   mostly git-ignored
  matches/              <gameId>.txt per game + history.txt (working file)
  gamebooks/txt/        <gameId>_gamebook.txt
  gamebooks/pdf/        <gameId>_gamebook.pdf
  exports/              CSV/JSON dumps and stats PDFs
  clock_logs/           game-clock CSV per game: <gameId>.csv
video/                  game videos (git-ignored)
tools/scoreboard.py     experimental scoreboard automation; not part of the app (needs opencv-python)
tests/                  unittest/pytest tests
docs/                   quicktime.md (QuickTime tracker) and the migration steps 00–07
```

## Development

From the repo root:

```sh
.venv/bin/python -m pytest          # all tests
.venv/bin/ruff check                # lint
.venv/bin/ruff format               # format (2-space indentation)
```

- `tests/test_replay.py` replays every saved game and compares the generated gamebook
  byte for byte with the one in `data/gamebooks/txt/`. That's the main guard that
  output hasn't changed.
- The data in `data/` is mostly git-ignored. Tests that need it are skipped when it is
  missing.
- The QuickTime tests (`tests/test_gameclock.py`, `tests/test_quarter_sync.py`,
  `tests/test_event_input.py`) mock AppleScript. Check clock changes by hand as well,
  with a video open in QuickTime Player.
