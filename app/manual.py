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
  return f"unknown command '{command}' - press 'h' to see what each command does"


def invalid_event(quarter: str) -> str:
  return f"invalid event - type '{quarter}help' to see the event codes and commands"


TOPICS = {
  "start": """
HOW IT WORKS
  In a menu, press the key in [ ] to pick an option - no Enter needed.
  1. Press 'c' to create a new game, or 'o' to open a saved one.
  2. In the game menu, press '1' to enter the events of quarter 1.
  3. Type one event per line, close the quarter with '1end'.
     Repeat with 2, 3 and 4 (5-8 are overtimes).
  4. Press 's' to save the game, 'r' to make a PDF gamebook report.

START MENU
  [c] create   New game. You are asked for the game ID, both teams, date
               (dd-mm-yyyy), time (HH:MM), location and both rosters.
               A roster is number,name;number,name;... with at least 6 players,
               e.g. 4,Jan;5,Piet;6,Kees;7,Joost;9,Bas;12,Tim
  [o] open     Open a saved game from data/matches/ by its game ID.
  [s] stats    Season stats per team or player, as PDF in data/exports/.
  [e] exit     Quit.

More detail: README.md in the project folder.
""",
  "match": """
GAME MENU
  [1-8] edit(n)  Enter events for quarter n (1-4; 5-8 = overtime).
                 A new quarter first asks for the 5 starters of each team, e.g.
                 4,5,6,7,9. Inside a quarter, type 'help' for all event codes.
                 Pressing the same number again reopens a closed quarter.
  [o] overview   Score and team totals of chosen quarters.
  [g] gamelog    All events of chosen quarters (play-by-play).
  [x] boxscore   Boxscore of chosen quarters.
  [s] save       Store the game as data/matches/<game ID>.txt. Do this before
                 you quit!
  [r] report     Make a gamebook (txt + pdf) in data/gamebooks/.
  [b] back       Return to START MENU. Save first to keep this game by its ID.
  [e] exit       Quit. Unsaved events stay in data/matches/history.txt.

When asked "which quarter(s)?", type e.g. 1 or 1,2 - or press Enter for all.
""",
  "stats": """
STATS MENU
  [t] team     Pick a team (arrow keys up/down, Enter) -> PDF in data/exports/.
  [p] player   Type (part of) a player's name, then pick with up/down + Enter
               -> PDF in data/exports/.
  [b] back     Return to START MENU.
  [e] exit     Quit the program.
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
