# QuickTime Timestamp Tracker

Continuously prints the current playback position of the video you have open in the
native macOS **QuickTime Player**, alongside the **game clock** that was showing at
that moment, updating roughly 10 times per second on a single terminal line:

```
Anchored: video 10.000s = game clock 09:59 at 13:53:25.443 (offset +49995.443s)
Tracking: test1.mov (duration 115.357s) against time_B.O.B.VSE-1.csv
Current timestamp: 132.400s  |  Game clock: 09:41  [playing]
```

Python never opens or decodes the video. It only asks QuickTime Player what it is
currently showing, via AppleScript.

## Requirements

- macOS (verified on macOS 27.0, build 26A428)
- Python 3.8+ (the system `python3` is fine)
- No third-party packages — standard library only

## Running it

1. Open a `.MOV` file in QuickTime Player (Finder → double-click, or `open -a "QuickTime Player" yourfile.mov`).
2. From this directory, run:

```bash
python3 main.py
```

3. You will be asked to line the video up with the game clock:

```
Scrub the video to the frame where the game clock first shows 09:59,
pause there, then press Enter.
```

   Do exactly that, then press Enter. The current QuickTime position is read at that
   instant and used as the anchor.

4. Press `Ctrl+C` to stop.

To skip the prompt, pass the anchor directly. Seconds, `MM:SS.mmm` and
`HH:MM:SS.mmm` are all accepted:

```bash
python3 main.py --anchor 132.4
python3 main.py --anchor 02:12.400
```

Other options:

```bash
python3 main.py --csv time_B.O.B.VSE-1.csv   # pick the game-clock log explicitly
python3 main.py --anchor-clock 09:59         # which clock value to anchor on
python3 main.py --interval 0.05              # poll faster (default 0.1 = ~10 Hz)
```

## The game-clock CSV

A CSV sitting next to `main.py`, named `time_*.csv`:

```csv
real_time,game_clock
13:53:08.230,10:00
13:53:25.443,09:59
13:53:26.443,09:58
```

- `real_time` is wall clock as `HH:MM:SS.mmm`; `game_clock` is `MM:SS`.
- Each row is the instant the game clock **changed to** that value, so a row's clock
  is displayed until the next row's `real_time`. That is what makes stoppages work:
  in the sample file the clock sits at `09:41` from `13:53:43.410` all the way to
  `13:53:50.209`.
- If `--csv` is omitted and exactly one `time_*.csv` is present, it is used
  automatically. If there are several, you are asked to pick one.
- A row earlier than its predecessor is treated as a midnight rollover and 86400 s is
  added so the series stays monotonic. Empty, malformed or still-out-of-order files
  are rejected with a message naming the offending line.

### Anchoring

The CSV is wall-clock based, the video is not, so the two need lining up once. You
point at the frame where the game clock first reads `09:59` (configurable via
`--anchor-clock`), and the program computes `offset = csv_real_time - video_timestamp`.
Every later lookup is `bisect_right(times, video_time + offset) - 1`.

This assumes the video runs at real-time speed with no cuts, so one anchor is enough.

## macOS permissions

The first time you run this, macOS will show a prompt like:

> "Terminal" wants access to control "QuickTime Player".

Click **OK**. Without it, every poll fails and the program prints a message telling
you to grant access.

Permission is granted to the app that *launches* Python, not to Python itself — so
Terminal, iTerm and VS Code are each approved separately. To review or change it:

**System Settings → Privacy & Security → Automation →** expand your terminal app →
enable **QuickTime Player**.

If you previously denied the prompt, macOS will not ask again. Re-enable it in that
panel, or reset it with:

```bash
tccutil reset AppleEvents
```

Note that toggling Automation permission quits the affected app, so restart your
terminal afterwards. This project needs **Automation** access only — not
Accessibility, Screen Recording or Full Disk Access.

## Testing it

1. Open a `.MOV` file in QuickTime Player.
2. Run `python3 main.py` and complete the anchor prompt.
3. Press play in QuickTime — the timestamp climbs and the game clock counts down.
4. Press pause — both freeze and the line flips to `[paused]`.
5. Drag the QuickTime timeline somewhere else — both values jump within about a tenth
   of a second. Dragging **backwards** immediately shows the earlier clock value.
