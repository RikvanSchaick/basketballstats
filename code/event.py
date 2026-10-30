import re
from dataclasses import dataclass

# Every event line starts with the quarter (1-8) and the game clock as MMSS (10:00 down to 00:00).
_PREFIX = r"(?P<quarter>[1-8])(?P<time>0[0-9](?:[0-5][0-9]|60)|1000)"
_TEAM = r"(?P<team>[HA])"
_PLAYER = r"(?P<team>[HA])(?P<player>[0-9]{1,2})"
_TEAM_OR_PLAYER = r"(?P<team>[HA])(?P<player>[0-9]{1,2})?"


def _second_player(actions: str) -> str:
    return rf"(?P<action2>{actions})(?P<team2>[HA])(?P<player2>[0-9]{{1,2}})"


# (action codes, what follows the action, whether a second player must be a teammate)
_GRAMMAR = [
    # 10624outH7inH11: H7 is substituted by H11
    ("out", _PLAYER + _second_player("in"), True),
    # 108392mA12aA4: A12 makes a 2, assisted by A4
    ("1m|2m|3m", _PLAYER + f"(?:{_second_player('a')})?", True),
    # 104412H8bA17: H8 misses a 2, blocked by A17
    ("2|3", _PLAYER + f"(?:{_second_player('b')})?", False),
    # 10827tH13sA11: H13 turns it over, stolen by A11; 10425tH: team turnover
    ("t", rf"(?P<team>[HA])(?:(?P<player>[0-9]{{1,2}})(?:{_second_player('s|b')})?)?", False),
    # 10813rA12 / 10624rA: player or team rebound (technical fouls likewise)
    ("r|ft", _TEAM_OR_PLAYER, None),
    # 11000jA: possession after the jump ball; 10500toH: timeout
    ("j|to", _TEAM, None),
    ("1|a|s|b|f0|f1|f2|f3|fu|fd", _PLAYER, None),
]

_PATTERNS = [(re.compile(rf"{_PREFIX}(?P<action>{actions}){body}"), same_team)
             for actions, body, same_team in _GRAMMAR]
_START = re.compile(r"edit(?P<quarter>[1-8])")
_END = re.compile(r"(?P<quarter>[1-8])end")


@dataclass(eq=False)
class Event:
    string: str | None = None
    quarter: str | None = None
    time: str | None = None
    actionID: str | None = None
    actionID2: str | None = None
    team: str | None = None
    playerID: str | None = None
    playerID2: str | None = None
    score: list[int] | None = None
    lead: int | None = None

    @classmethod
    def parse(cls, eventstring: str) -> "Event | None":
        """Parse one history line into an Event, or None if it is not a valid event."""
        if m := _START.fullmatch(eventstring):
            time = "1000" if m["quarter"] in {"1", "2", "3", "4"} else "0500"
            return cls(string=eventstring, quarter=m["quarter"], time=time, actionID="start")
        if m := _END.fullmatch(eventstring):
            return cls(string=eventstring, quarter=m["quarter"], time="0000", actionID="end")

        for pattern, same_team in _PATTERNS:
            m = pattern.fullmatch(eventstring)
            if m is None:
                continue
            groups = m.groupdict()
            if groups.get("team2") and (groups["team2"] == m["team"]) != same_team:
                return None
            return cls(string=eventstring,
                       quarter=m["quarter"],
                       time=m["time"],
                       actionID=m["action"],
                       actionID2=groups.get("action2"),
                       team=m["team"],
                       playerID=groups.get("player"),
                       playerID2=groups.get("player2"))
        return None

    def eventstring(self) -> str:
        return self.string

    def print_score(self, lead:bool) -> str | tuple[str, str]:
        if lead: 
            if self.lead == 0: return f"{self.score[0]}-{self.score[1]}", f"TIE"
            if self.lead > 0: return f"{self.score[0]}-{self.score[1]}", f"+{self.lead}"
            return f"{self.score[0]}-{self.score[1]}", f"{self.lead}"
        return f"{self.score[0]}-{self.score[1]}"
    
    def print_event(self, terms:object, players1:list = None, players2:list = None) -> str:
        if self.actionID in {"j", "to"}:
            return f"{terms[self.actionID]}"
        if self.actionID == "ft" and self.playerID == None:
            return f"{terms[self.actionID]}"
        if self.actionID == "r" and self.playerID == None:
            return f"{terms[self.actionID]}"
        if self.actionID == "t" and self.playerID == None:
            return f"{terms[self.actionID]}"
        if self.actionID == "out":
            if players1 == None:
                return f"{terms[self.actionID]}: #{self.playerID} {terms[self.actionID2]} #{self.playerID2}"
            return f"{terms[self.actionID]}: {players1.names[self.playerID]} {terms[self.actionID2]} {players1.names[self.playerID2]}"
        if self.actionID in {'t', '2', '3'} and not self.actionID2 == None:
            if players1 == None:
                return f"#{self.playerID} {terms[self.actionID]}", f"#{self.playerID2} {terms[self.actionID2]}"
            return f"{players1.names[self.playerID]} {terms[self.actionID]}", f"{players2.names[self.playerID2]} {terms[self.actionID2]}"
        if self.actionID in {'1', '2', '3'}:
            if players1 == None:
                return f"#{self.playerID} {terms[self.actionID]}"
            return f"{players1.names[self.playerID]} {terms[self.actionID]}"
        if self.actionID in {'2m', '3m'} and not self.playerID2 == None:
            if players1 == None:
                return f"#{self.playerID} {terms[self.actionID]} (#{self.playerID2} {terms[self.actionID2]})"
            return f"{players1.names[self.playerID]} {terms[self.actionID]} ({players1.names[self.playerID2]} {terms[self.actionID2]})"
        elif self.actionID in {'2m', '3m'}:
            if players1 == None:
                return f"#{self.playerID} {terms[self.actionID]}"
            return f"{players1.names[self.playerID]} {terms[self.actionID]}"
        if players1 == None:
            return f"#{self.playerID} {terms[self.actionID]}"
        return f"{players1.names[self.playerID]} {terms[self.actionID]}"
