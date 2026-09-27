from event import event
from match import match
from stats_export import statsreport
from gamereport import gamereport
# from rawstats import rawstats
from data_export import data
from gameclock import ClockLogError, GameClockTracker, DEFAULT_ANCHOR_CLOCK, parse_anchor_value
from copy import deepcopy
import argparse
import asyncio
import os
import shutil
from prompt_toolkit import PromptSession
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings

# Event strings start with the period digit plus MMSS.
PREFIX_LEN = 5
LIVE_CLOCK_INTERVAL = 0.2

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
        print("- export:\texport stats of match as txt/pdf")
        # print("- rawstats:\tsave rawstats of match in txt (sep=';')")
        print("- exit:\t\texit program")     
    
def _clock_prefix(tracker, quarter):
    """Event-string prefix (quarter + MMSS) from the video, or None."""
    if tracker is None:
        return None
    sample = tracker.sample()
    if sample is None or not sample.usable:
        return None
    return f"{quarter}{sample.event_time}"


def setup_tracker(options):
    """Build the game-clock tracker, or return None to stay fully manual."""
    if options.no_video_clock:
        return None

    tracker = GameClockTracker(csv_path=options.csv,
                               anchor_clock=options.anchor_clock,
                               anchor=options.anchor)
    try:
        path = tracker.load_csv()
        print(f"\nGAME CLOCK: using {path.name}")
        tracker.start()
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

    print(f"GAME CLOCK: {info['document']} anchored at {info['video_seconds']:.3f}s "
          f"= {options.anchor_clock} ({info['real_time_text']})")
    return tracker


def event_input(quarter, tracker=None) -> str:
    f = open("matches/history.txt", "r")
    lines = f.readlines()
    f.close()
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


