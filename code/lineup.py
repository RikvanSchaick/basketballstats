# from player import player

class lineup():
    def __init__(self) -> None:
        self.names = None
        self.players = None
        self.team = None
        
    def create_lineup(self, team:str) -> None:
        self.names = {}
        self.players = []
        self.team = team
        
    def add_player(self, number:str, name:str) -> None:
        self.players.append([number, False])
        if len(name) == 0: name = None
        self.names[number] = name
        
    def add_starters(self, players:list) -> None:
        for player in self.players:
            if player[0] in players:
                player[1] = True
