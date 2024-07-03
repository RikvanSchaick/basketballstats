from lineup import lineup

class team():
    def __init__(self, name:str, team:str) -> None:
        self.name = name
        self.team = team
        self.lineup = None
        self.starters = []
        
    def add_lineup(self, players:list) -> None:
        self.lineup = lineup()
        self.lineup.create_lineup(self.team)
        for player in players:
            number, name = player.split(",")
            self.lineup.add_player(number, name)
            
    def add_starters(self, quarter:str, players:list) -> None:
        if quarter == "1": self.lineup.add_starters(players)
        self.starters.append(players)