def _run_app(options, holder):
    tracker = None
    eventstring = None
    while not eventstring in {"create", "select", "exit"}:
        prints("intro")
        eventstring = input()
        
        if eventstring == "create":
            m = match()
            m.create_match(input("game ID: "), 
                           input("home team: "), 
                           input("away team: "), 
                           input("date: "), 
                           input("time: "), 
                           input("location: "),
                           True)
            b = False
            while not b:
                homeplayers = input("players (home)\n")
                awayplayers = input("players (away)\n")
                b = m.add_teams(homeplayers.split(";"), awayplayers.split(";"))
            
            f = open(f"matches/history.txt", "w")
            f.writelines(m.matchID + '\n')
            f.writelines(m.home.name + '\n')
            f.writelines(m.away.name + '\n')
            f.writelines(m.date + '\n')
            f.writelines(m.time + '\n')
            f.writelines(m.location + '\n')
            f.writelines(homeplayers + '\n')
            f.writelines(awayplayers + '\n')
            f.close()
                                    
        elif eventstring == "select":
            matches = []
            for file in os.listdir("matches"):
                if file.endswith(".txt") and not file == "history.txt":
                    matches.append(file.split('.')[0])
                    print("game " + file.split('.')[0])
                    
            if len(matches) == 0: 
                print("no matches found")
                eventstring = None
            
            else:
                id = input("SELECT MATCH BY ID: ")
                
                if id in matches:
                    shutil.copyfile(f"matches/{id}.txt", "matches/history.txt") 
                            
                    f = open("matches/history.txt", "r")
                    lines = f.read().splitlines()
                    f.close()
                    
                    m = match()
                    m.create_match(lines[0],
                                   lines[1],
                                   lines[2],
                                   lines[3],
                                   lines[4],
                                   lines[5],
                                   True)
                    homeplayers = lines[6]
                    awayplayers = lines[7]
                    m.add_teams(homeplayers.split(";"), awayplayers.split(";"))
                    
                    m.start_match()
                    added_events = 0
                    n_events = len(lines)-8
                    for n in range(8, 8+n_events):
                        eventstring = deepcopy(lines[n])
                        e = event()
                        b = e.extract_eventstring(eventstring)
                        if eventstring[:4] == "edit":
                            m.add_event(e)
                            added_events += 1
                            quarter = eventstring[4]
                        elif eventstring[0] == "H":
                            homestarters = eventstring[1:].split(",")
                            del e
                        elif eventstring[0] == "A":
                            awaystarters = eventstring[1:].split(",")
                            m.add_starters(quarter, homestarters, awaystarters)              
                            del e
                        elif b:
                            m.add_event(e)
                            added_events += 1
                        else:
                            del e

                    print(f"selected match {id} with {n_events} written lines and {added_events} added events")
                    eventstring = "select"
                else:
                    print("invalid matchID")
                    eventstring = None
            
        elif eventstring == "stats":
            d = data()
            if not d.n_exports():
                d.read(prnt=False)
                d.add_data()
                d.export()
            
            s = statsreport()
            s.make_pdf()
            exit()
            
        elif eventstring == "exit":
            exit()
                    
    while not eventstring in {"exit"}:
        
        prints("match")
        eventstring = input()
        
        if eventstring[:4] == "edit" and len(eventstring) == 5:
            if m.events == None:
                m.start_match()
            
            quarter = eventstring[4]
            if not quarter in {"1","2","3","4","5","6","7","8"}: print("invalid quarter")
               
            # check of laatste line het einde was van hetzelfde kwart 
            f = open(f"matches/history.txt", "r")
            lines = f.readlines()
            lastline = lines[-1]
            if lastline[:-1] == (f"{quarter}end"):
                f.close()
                # laatste line verwijderen
                f = open("matches/history.txt", 'w')
                for line in lines[:-1]:
                    f.writelines(line)
                f.close()
            else:
                f.close()
                f = open(f"matches/history.txt", "a")
                f.writelines(eventstring + '\n')
                f.close()
            
            # Start edit-mode
            m.edit = True
            e = event()
            b = e.extract_eventstring(eventstring)
            m.add_event(e)

            if m.count_events(quarter) < 2:
                b = False
                while not b:
                    print("ADD STARTERS")
                    homestarters = input("home: ")
                    awaystarters = input("away: ")
                    b = m.add_starters(quarter, homestarters.split(","), awaystarters.split(","))
                    if b:  
                        f = open(f"matches/history.txt", "a")
                        f.writelines(f"H{str(homestarters)}" + '\n')
                        f.writelines(f"A{str(awaystarters)}" + '\n')
                        f.close()
                    
            # Set the tracker up on the first edit quarter, so a match can be
            # created or selected before anchoring interrupts.
            if tracker is None and not options.no_video_clock:
                tracker = setup_tracker(options)
                holder["tracker"] = tracker
            elif tracker is not None and tracker.document_changed():
                print("\nGAME CLOCK: a different video is open in QuickTime Player.")
                tracker.invalidate_anchor()
                try:
                    info = tracker.anchor_to_video(on_wait=lambda msg: print(f"  {msg}"))
                    print(f"GAME CLOCK: {info['document']} anchored at "
                          f"{info['video_seconds']:.3f}s = {options.anchor_clock}")
                except (ClockLogError, KeyboardInterrupt) as exc:
                    print(f"GAME CLOCK: {exc or 'anchoring cancelled'}; "
                          "type the times yourself.")
                    tracker.stop()
                    tracker = None
                    holder["tracker"] = None

            print("ADD EVENTS (enter 'end' to stop)")
            while not eventstring == quarter + "end":
                eventstring = event_input(quarter, tracker)
                e = event()
                b = e.extract_eventstring(eventstring)
                if b:
                    c = m.add_event(e)
                    if not c == True:
                        print(c)
                    else:
                        f = open(f"matches/history.txt", "a")
                        f.writelines(eventstring + '\n')
                        f.close()
                elif eventstring[1:8] == "oncourt":
                    m.print_oncourt()
                    del e
                else:
                    print("invalid event")
                    del e
                    
            # Stop edit-mode
            m.edit = False
            
            # Read file opnieuw om met de hand gefixte dingen in history.txt mee te nemen in de check
            f = open("matches/history.txt", "r")
            lines = f.read().splitlines()
            f.close()
            
            m = match()
            m.create_match(lines[0],
                            lines[1],
                            lines[2],
                            lines[3],
                            lines[4],
                            lines[5],
                            False)

            homeplayers = lines[6]
            awayplayers = lines[7]
            m.add_teams(homeplayers.split(";"), awayplayers.split(";"))
            
            m.start_match()
            added_events = 0
            n_events = len(lines)-8
            for n in range(8, 8+n_events):
                eventstring = deepcopy(lines[n])
                e = event()
                b = e.extract_eventstring(eventstring)
                if eventstring[:4] == "edit":
                    m.add_event(e)
                    added_events += 1
                    quarter = eventstring[4]
                elif eventstring[0] == "H":
                    homestarters = eventstring[1:].split(",")
                    del e
                elif eventstring[0] == "A":
                    awaystarters = eventstring[1:].split(",")
                    m.add_starters(quarter, homestarters, awaystarters)              
                    del e
                elif b:
                    m.add_event(e)
                    added_events += 1
                else:
                    del e
            
            quarters = m.all_quarters()
            if m.check_boxscore(quarters)==True: print("exited succesfully")
        
        if eventstring == "summary":
            if m.events == None or len(m.events) == 0:
                print("no events")
            else:
                # quarters = m.all_quarters()
                quarters = input("which quarter(s)? ").split(",")
                if all(quarter in m.all_quarters() for quarter in quarters):
                    m.print_summary(quarters)
                    
        if eventstring == "log":
            quarters = input("which quarter(s)? ").split(",")
            if m.events == None or len(m.events) == 0:
                print("no events")
            else:
                m.print_events(quarters)
            
        if eventstring == "box":
            if m.events == None or len(m.events) == 0:
                print("no events")
            else:
                quarters = input("which quarter(s)? ").split(",")
                if m.check_boxscore(quarters)==True: m.print_boxscore(quarters)
            
        if eventstring == "save":
            if os.path.isfile(f"matches/{m.matchID}.txt"):
                print(f"match is already saved under {m.matchID}.txt")
                if input("overwrite existing file? (y/n) ") == "y":
                    shutil.copyfile("matches/history.txt", f"matches/{m.matchID}.txt") 
            else:
                shutil.copyfile("matches/history.txt", f"matches/{m.matchID}.txt") 

        if eventstring == "export":
            if input(f"want to make a game report of match {m.matchID}? (y/n) ") == "y":
                gamebook = gamereport(m)
                quarters = m.all_quarters()
                gamebook.make_txt(quarters)
                gamebook.make_pdf(quarters)

        # if eventstring == "rawstats":
        #     rawstat = rawstats(m)
        #     rawstat.gameinfo()
        #     rawstat.create_boxscores()
        #     rawstat.save_teamstats()
        #     rawstat.save_playerstats()
                         
        if eventstring == "exit":
            exit()
            
if __name__ == '__main__':
    main()