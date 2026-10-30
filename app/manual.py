"""In-program manual: the help texts shown when the user types 'help'."""

import re

HELP_WORDS = {"help", "?", "h"}
# The event prompt is pre-filled with the quarter (and clock), so "help"
# arrives as e.g. "1help" or "10839help".
_EVENT_HELP = re.compile(r"[0-9]*\s*(help|\?)")


def is_help(text: str) -> bool:
  return text.strip().lower() in HELP_WORDS


def is_event_help(line: str) -> bool:
  return _EVENT_HELP.fullmatch(line.strip().lower()) is not None


def unknown_command(command: str) -> str:
  return f"unknown command '{command}' - type 'help' to see what each command does"


def invalid_event(quarter: str) -> str:
  return f"invalid event - type '{quarter}help' to see the event codes and commands"


TOPICS = {
  "start": """
HOW IT WORKS
  1. Start a game with 'create' (new game) or 'open' (a saved game).
  2. In the game menu, type 'edit1' to enter the events of quarter 1.
  3. Type one event per line, close the quarter with '1end'.
     Repeat for edit2, edit3, edit4 (edit5-edit8 are overtimes).
  4. Type 'save' to store the game, 'export' for a PDF gamebook.

START MENU
  create   New game. You are asked for the game ID, both teams, date
           (dd-mm-yyyy), time (HH:MM), location and both rosters.
           A roster is number,name;number,name;... with at least 6 players,
           e.g. 4,Jan;5,Piet;6,Kees;7,Joost;9,Bas;12,Tim
  open     Open a saved game from data/matches/ by its game ID.
  stats    Season stats per team or player, as PDF in data/exports/.
  exit     Quit.

More detail: README.md in the project folder.
""",
  "match": """
GAME MENU
  edit1    Enter events for quarter 1 (edit2-edit4; edit5-edit8 = overtime).
           A new quarter first asks for the 5 starters of each team, e.g.
           4,5,6,7,9. Inside a quarter, type 'help' for all event codes.
           Typing edit1 again reopens a closed quarter.
  summary  Score and team totals of chosen quarters.
  log      All events of chosen quarters (play-by-play).
  box      Boxscore of chosen quarters.
  save     Store the game as data/matches/<game ID>.txt. Do this before you quit!
  export   Make a gamebook (txt + pdf) in data/gamebooks/.
  exit     Quit. Unsaved events stay in data/matches/history.txt.

When asked "which quarter(s)?", type e.g. 1 or 1,2 - or press Enter for all.
""",
  "stats": """
STATS MENU
  team     Pick a team (arrow keys up/down, Enter) -> PDF in data/exports/.
  player   Type (part of) a player's name, then pick with up/down + Enter
           -> PDF in data/exports/.
  exit     Quit the program.
""",
}


def event_help(quarter: str) -> str:
  q = quarter
  start = "1000" if quarter in {"1", "2", "3", "4"} else "0500"
  return f"""
EVENT CODES - type one event per line, without spaces:
  quarter + clock (MMSS) + action + team (H/A) + shirt number [+ extra player]
  e.g. {q}04392mA12aA4 = quarter {q}, 04:39, made 2 by away #12, assist by away #4

  made 2 / 3 / FT        {q}04392mH7   {q}04393mH7   {q}04391mH7   assist: {q}04392mH7aH4
  missed 2 / 3 / FT      {q}04392H7    {q}04393H7    {q}04391H7    block:  {q}04392H7bA5
  rebound                {q}0439rA12   team rebound: {q}0439rA
  turnover               {q}0439tH13   stolen by A11: {q}0439tH13sA11   team: {q}0439tH
  foul + free throws 0-3 {q}0439f2H4   (f0 = no free throws)
  unsportsm. / disq.     {q}0439fuA8   {q}0439fdA8
  technical foul         {q}0439ftH4   on the team/bench: {q}0439ftH
  assist / steal / block {q}0439aH4    {q}0439sH4    {q}0439bH4
  substitution           {q}0439outH7inH11   (H7 off, H11 on)
  jump ball              {q}{start}jA   (team that gets the ball)
  timeout                {q}0439toH

OTHER
  {q}oncourt   show who is on the court
  {q}end       close quarter {q} and go back to the game menu
  help       show this list

KEYS
  Up / Down   browse earlier lines
  Tab         copy the time of the last line, press again for the whole line
"""