6. Confirm the game clock matches what is burned into the video.

Also worth trying, to see the error handling:

- Scrub before the first logged row → `Game clock: --:--`
- Scrub past the last logged row → `Game clock: 08:55 (end of log)`
- Close the video window → `No video is open in QuickTime Player`
- Quit QuickTime Player → `QuickTime Player is not running`
- Re-open a video → tracking resumes automatically, no restart needed

## How it works

```
QuickTime Player  <--Apple events-->  osascript helper  --stdout lines-->  main.py
                                                                              |
                                              time_*.csv --> ClockMap --------+
```

`main.py` spawns a single long-lived `osascript` process running an AppleScript
`repeat` loop. Each pass reads `current time`, `duration`, `playing` and `name` from
`document 1` of QuickTime Player, writes one tab-separated line, then delays. Python
reads those lines on a background thread, maps the timestamp through `ClockMap`, and
renders the result.

### Layout

| File | Contains |
| ---- | -------- |
| `tracker.py` | Everything reusable: AppleScript queries, `Status`, CSV loading, `ClockMap`, anchoring and the background `Poller`. |
| `main.py` | Only the terminal front end: `Printer`, the polling loop and the CLI. |

`code/gameclock.py` imports `tracker.py` to autofill event times in the basketball
app, so the AppleScript, CSV parsing, anchoring and mapping logic exist once. It
loads the module by file path rather than via `sys.path`, because this directory
also contains a `main.py` that would otherwise shadow the app's own module.

A few details that matter:

- **One helper process, not one per poll.** Launching `osascript` costs ~170 ms, which
  caps you at under 6 updates/second. Reusing one process drops the per-sample cost to
  the ~58 ms Apple event round trip.
- **Rate calibration.** That round trip adds to the scripted `delay`, so a naive
  `delay 0.1` yields only ~6.3 Hz. The program measures its own period over the first
  few samples and trims the delay once to land on the requested rate.
- **A separate one-shot query for anchoring.** The anchor is captured with its own
  single `osascript` run rather than by reading the streaming queue, which could hand
  back a sample from before you finished scrubbing.
- **Milliseconds on the wire.** AppleScript formats real numbers using the system
  locale, so on a Dutch (`nl_NL`) Mac `83.45` serialises as `83,45`, and small values
  become scientific notation like `1,0E-7`. Neither parses with `float()`. The helper
  therefore sends integer milliseconds, which are locale-independent, and Python
  converts back to seconds.
- **It never launches QuickTime.** The guard `if application "QuickTime Player" is
  running` checks state without starting the app, so running this program does not pop
  QuickTime open.
- **Recovery.** Errors are caught inside the AppleScript loop, so a missing document or
  a quit application does not kill the helper. If the helper itself dies or stops
  producing output for 3 seconds, Python restarts it.

### AppleScript properties used

These were read from the installed dictionary
(`sdef /System/Applications/QuickTime\ Player.app`) rather than assumed. On the
`document` class:

| Property       | Type    | Access | Meaning                          |
| -------------- | ------- | ------ | -------------------------------- |
| `current time` | real    | rw     | Playback position in seconds     |
| `duration`     | real    | r      | Movie length in seconds          |
| `playing`      | boolean | r      | Whether the movie is playing     |
| `name`         | text    | r      | Document name                    |

`current time` reports sub-millisecond precision while playing, freezes when paused,
and updates immediately when you scrub the timeline.


### AppleScript properties used

These were read from the installed dictionary
(`sdef /System/Applications/QuickTime\ Player.app`) rather than assumed. On the
`document` class:

| Property       | Type    | Access | Meaning                          |
| -------------- | ------- | ------ | -------------------------------- |
| `current time` | real    | rw     | Playback position in seconds     |
| `duration`     | real    | r      | Movie length in seconds          |
| `playing`      | boolean | r      | Whether the movie is playing     |
| `name`         | text    | r      | Document name                    |

`current time` reports sub-millisecond precision while playing, freezes when paused,
and updates immediately when you scrub the timeline.
