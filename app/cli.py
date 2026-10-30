from app.model.event import Event
from app.model.match import Match
from app.stats.report import StatsReport
from app.reports.gamebook import GameReport

# from rawstats import rawstats
from app.stats.export import Data
from app.clock.gameclock import (
  DEFAULT_ANCHOR_CLOCK,
  parse_anchor_value,
)
from app.history import append_history, read_history, write_history
from app.prompt import event_input, setup_tracker, sync_quarter
from app import manual, style
import argparse
import os
import re
from app import paths
import shutil

VALID_QUARTERS = {"1", "2", "3", "4", "5", "6", "7", "8"}

QUICK_START = """\
quick start:
  python -m app                    start; type 'help' in any menu for a guide
  python -m app --no-video-clock   type every event time yourself

  In the program: 'create' a game (or 'open' a saved one), then 'edit1' to
  enter quarter 1, one event per line (type 'help' there for the codes),
  '1end' to close the quarter, and 'save' before you 'exit'.
  Full manual: README.md
"""


MENUS = {
  "intro": (
    "START MENU",
    [
      ("create", "create a new game"),
      ("open", "open a saved game"),
      ("stats", "season stats of a team or player"),
      ("help", "how this program works"),
      ("exit", "exit program"),
    ],
  ),
  "match": (
    "GAME MENU",
    [
      ("edit(n)", "enter events of a quarter (e.g. edit1)"),
      ("summary", "view summary of match"),
      ("log", "view gamelog of match"),
      ("box", "view boxscore of match"),
      ("save", "save match as txt"),
      ("export", "export gamebook as txt/pdf"),
      # ("rawstats", "save rawstats of match in txt (sep=';')"),
      ("help", "explain these commands"),
      ("exit", "exit program"),
    ],
  ),
  "stats": (
    "STATS MENU",
    [
      ("team", "view stats of certain team"),
      ("player", "view stats of certain player"),
      ("help", "explain these commands"),
      ("exit", "exit program"),
    ],
  ),
}


def prints(type: str):
  heading, items = MENUS[type]
  print(style.menu(heading, items))


def answer_menu(topic: str, command: str) -> None:
  """Show the manual for 'help', or say an unknown command was not understood."""
  if manual.is_help(command):
    print(style.manual(manual.TOPICS[topic]))
  elif command.strip():
    print(manual.unknown_command(command))


def event_help(quarter: str) -> str:
  """The styled event-code list; codes such as 104392mH7 or 1end stand out."""
  codes = rf"\b{quarter}(?:[0-9]{{4}}[0-9A-Za-z]*|end|oncourt)\b|\bhelp\b"
  return style.manual(manual.event_help(quarter), codes=codes)


def ask_quarters(m: Match) -> list | None:
  """Ask which quarters to show; Enter means all. None if any is unknown."""
  played = m.all_quarters()
  reply = input(f"which quarter(s)? (e.g. 1 or 1,2 - Enter for all {','.join(played)}): ")
  if not reply.strip():
    return played
  quarters = [quarter.strip() for quarter in reply.split(",")]
  unknown = [quarter for quarter in quarters if quarter not in played]
  if unknown:
    print(f"no events for quarter(s) {','.join(unknown)}; choose from {','.join(played)}")
    return None
  return quarters


def normalize_event_line(line: str, quarter: str) -> str:
  """Accept '<N>end' and '<N>oncourt' even when typed after the pre-filled clock."""
  line = line.strip()
  if m := re.fullmatch(rf"{quarter}[0-9]{{4}}(end|oncourt)", line):
    return quarter + m[1]
  return line


def parse_args(argv=None):
  parser = argparse.ArgumentParser(
    prog="python -m app",
    description="Basketball match event entry, with optional game-clock "
    "autofill from a video open in QuickTime Player.",
    epilog=style.manual(QUICK_START),
    formatter_class=argparse.RawDescriptionHelpFormatter,
  )
  parser.add_argument(
    "--csv",
    help="Game-clock CSV. Defaults to data/clock_logs/<match id>.csv, else "
    "the single time_*.csv there; you are asked to pick when there are several.",
  )
  parser.add_argument(
    "--anchor-clock",
    default=DEFAULT_ANCHOR_CLOCK,
    help="Game clock value used to line the video up with the CSV "
    "(default: %(default)s).",
  )
  parser.add_argument(
    "--anchor",
    help="Video timestamp showing --anchor-clock, as seconds, MM:SS.mmm or "
    "HH:MM:SS.mmm. Skips the interactive anchor prompt.",
  )
  parser.add_argument(
    "--no-video-clock",
    action="store_true",
    help="Disable QuickTime clock autofill and type every event time by hand.",
  )
  options = parser.parse_args(argv)

  if options.anchor is not None:
    try:
      options.anchor = parse_anchor_value(options.anchor)
    except ValueError as exc:
      parser.error(f"--anchor: {exc}")
  return options


