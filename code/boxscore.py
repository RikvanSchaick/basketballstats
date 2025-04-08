from gamelog import gamelog
from team import team
from terminoligy import team_terms
from copy import deepcopy

class boxscore():
    def __init__(self) -> None:
        self.team = None
        self.starters = None
        self.bench = None
        self.onfloor = None
        self.gamelogs = None
        self.sec = 0
        self.fg = 0
        self.fga = 0
        self.tp = 0
        self.tpa = 0
        self.ft = 0
        self.fta = 0
        self.oreb = 0
        self.dreb = 0
        self.reb = 0
        self.tmreb = 0
        self.ast = 0
        self.pf = 0
        self.stl = 0
        self.blk = 0
        self.to = 0
        self.tmto = 0
        self.pir = 0
        self.pm = 0
        self.pts = 0
        self.fgpct = 0
        self.tppct = 0
        self.ftpct = 0

    def create_boxscore(self, team:team) -> None:
        self.team = team
        self.starters = []
        self.bench = []
        for player in self.team.lineup.players:
            if player[1]:
                self.starters.append(player[0])
            else:
                self.bench.append(player[0])
        self.gamelogs = dict()
        
        for player in self.starters:
            self.gamelogs[str(player)] = gamelog(player, self.team, True)
        for player in self.bench:
            self.gamelogs[str(player)] = gamelog(player, self.team, False)
            
    def add_gamelogs(self, events:list, quarters:list) -> None:
        previous_team = None
        b = False
        for event in events:
            if event.quarter in quarters:
                if event.actionID in {"2","3","1","t"}:
                        previous_team = deepcopy(event.team)

                if event.team == self.team.team:
                    if event.actionID in {"j", "to"}:
                        pass
                    elif event.actionID == "ft" and event.playerID == None:
                        pass
                    elif event.actionID == "r" and event.playerID == None:
                        self.tmreb += 1
                    elif event.actionID == "t" and event.playerID == None:
                        self.tmto += 1
                    elif event.actionID == "out":
                        self.gamelogs[event.playerID].sub(event.actionID, event.quarter, event.time, event.lead)
                        if not event.actionID2 == None:
                            self.gamelogs[event.playerID2].sub(event.actionID2, event.quarter, event.time, event.lead)
                    else:
                        b = event.team == previous_team
                        self.gamelogs[event.playerID].add(event.actionID, b)
                        if event.actionID2 == 'a':
                            self.gamelogs[event.playerID2].add(event.actionID2, b)
                        # BLOCKED:
                        # if event.actionID2 == 'b':
                        #     self.gamelogs[event.playerID].add("blkd", b)
                    
                if not event.team == self.team.team:
                    if event.actionID2 in {"s","b"}:
                        self.gamelogs[event.playerID2].add(event.actionID2, b)
                    # FOULS DRAWN:
                    # if event.actionID in {"f0", "f1", "f2", "f3", "fu", "fd"}:
                    #     self.gamelogs[event.playerID2].add("pfd", b)
                    if event.actionID == "start":
                        for player in self.team.starters[int(event.quarter)-1]:
                            self.gamelogs[player].sub(event.actionID, event.quarter, event.time, event.lead)
                            self.gamelogs[player]
                    if event.actionID == "end":
                        for player in self.team.lineup.players:
                            self.gamelogs[player[0]].sub(event.actionID, event.quarter, event.time, event.lead)
            
    def make_boxscore(self, events:list, quarters:list) -> None:
        for gamelog in self.gamelogs.values():
            gamelog.minutes(quarters)
            gamelog.plusminus(quarters)
            self.sec += int(gamelog.sec or 0)
            self.fg += int(gamelog.fg or 0)
            self.fga += int(gamelog.fga or 0)
            self.tp += int(gamelog.tp or 0)
            self.tpa += int(gamelog.tpa or 0)    
            self.ft += int(gamelog.ft or 0)
            self.fta += int(gamelog.fta or 0)
            self.oreb += int(gamelog.oreb or 0)
            self.dreb += int(gamelog.dreb or 0)
            self.reb += int(gamelog.reb or 0)
            self.ast += int(gamelog.ast or 0)
            self.pf += int(gamelog.pf or 0)
            self.stl += int(gamelog.stl or 0)
            self.blk += int(gamelog.blk or 0)
            self.to += int(gamelog.to or 0)
            self.pm += int(gamelog.pm or 0)
            self.pts += int(gamelog.pts or 0)
        
        self.pm = int(self.pm/5)
        if self.fga > 0: self.fgpct = self.fg*100/self.fga
        if self.tpa > 0: self.tppct = self.tp*100/self.tpa
        if self.fta > 0: self.ftpct = self.ft*100/self.fta
        
    def print_boxscore(self, events:list, quarters:list) -> None:
        self.add_gamelogs(events, quarters)
        self.make_boxscore(events, quarters)
        print()
        print(f"{team_terms[self.team.team]}: {self.team.name}")
        print("\t".expandtabs(3) + "\t".expandtabs(32) + "MIN\t\tFG\tFGA\t3P\t3PA\tFT\tFTA\tOR\tDR\tTOT\tAST\tPF\tSTL\tBLK\tTO\t+/-\tPTS".expandtabs(5))
        starters = True
        for gamelog in self.gamelogs.values():
            if not gamelog.player in self.starters:
                if starters: print()
                starters = False
            player_name = gamelog.team.lineup.names[gamelog.player]
            print(f"{gamelog.player}\t".expandtabs(3) + f"{player_name}\t".expandtabs(32) + f"{gamelog.sec//60:02d}:{gamelog.sec%60:02d}\t{int(gamelog.fg or 0)}\t{int(gamelog.fga or 0)}\t{int(gamelog.tp or 0)}\t{int(gamelog.tpa or 0)}\t{int(gamelog.ft or 0)}\t{int(gamelog.fta or 0)}\t{int(gamelog.oreb or 0)}\t{int(gamelog.dreb or 0)}\t{int(gamelog.reb or 0)}\t{int(gamelog.ast or 0)}\t{int(gamelog.pf or 0)}\t{int(gamelog.stl or 0)}\t{int(gamelog.blk or 0)}\t{int(gamelog.to or 0)}\t{int(gamelog.pm or 0)}\t{int(gamelog.pts or 0)}".expandtabs(5))
        print("\t".expandtabs(3) + "\t".expandtabs(32) + f"{self.sec//60:02d}:{self.sec%60:02d}\t{self.fg}\t{self.fga}\t{self.tp}\t{self.tpa}\t{self.ft}\t{self.fta}\t{self.oreb}\t{self.dreb}\t{self.reb}\t{self.ast}\t{self.pf}\t{self.stl}\t{self.blk}\t{self.to}\t{self.pm}\t{self.pts}".expandtabs(5))
        print("\t".expandtabs(3) + "\t".expandtabs(32) + f"\t\t {(self.fgpct):.1f}%\t {(self.tppct):.1f}%\t {(self.ftpct):.1f}%\t TM REB: {self.tmreb}".expandtabs(5))
        
    def check_boxscore(self, team:team, events:list, quarters:list) -> None:
        try:
            self.create_boxscore(team)
            self.add_gamelogs(events, quarters)
            self.make_boxscore(events, quarters)
            return True
        except Exception as e: 
            return e