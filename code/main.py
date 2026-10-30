from event import Event
from match import Match
from stats_export import StatsReport
from gamereport import GameReport
# from rawstats import rawstats
from data_export import Data
from gameclock import ClockLogError, GameClockTracker, DEFAULT_ANCHOR_CLOCK, parse_anchor_value
import argparse
import asyncio
import os
import shutil
import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings

# Event strings start with the period digit plus MMSS.
PREFIX_LEN = 5
LIVE_CLOCK_INTERVAL = 0.2
HISTORY = "matches/history.txt"
VALID_QUARTERS = {"1","2","3","4","5","6","7","8"}


def read_history() -> list[str]:
    with open(HISTORY, "r") as f:
        return f.read().splitlines()


def write_history(lines: list[str]) -> None:
    with open(HISTORY, "w") as f:
        f.writelines(line + "\n" for line in lines)


def append_history(*lines: str) -> None:
    with open(HISTORY, "a") as f:
        f.writelines(line + "\n" for line in lines)


def prints(type:str):
    if type == "intro":
        print("\nOPTIONS")
        print("- create:\tcreate new match")
        print("- select:\tselect match")
        print("- stats:\tsee all stats of certain team")
        print("- exit:\t\texit program")
    
    if type == "match":
        print("\nOPTIONS")
        print("- edit:\t\tedit match")
        print("- summary:\tview summary of match")
        print("- log:\t\tview gamelog of match")
        print("- box:\t\tview boxscore of match")
        print("- save:\t\tsave match as txt")
        print("- export:\texport stats as txt/pdf")
        # print("- rawstats:\tsave rawstats of match in txt (sep=';')")
        print("- exit:\t\texit program")  
        
    if type == "stats":
        print("\nOPTIONS")
        print("- team:\t\tview stats of certain team")
        print("- player:\tview stats of certain player")
        print("- exit:\t\texit program")
    
def _clock_prefix(tracker, quarter):
    """Event-string prefix (quarter + MMSS) from the video, or None."""
    if tracker is None:
        return None
    sample = tracker.sample()
    if sample is None or not sample.usable:
        return None
    return f"{quarter}{sample.event_time}"


def setup_tracker(options, quarter=None, match_id=None):
    """Build the game-clock tracker, or return None to stay fully manual."""
    if options.no_video_clock:
        return None

    tracker = GameClockTracker(csv_path=options.csv,
                               anchor_clock=options.anchor_clock,
                               anchor=options.anchor,
                               match_id=match_id)
    try:
        path = tracker.load_csv()
        print(f"\nGAME CLOCK: using {path.name}")
        tracker.start()
        tracker.set_quarter(quarter)
        info = tracker.anchor_to_video(on_wait=lambda msg: print(f"  {msg}"))
    except ClockLogError as exc:
        print(f"\nGAME CLOCK: {exc}")
        print("Continuing without automatic clock times; type them yourself.")
        tracker.stop()
        return None
    except KeyboardInterrupt:
        print("\nGAME CLOCK: anchoring cancelled; type the times yourself.")
        tracker.stop()
        return None

    print_anchor(info)
    return tracker


def print_anchor(info):
    """One-line confirmation of where the video was lined up with the CSV."""
    where = (f"quarter {info['quarter']} " if info["quarter"] is not None else "")
    print(f"GAME CLOCK: {info['document']} anchored at {info['video_seconds']:.3f}s "
          f"= {where}{info['anchor_clock']} ({info['real_time_text']}), "
          f"offset {info['offset']:+.3f}s")


def ask_sync(quarter):
    """Ask whether the video still lines up with the CSV for this quarter."""
    try:
        reply = input(f"Sync video for quarter {quarter}? (y/n): ")
    except EOFError:
        return False
    # Only an explicit "y" re-syncs; anything else keeps the current offset.
    return reply.strip().lower() == "y"