def main():
  options = parse_args()
  paths.ensure_dirs()
  holder = {}
  try:
    _run_app(options, holder)
  finally:
    # The background poller owns an osascript process; always shut it down.
    if holder.get("tracker") is not None:
      holder["tracker"].stop()


def cmd_create() -> Match:
  m = Match()
  m.create_match(
    input("game ID: "),
    input("home team: "),
    input("away team: "),
    input("date: "),
    input("time: "),
    input("location: "),
    True,
  )
  added = False
  while not added:
    homeplayers = input("players (home)\n")
    awayplayers = input("players (away)\n")
    added = m.add_teams(homeplayers.split(";"), awayplayers.split(";"))

  write_history(
    [
      m.matchID,
      m.home.name,
      m.away.name,
      m.date,
      m.time,
      m.location,
      homeplayers,
      awayplayers,
    ]
  )
  return m


def cmd_open() -> Match | None:
  matches = []
  for file in os.listdir(paths.MATCHES):
    if file.endswith(".txt") and not file == "history.txt":
      matches.append(file.split(".")[0])
      print("game " + file.split(".")[0])

  if len(matches) == 0:
    print("no matches found")
    return None

  match_id = input("SELECT MATCH BY ID: ")
  if match_id not in matches:
    print("invalid matchID")
    return None

  shutil.copyfile(paths.match_file(match_id), paths.HISTORY)
  lines = read_history()
  m = Match.from_history(lines, prnt=True)
  print(
    f"selected match {match_id} with {len(lines) - 8} written lines and {len(m.events)} added events"
  )
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
    elif command != "exit":
      answer_menu("stats", command)


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
      print(style.title("ADD STARTERS"))
      homestarters = input("home: ")
      awaystarters = input("away: ")
      added = m.add_starters(quarter, homestarters.split(","), awaystarters.split(","))
      if added:
        append_history(f"H{homestarters}", f"A{awaystarters}")

  # Set the tracker up on the first edit quarter, so a match can be
  # created or opened before anchoring interrupts.
  tracker = holder.get("tracker")
  if tracker is None and not options.no_video_clock:
    tracker = setup_tracker(options, quarter, match_id=m.matchID)
  elif tracker is not None:
    tracker = sync_quarter(tracker, quarter, options)
  holder["tracker"] = tracker

  print("\n" + style.message("ADD EVENTS", "enter 'end' to stop"))
  eventstring = command
  while not eventstring == quarter + "end":
    eventstring = event_input(quarter, tracker)
    if manual.is_event_help(eventstring):
      print(event_help(quarter))
      continue
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
      print(style.body(manual.invalid_event(quarter)))

  m.edit = False

  # Rebuild from the file so hand-made fixes in history.txt are checked too.
  m = Match.from_history(read_history())
  if m.check_boxscore(m.all_quarters()) == True:
    print("exited succesfully")
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
    if m.check_boxscore(quarters) == True:
      m.print_boxscore(quarters)


def cmd_save(m: Match) -> None:
  if os.path.isfile(paths.match_file(m.matchID)):
    print(f"match is already saved under {m.matchID}.txt")
    if input("overwrite existing file? (y/n) ") == "y":
      shutil.copyfile(paths.HISTORY, paths.match_file(m.matchID))
  else:
    shutil.copyfile(paths.HISTORY, paths.match_file(m.matchID))


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
    elif command == "open":
      m = cmd_open()
    elif command == "stats":
      # Leaving the stats menu ends the program.
      cmd_stats()
      return
    elif command == "exit":
      return
    else:
      answer_menu("start", command)

  while True:
    prints("match")
    command = input()

    if command[:4] == "edit" and len(command) == 5:
      m = cmd_edit(m, command, options, holder)
    elif command in MATCH_COMMANDS:
      MATCH_COMMANDS[command](m)
    elif command == "exit":
      return
    else:
      answer_menu("match", command)

    # if command == "rawstats":
    #     rawstat = rawstats(m)
    #     rawstat.gameinfo()
    #     rawstat.create_boxscores()
    #     rawstat.save_teamstats()
    #     rawstat.save_playerstats()
