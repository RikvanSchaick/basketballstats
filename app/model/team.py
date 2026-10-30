class Players:
  def __init__(self) -> None:
    self.names = None
    self.players = None
    self.team = None

  def create_team(self, team: str) -> None:
    self.names = {}
    self.players = []
    self.team = team

  def add_player(self, number: str, name: str) -> None:
    self.players.append([number, False])
    if len(name) == 0:
      name = None
    self.names[number] = name

  def add_starters(self, lineup: list) -> None:
    for player in self.players:
      if player[0] in lineup:
        player[1] = True


class Team:
  def __init__(self, name: str, team: str) -> None:
    self.name = name
    self.team = team
    self.players = None
    self.starters = []

  def add_team(self, team: list) -> None:
    self.players = Players()
    self.players.create_team(self.team)
    for player in team:
      number, name = player.split(",")
      self.players.add_player(number, name)

  def add_starters(self, quarter: str, lineup: list) -> None:
    if quarter == "1":
      self.players.add_starters(lineup)
    self.starters.append(lineup)