def anchor_quarter(tracker, quarter):
    """Re-anchor the video on `quarter`. False means fall back to manual times."""
    tracker.invalidate_anchor()
    try:
        info = tracker.anchor_to_video(quarter=quarter,
                                       on_wait=lambda msg: print(f"  {msg}"))
    except (ClockLogError, KeyboardInterrupt, EOFError) as exc:
        print(f"GAME CLOCK: {exc or 'anchoring cancelled'}; "
              "type the times yourself.")
        return False
    print_anchor(info)
    return True


def sync_quarter(tracker, quarter, options):
    """Per-quarter sync step. Returns the tracker, or None to go manual."""
    tracker.set_quarter(quarter)

    # Without an offset there is nothing to keep, so never offer to skip.
    if not tracker.ready:
        print("\nGAME CLOCK: the video is not lined up with the CSV yet.")
    elif tracker.document_changed():
        print("\nGAME CLOCK: a different video is open in QuickTime Player.")
    elif options.anchor is not None or not sys.stdin.isatty():
        return tracker
    elif not ask_sync(quarter):
        print(f"GAME CLOCK: keeping the current sync for quarter {quarter}.")
        return tracker

    if anchor_quarter(tracker, quarter):
        return tracker
    tracker.stop()
    return None


def event_input(quarter, tracker=None) -> str:
    lines = read_history()
    counta = 0
    countb = 0

    # The first five characters (period digit + MMSS) are kept in step with the
    # video while the prompt is open; everything the user types after them is
    # left alone.
    autofill = _clock_prefix(tracker, quarter)
    default_text = autofill or f"{quarter}"

    # "prefix" is the text this code last wrote, so a mismatch means the user
    # edited it themselves. "bare" marks the quarter-only fallback, which may
    # only be upgraded while the line is still untouched.
    live = {
        "active": tracker is not None,
        "prefix": default_text,
        "bare": autofill is None,
    }

    def base_default():
        """The text for the 'new event' state, with the freshest clock."""
        return _clock_prefix(tracker, quarter) or autofill or f"{quarter}"

    bindings = KeyBindings()
    def update_defaulta():
        nonlocal default_text
        if counta > 0:
            default_text = lines[-counta].strip()
        else:
            default_text = base_default()

    def update_defaultb():
        nonlocal default_text
        if countb == 1:
            default_text = lines[-1].strip()[:5]
        elif countb == 2:
            default_text = lines[-1].strip()
        else:
            default_text = base_default()

    def apply_recall(event, at_base):
        """Write a recalled/base entry and resync the live-clock state."""
        event.app.current_buffer.text = default_text
        event.app.current_buffer.cursor_position = len(default_text)
        # Only the plain new-event state keeps following the video.
        live["active"] = at_base and tracker is not None
        if live["active"]:
            live["prefix"] = default_text
            live["bare"] = len(default_text) < PREFIX_LEN

    @bindings.add('up')
    def _(event):
        nonlocal counta
        nonlocal countb
        if counta < len(lines):
            countb = 2
            counta += 1
            update_defaulta()
            apply_recall(event, at_base=False)

    @bindings.add('down')
    def _(event):
        nonlocal counta
        nonlocal countb
        if counta > 1:
            countb = 2
        elif counta == 1:
            countb = 0
        if counta > 0:
            counta -= 1
            update_defaulta()
            apply_recall(event, at_base=counta == 0 and countb == 0)
            
    @bindings.add('tab')
    def _(event):
        nonlocal counta
        nonlocal countb
        countb += 1
        countb = countb % 3
        update_defaultb()
        apply_recall(event, at_base=countb == 0)
        if countb == 2:
            counta = 1
        else:
            counta = 0

    session = PromptSession(key_bindings=bindings)
    buffer = session.default_buffer

    def refresh_prefix():
        """Re-point the prefix at the current clock; False stops the updates."""
        fresh = _clock_prefix(tracker, quarter)
        if not fresh:
            return True
        prefix = live["prefix"]
        text = buffer.text

        if live["bare"]:
            # Nothing typed yet, so the quarter-only line can become a full
            # prefix. Once the user starts typing, leave it to them.
            if text != prefix:
                return False
            updated, cursor = fresh, len(fresh)
        else:
            if not text.startswith(prefix):
                return False  # the user edited the clock themselves
            if fresh == prefix:
                return True
            shift = len(fresh) - len(prefix)
            updated = fresh + text[len(prefix):]
            cursor = (buffer.cursor_position + shift
                      if buffer.cursor_position >= len(prefix)
                      else min(buffer.cursor_position, len(fresh)))

        live["prefix"] = fresh
        live["bare"] = False
        if updated != text:
            buffer.set_document(Document(updated, cursor), bypass_readonly=True)
        return True

    async def follow_clock():
        while True:
            await asyncio.sleep(LIVE_CLOCK_INTERVAL)
            if not live["active"]:
                continue
            if not refresh_prefix():
                live["active"] = False

    def start_following():
        # Background tasks are cancelled and awaited by the application itself
        # when the prompt finishes, including on Ctrl+C.
        session.app.create_background_task(follow_clock())

    eventstring = session.prompt(
        default=default_text,
        pre_run=start_following if tracker is not None else None,
    )
    return eventstring
    
