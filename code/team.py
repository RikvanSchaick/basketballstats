from players import players
class team():
    def __init__(self, name:str, team:str) -> None:
        self.name = name
        self.team = team
        self.players = None
        self.starters = []
        
    def add_team(self, team:list) -> None:
        self.players = players()
        self.players.create_team(self.team)
        for player in team:
            number, name = player.split(",")
            self.players.add_player(number, name)
            
    def add_starters(self, quarter:str, lineup:list) -> None:
        if quarter == "1": self.players.add_starters(lineup)
        self.starters.append(lineup)