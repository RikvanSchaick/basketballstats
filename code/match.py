from event import event
from boxscore import boxscore
from team import team
from copy import deepcopy
from terminoligy import quarter_terms, team_terms, actions_terms

class match():
    def __init__(self) -> None:
        self.matchID = None
        self.home = None
        self.away = None
        self.date = None
        self.time = None
        self.location = None
        self.events = None
        self.score = None
        self.oncourt = None
        
    def create_match(self, ID:str, home:str, away:str, date:str, time:str, location:str, prnt:bool) -> None:
        self.matchID = ID
        self.home = team(home, "H")
        self.away = team(away, "A")
        self.date = date
        self.time = time
        self.location = location
        self.oncourt = {"quarter": [], "time": [], "score": [], "_home": [], "_away": []}
        
        if prnt: print(f"created match {self.matchID}\n{self.away.name} at {self.home.name}\n{self.date}, {self.time}, {self.location}")

    def add_teams(self, homeplayers:list, awayplayers:list) -> None:
        if len(homeplayers) < 6 or len(awayplayers) < 6: return False
        self.home.add_team(homeplayers)
        self.away.add_team(awayplayers)
        return True
    
    def start_match(self) -> None:
        self.score = [0,0]
        self.events = []
        
    def add_starters(self, quarter:int, homestarters:list, awaystarters:list) -> bool:
        if not (len(homestarters) == 5 and len(awaystarters) == 5): return False
        if quarter in {"1","2","3","4","5","6","7","8"}:
            self.home.add_starters(quarter, homestarters)
            self.away.add_starters(quarter, awaystarters)
            time = "1000" if quarter in {"1","2","3","4"} else "500"
            self.add_oncourt(time=time, quarter=quarter, score=deepcopy(self.score), home=homestarters, away=awaystarters)
            return True
        else:
            return False

    def add_oncourt(self, quarter:int, time:str, score:list, home:list, away:list) -> None:
        self.oncourt["quarter"].append(quarter)
        self.oncourt["time"].append(time)
        self.oncourt["score"].append(score)
        self.oncourt["_home"].append(home)
        self.oncourt["_away"].append(away)

    def print_oncourt(self) -> None:
        _home = deepcopy(self.oncourt["_home"][-1])
        _away = deepcopy(self.oncourt["_away"][-1])
        print("home: " + ", ".join(str(player) for player in sorted(_home, key=int)))
        print("away: " + ", ".join(str(player) for player in sorted(_away, key=int)))

    def update_oncourt(self, event:event) -> bool:
        if event.actionID == "to":
            self.print_oncourt()
        if event.actionID == "out":
            b = self.substition_check(event)
            if not b == True: return b
            _home = deepcopy(self.oncourt["_home"][-1])
            _away = deepcopy(self.oncourt["_away"][-1])
            if event.team == "H":
                _home.remove(event.playerID)
                _home.append(event.playerID2)
            elif event.team == "A":
                _away.remove(event.playerID)
                _away.append(event.playerID2)
            self.add_oncourt(quarter=event.quarter, time=event.time, score=deepcopy(self.score), home=_home, away=_away)
        elif event.actionID == "end":
            _home = deepcopy(self.oncourt["_home"][-1])
            _away = deepcopy(self.oncourt["_away"][-1])
            self.add_oncourt(quarter=event.quarter, time=event.time, score=deepcopy(self.score), home=_home, away=_away)
        return True
        
    def substition_check(self, event:event) -> bool | str:
        if not event.actionID == "out": return True
        if event.team == "H":
            if not event.playerID in self.oncourt["_home"][-1]: return f"{event.playerID} not on court"
            if event.playerID2 in self.oncourt["_home"][-1]: return f"{event.playerID2} already on court"
            if event.playerID2 not in self.home.players.names.keys(): return f"{event.playerID2} not on team"
        elif event.team == "A":
            if not event.playerID in self.oncourt["_away"][-1]: return f"{event.playerID} not on court"
            if event.playerID2 in self.oncourt["_away"][-1]: return f"{event.playerID2} already on court"
            if event.playerID2 not in self.away.players.names.keys(): return f"{event.playerID2} not on team"
        return True
        
    def update_score(self, event:event) -> None:
        if event.actionID in {"2m","3m","1m"}:
            points = int(event.actionID[0])
            if event.team == "H":
                self.score[0] += points
            elif event.team == "A":
                self.score[1] += points
        event.score = deepcopy(self.score)
        event.lead = self.score[0] - self.score[1]
        
    def print_score(self) -> None:
        return f"{self.score[0]}-{self.score[1]}"
    
    def add_event(self, event:event) -> bool:
        self.update_score(event)
        self.events.append(event)
        return self.update_oncourt(event)
        
    def get_eventstring(self, i:int) -> str:
        return self.events[i].eventstring()
        
    def last_quarter(self) -> int:
        last_quarter = 0
        for event in self.events:
            if int(event.quarter) > last_quarter: last_quarter = deepcopy(int(event.quarter))
        return last_quarter
        
    def all_quarters(self) -> list:
        all_quarters = []
        for event in self.events:
            if not event.quarter in all_quarters: all_quarters.append(deepcopy(event.quarter))
        return all_quarters
    
    def count_events(self, quarter:int) -> int:
        count = 0
        for event in self.events:
            if event.quarter == quarter:
                count += 1
        return count
        
    def quarter_score(self, quarter:int) -> int:
        for event in self.events:
            if event.actionID == "start" and event.quarter == quarter:
                start_score = deepcopy(event.score)
            if event.actionID == "end" and event.quarter == quarter:
                end_score = deepcopy(event.score)
        return (end_score[0]-start_score[0]), (end_score[1]-start_score[1]) 

    def score_by_period(self, quarters:list) -> {list,list,list}:
        quartersprint = []
        totalpointshome = []
        totalpointsaway = []
        for quarter in quarters:
            homepoints, awaypoints = self.quarter_score(quarter)
            quartersprint.append(f"Q{quarter}")
            totalpointshome.append(homepoints)
            totalpointsaway.append(awaypoints)
        quartersprint.append("FINAL")
        totalpointshome.append(sum(totalpointshome))
        totalpointsaway.append(sum(totalpointsaway))
        return quartersprint, totalpointshome, totalpointsaway
            
    def second_chance_points(self, quarters:list) -> list:
        second_chance_points = [0, 0]
        previous_team = None
        last_shot = False
        oreb = [False, None]
        for event in self.events:
            if event.quarter in quarters:
                if event.actionID in {"2","3","1"}:
                    previous_team = deepcopy(event.team)
                if event.actionID == "r" and event.team == previous_team:
                    oreb = [True, deepcopy(event.team)]
                elif oreb[0] and event.team == oreb[1] and event.actionID in {"f0","f1","f2","f3","ft","fu","fd"}:
                    oreb = [False, None]
                elif oreb[0] and not event.team == oreb[1] and event.actionID in {"r","s","j","t","2","3","1","2m","3m","1m"}:
                    oreb = [False, None]
                elif event.actionID == "end":
                    oreb = [False, None]
                if last_shot and not event.actionID in {"1m","f1"}:
                    last_shot = False
                    oreb = [False, None]
                elif oreb[0] and event.team == oreb[1] and event.actionID in {"2m","3m","1m"}:
                    if event.team == "H": second_chance_points[0] += int(event.actionID[0])
                    if event.team == "A": second_chance_points[1] += int(event.actionID[0])
                    last_shot = True
        return second_chance_points

    def points_off_turnovers(self, quarters:list) -> list:
        points_off_turnovers = [0, 0]
        last_shot = False
        to = [False, None]
        for event in self.events:
            if event.quarter in quarters:
                if event.actionID == "t":
                    last_shot = False
                    to = [True, deepcopy(event.team)]
                elif last_shot and not event.actionID in {"1m","f1"}:
                    last_shot = False
                    to = [False, None]
                elif to[0] and not event.team == to[1] and event.actionID in {"2m","3m","1m"}:
                    if event.team == "H": points_off_turnovers[0] += int(event.actionID[0])
                    if event.team == "A": points_off_turnovers[1] += int(event.actionID[0])
                    last_shot = True
                elif to[0] and not event.actionID in {"2m","3m","s","to","out","in","f2","f3","fu","fd"}:
                    to = [False, None]
        return points_off_turnovers
                    
    def largest_lead(self, quarters:list) -> {int,int}:
        llH = 0
        llA = 0
        for event in self.events:
            if event.quarter in quarters:
                if event.actionID in {"2m","3m","1m"}:
                    if event.lead > llH: llH = deepcopy(event.lead)
                    if event.lead < llA: llA = deepcopy(event.lead)
        return llH,-llA
    
    def lead_chances(self, quarters:list) -> int:
        lc = 0
        last_lead = None
        for event in self.events:
            if event.quarter in quarters:
                if event.actionID in {"2m","3m","1m"}:
                    if event.lead > 0 and last_lead == "A": lc += 1
                    if event.lead < 0 and last_lead == "H": lc += 1
                if event.lead > 0: last_lead = "H"
                if event.lead < 0: last_lead = "A"    
        return lc
    
    def ties(self, quarters:list) -> int:
        ties = 0
        for event in self.events:
            if event.quarter in quarters:
                if event.actionID in {"2m","3m","1m"}:
                    if event.lead == 0: ties += 1
        return ties
    
    def team_turnovers(self, quarters:list) -> int:
        team_turnovers = [0, 0]
        for event in self.events:
            if event.quarter in quarters:
                if event.actionID == "t" and event.playerID == None:
                    if event.team == "H": team_turnovers[0] += 1
                    if event.team == "A": team_turnovers[1] += 1
        return team_turnovers
        
    def print_summary(self, quarters:list) -> None:
        quartersprint, totalpointshome, totalpointsaway = self.score_by_period(quarters)
        quartersprint.insert(0, "\t".expandtabs(4))
        totalpointshome.insert(0, "HOME".expandtabs(3))
        totalpointsaway.insert(0, "AWAY".expandtabs(3))

        print()
        print(*quartersprint, sep='\t'.expandtabs(4))
        print(*totalpointshome, sep='\t'.expandtabs(4))
        print(*totalpointsaway, sep='\t'.expandtabs(4))
        print()
        
        llH, llA = self.largest_lead(quarters)
        print(f"BIGGEST LEAD HOME:\t {llH}".expandtabs(26))
        print(f"BIGGEST LEAD AWAY:\t {llA}".expandtabs(26))

        lc = self.lead_chances(quarters)
        print(f"LEAD CHANGES:\t {lc}".expandtabs(26))
        
        ties = self.ties(quarters)
        print(f"TIES:\t {ties}".expandtabs(26))
        
        scp_H, scp_A = self.second_chance_points(quarters)
        print(f"2ND CHANCE POINTS HOME:\t {scp_H}".expandtabs(26))
        print(f"2ND CHANCE POINTS AWAY:\t {scp_A}".expandtabs(26))

        tmto_H, tmto_A = self.team_turnovers(quarters)
        print(f"TEAM TURNOVERS HOME:\t {tmto_H}".expandtabs(26))
        print(f"TEAM TURNOVERS AWAY:\t {tmto_A}".expandtabs(26))

        pot_H, pot_A = self.points_off_turnovers(quarters)
        print(f"POINTS OF TURNOVERS HOME:\t {pot_H}".expandtabs(26))
        print(f"POINTS OF TURNOVERS AWAY:\t {pot_A}".expandtabs(26))
        
    def print_events(self, quarters:list) -> None:
        for event in self.events:
            if event.quarter in quarters:
                if event.actionID == "start":
                    print(f"START OF {quarter_terms[event.quarter]} ({event.print_score(False)})")
                    print(f"TIME\tSCORE\tLEAD\t{team_terms['H']}\t\t\t\t\t{team_terms['A']}")
                elif event.actionID == "end":
                    print(f"END OF {quarter_terms[event.quarter]} ({event.print_score(False)})\n")
                if event.team == "H":
                    if event.actionID in {"2m","3m","1m"}:
                        print(f"[{event.time[:2]}:{event.time[2:]}]\t{event.print_score(True)[0]}\t{event.print_score(True)[1]}\t{event.print_event(actions_terms)}")
                    elif event.actionID in {"2", "3", "t"} and not event.actionID2 == None:
                        print(f"[{event.time[:2]}:{event.time[2:]}]\t\t\t{event.print_event(actions_terms)[0]}\t\t\t\t{event.print_event(actions_terms)[1]}")
                    else:
                        print(f"[{event.time[:2]}:{event.time[2:]}]\t\t\t{event.print_event(actions_terms)}")
                if event.team == "A":
                    if event.actionID in {"2m","3m","1m"}:
                        print(f"[{event.time[:2]}:{event.time[2:]}]\t{event.print_score(True)[0]}\t{event.print_score(True)[1]}\t\t\t\t\t\t{event.print_event(actions_terms)}")
                    elif event.actionID in {"2", "3", "t"} and not event.actionID2 == None:
                        print(f"[{event.time[:2]}:{event.time[2:]}]\t\t\t{event.print_event(actions_terms)[1]}\t\t\t\t{event.print_event(actions_terms)[0]}")
                    else:
                        print(f"[{event.time[:2]}:{event.time[2:]}]\t\t\t\t\t\t\t\t{event.print_event(actions_terms)}")
        
    def print_boxscore(self, quarters:list) -> None:
        boxscore_home = boxscore()
        boxscore_home.create_boxscore(self.home)
        boxscore_home.print_boxscore(self.events, quarters)
        
        boxscore_away = boxscore()
        boxscore_away.create_boxscore(self.away)
        boxscore_away.print_boxscore(self.events, quarters)
        
    def check_boxscore(self, quarters:list) -> None:
        boxscore_home = boxscore()
        boxscore_away = boxscore()
        home_check = boxscore_home.check_boxscore(self.home, self.events, quarters)
        if home_check==True: 
            away_check = boxscore_away.check_boxscore(self.away, self.events, quarters)
            return True if away_check==True else print(f"ERROR: {away_check}")
        else:
            print(home_check)