def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Basketball match event entry, with optional game-clock "
                    "autofill from a video open in QuickTime Player.")
    parser.add_argument(
        "--csv",
        help="Game-clock CSV. Defaults to the single time_*.csv in "
             "quicktime_timestamp/; you are asked to pick when there are several.")
    parser.add_argument(
        "--anchor-clock", default=DEFAULT_ANCHOR_CLOCK,
        help="Game clock value used to line the video up with the CSV "
             "(default: %(default)s).")
    parser.add_argument(
        "--anchor",
        help="Video timestamp showing --anchor-clock, as seconds, MM:SS.mmm or "
             "HH:MM:SS.mmm. Skips the interactive anchor prompt.")
    parser.add_argument(
        "--no-video-clock", action="store_true",
        help="Disable QuickTime clock autofill and type every event time by hand.")
    options = parser.parse_args(argv)

    if options.anchor is not None:
        try:
            options.anchor = parse_anchor_value(options.anchor)
        except ValueError as exc:
            parser.error(f"--anchor: {exc}")
    return options


def main():
    options = parse_args()
    holder = {}
    try:
        _run_app(options, holder)
    finally:
        # The background poller owns an osascript process; always shut it down.
        if holder.get("tracker") is not None:
            holder["tracker"].stop()


def cmd_create() -> Match:
    m = Match()
    m.create_match(input("game ID: "), 
                   input("home team: "), 
                   input("away team: "), 
                   input("date: "), 
                   input("time: "), 
                   input("location: "),
                   True)
    added = False
    while not added:
        homeplayers = input("players (home)\n")
        awayplayers = input("players (away)\n")
        added = m.add_teams(homeplayers.split(";"), awayplayers.split(";"))

    write_history([m.matchID, m.home.name, m.away.name, m.date, m.time,
                   m.location, homeplayers, awayplayers])
    return m


def cmd_select() -> Match | None:
    matches = []
    for file in os.listdir("matches"):
        if file.endswith(".txt") and not file == "history.txt":
            matches.append(file.split('.')[0])
            print("game " + file.split('.')[0])

    if len(matches) == 0: 
        print("no matches found")
        return None

    match_id = input("SELECT MATCH BY ID: ")
    if match_id not in matches:
        print("invalid matchID")
        return None

    shutil.copyfile(f"matches/{match_id}.txt", HISTORY)
    lines = read_history()
    m = Match.from_history(lines, prnt=True)
    print(f"selected match {match_id} with {len(lines)-8} written lines and {len(m.events)} added events")
    return m


def cmd_stats() -> None:
    d = Data()
    if not d.n_exports():
        d.read(prnt=False)
        d.add_data()
        d.export()

    command = None
    while not command == "exit":
        prints("stats")
        command = input()

        if command == "team":
            StatsReport().export_team_stats()
        elif command == "player":
            StatsReport().export_player_stats()


