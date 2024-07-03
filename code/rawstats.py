from match import match
from boxscore import boxscore
from formulas import EFGpct, TSpct, ASTtoTO

class rawstats():
    def __init__(self, match:match) -> None:
        self.match = match
        self.FOLDER = f"data/{match.matchID}"
        self.quarters = self.match.all_quarters()
        self.box = boxscore()
        self.boxopp = boxscore()
        self.team = None
        
        while not self.team in {'H', "A"}:
            self.team = input("which team? (H/A) ")
        
    def gameinfo(self):
        file = open(self.FOLDER, "w")
        file.writelines(f"{max(self.quarters)}" + '\n')
        file.close()
        
    def create_boxscores(self):
        if self.team == "H":
            self.box.create_boxscore(self.match.home)
            self.box.add_gamelogs(self.match.events, self.quarters)
            self.box.make_boxscore(self.match.events, self.quarters)
            self.n_players = len(self.box.gamelogs.values())
            self.boxopp.create_boxscore(self.match.away)
            self.boxopp.add_gamelogs(self.match.events, self.quarters)
            self.boxopp.make_boxscore(self.match.events, self.quarters)
        if self.team == "A":
            self.box.create_boxscore(self.match.away)
            self.box.add_gamelogs(self.match.events, self.quarters)
            self.box.make_boxscore(self.match.events, self.quarters)
            self.n_players = len(self.box.gamelogs.values())
            self.boxopp.create_boxscore(self.match.home)
            self.boxopp.add_gamelogs(self.match.events, self.quarters)
            self.boxopp.make_boxscore(self.match.events, self.quarters)
        
    def save_teamstats(self):
        file = open(self.FOLDER, "a")
        file.writelines(f"{self.box.sec};{self.boxopp.sec}" + '\n')
        file.writelines(f"{self.box.fg};{self.boxopp.fg}" + '\n')
        file.writelines(f"{self.box.fga};{self.boxopp.fga}" + '\n')
        file.writelines(f"{self.box.tp};{self.boxopp.tp}" + '\n')
        file.writelines(f"{self.box.tpa};{self.boxopp.tpa}" + '\n')
        file.writelines(f"{self.box.ft};{self.boxopp.ft}" + '\n')
        file.writelines(f"{self.box.fta};{self.boxopp.fta}" + '\n')
        file.writelines(f"{self.box.oreb};{self.boxopp.oreb}" + '\n')
        file.writelines(f"{self.box.dreb};{self.boxopp.dreb}" + '\n')
        file.writelines(f"{self.box.reb};{self.boxopp.reb}" + '\n')
        file.writelines(f"{self.box.tmreb};{self.boxopp.tmreb}" + '\n')
        file.writelines(f"{self.box.ast};{self.boxopp.ast}" + '\n')
        file.writelines(f"{self.box.pf};{self.boxopp.pf}" + '\n')
        file.writelines(f"{self.box.stl};{self.boxopp.stl}" + '\n')
        file.writelines(f"{self.box.blk};{self.boxopp.blk}" + '\n')
        file.writelines(f"{self.box.to};{self.boxopp.to}" + '\n')
        file.writelines(f"{self.box.pm};{self.boxopp.pm}" + '\n')
        file.writelines(f"{self.box.pts};{self.boxopp.pts}" + '\n')
        file.writelines(f"{self.box.fgpct};{self.boxopp.fgpct}" + '\n')
        file.writelines(f"{self.box.tppct};{self.boxopp.tppct}" + '\n')
        file.writelines(f"{self.box.ftpct};{self.boxopp.ftpct}" + '\n')
        file.writelines(f"{self.match.largest_lead(self.quarters)[0]};{self.match.largest_lead(self.quarters)[1]}" + '\n')
        file.writelines(f"{self.match.second_chance_points(self.quarters)[0]};{self.match.second_chance_points(self.quarters)[1]}" + '\n')
        file.writelines(f"{self.match.points_off_turnovers(self.quarters)[0]};{self.match.points_off_turnovers(self.quarters)[1]}" + '\n')
        file.writelines(f"{EFGpct(self.box.fg, self.box.tp, self.box.fga)};{EFGpct(self.boxopp.fg, self.boxopp.tp, self.boxopp.fga)}" + '\n')
        file.writelines(f"{TSpct(self.box.pts, self.box.fga, self.box.fta)};{TSpct(self.boxopp.pts, self.boxopp.fga, self.boxopp.fta)}" + '\n')
        file.writelines(f"{ASTtoTO(self.box.ast, self.box.to)};{ASTtoTO(self.boxopp.ast, self.boxopp.to)}" + '\n')
        file.close()
        
    def save_playerstats(self):
        file = open(self.FOLDER, "a")
        file.writelines(f"{self.n_players}" + '\n')
        for gamelog in self.box.gamelogs.values():
            file.writelines(f"{gamelog.player};")
            file.writelines(f"{gamelog.team.lineup.names[gamelog.player]};")
            file.writelines(f"{gamelog.starter};")
            file.writelines(f"{gamelog.subbedin};")
            file.writelines(f"{gamelog.subbedout};")
            file.writelines(f"{gamelog.sec};")
            file.writelines(f"{gamelog.fg};")
            file.writelines(f"{gamelog.fga};")
            file.writelines(f"{gamelog.tp};")
            file.writelines(f"{gamelog.tpa};")
            file.writelines(f"{gamelog.ft};")
            file.writelines(f"{gamelog.fta};")
            file.writelines(f"{gamelog.oreb};")
            file.writelines(f"{gamelog.dreb};")
            file.writelines(f"{gamelog.reb};")
            file.writelines(f"{gamelog.ast};")
            file.writelines(f"{gamelog.pf};")
            file.writelines(f"{gamelog.stl};")
            file.writelines(f"{gamelog.blk};")
            file.writelines(f"{gamelog.to};")
            file.writelines(f"{gamelog.pm};")
            file.writelines(f"{gamelog.pts}" + '\n')
        file.close()