def cmd_edit(m: Match, command: str, options, holder: dict) -> Match:
    if m.events == None:
        m.start_match()

    quarter = command[4]
    if quarter not in VALID_QUARTERS:
        print("invalid quarter")
        return m

    # Re-opening a finished quarter drops its "end" line instead of adding a new "edit" line.
    lines = read_history()
    if lines[-1] == f"{quarter}end":
        write_history(lines[:-1])
    else:
        append_history(command)

    m.edit = True
    m.add_event(Event.parse(command))

    if m.count_events(quarter) < 2:
        added = False
        while not added:
            print("ADD STARTERS")
            homestarters = input("home: ")
            awaystarters = input("away: ")
            added = m.add_starters(quarter, homestarters.split(","), awaystarters.split(","))
            if added:
                append_history(f"H{homestarters}", f"A{awaystarters}")

    # Set the tracker up on the first edit quarter, so a match can be
    # created or selected before anchoring interrupts.
    tracker = holder.get("tracker")
    if tracker is None and not options.no_video_clock:
        tracker = setup_tracker(options, quarter, match_id=m.matchID)
    elif tracker is not None:
        tracker = sync_quarter(tracker, quarter, options)
    holder["tracker"] = tracker

    print("ADD EVENTS (enter 'end' to stop)")
    eventstring = command
    while not eventstring == quarter + "end":
        eventstring = event_input(quarter, tracker)
        e = Event.parse(eventstring)
        if e is not None:
            result = m.add_event(e)
            if not result == True:
                print(result)
            else:
                append_history(eventstring)
        elif eventstring[1:8] == "oncourt":
            m.print_oncourt()
        else:
            print("invalid event")

    m.edit = False

    # Rebuild from the file so hand-made fixes in history.txt are checked too.
    m = Match.from_history(read_history())
    if m.check_boxscore(m.all_quarters())==True: print("exited succesfully")
    return m


def cmd_summary(m: Match) -> None:
    if m.events == None or len(m.events) == 0:
        print("no events")
    else:
        quarters = input("which quarter(s)? ").split(",")
        if all(quarter in m.all_quarters() for quarter in quarters):
            m.print_summary(quarters)


def cmd_log(m: Match) -> None:
    quarters = input("which quarter(s)? ").split(",")
    if m.events == None or len(m.events) == 0:
        print("no events")
    else:
        m.print_events(quarters)


def cmd_box(m: Match) -> None:
    if m.events == None or len(m.events) == 0:
        print("no events")
    else:
        quarters = input("which quarter(s)? ").split(",")
        if m.check_boxscore(quarters)==True: m.print_boxscore(quarters)


def cmd_save(m: Match) -> None:
    if os.path.isfile(f"matches/{m.matchID}.txt"):
        print(f"match is already saved under {m.matchID}.txt")
        if input("overwrite existing file? (y/n) ") == "y":
            shutil.copyfile(HISTORY, f"matches/{m.matchID}.txt") 
    else:
        shutil.copyfile(HISTORY, f"matches/{m.matchID}.txt") 


def cmd_export(m: Match) -> None:
    if input(f"want to make a game report of match {m.matchID}? (y/n) ") == "y":
        gamebook = GameReport(m)
        quarters = m.all_quarters()
        gamebook.make_txt(quarters)
        gamebook.make_pdf(quarters)


MATCH_COMMANDS = {
    "summary": cmd_summary,
    "log": cmd_log,
    "box": cmd_box,
    "save": cmd_save,
    "export": cmd_export,
}


def _run_app(options, holder):
    m = None
    while m is None:
        prints("intro")
        command = input()

        if command == "create":
            m = cmd_create()
        elif command == "select":
            m = cmd_select()
        elif command == "stats":
            # Leaving the stats menu ends the program.
            cmd_stats()
            return
        elif command == "exit":
            return

    while True:
        prints("match")
        command = input()

        if command[:4] == "edit" and len(command) == 5:
            m = cmd_edit(m, command, options, holder)
        elif command in MATCH_COMMANDS:
            MATCH_COMMANDS[command](m)
        elif command == "exit":
            return

        # if command == "rawstats":
        #     rawstat = rawstats(m)
        #     rawstat.gameinfo()
        #     rawstat.create_boxscores()
        #     rawstat.save_teamstats()
        #     rawstat.save_playerstats()


if __name__ == '__main__':
    main()