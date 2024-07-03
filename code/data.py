from match import match
from event import event
from copy import deepcopy
from datetime import datetime
from boxscore import boxscore
from terminoligy import actions_code, actions_terms, quarter_code
import pandas as pd
import os

class data():
    def __init__(self) -> None:
        self.df_match = pd.DataFrame(columns=['gameId', 'dateTime', 'homeTeam', 'awayTeam', 'pointsDiff', 'pointsSum', 'quarters', 'status', 'homeScore', 'quarter1home', 'quarter2home', 'quarter3home', 'quarter4home', 'quarter5home', 'homeFieldGoalsMade', 'homeFieldGoalsAttempted', 'homeThreePointersMade', 'homeThreePointersAttempted', 'homeFreeThrowsMade', 'homeFreeThrowsAttempted', 'homeOffRebounds', 'homeDefRebounds', 'homeTeamRebounds', 'homeRebounds', 'homeAssists', 'homePersonalFouls', 'homeSteals', 'homeBlocks', 'homeTurnovers', 'homeLargestLead', 'homeSecondChancePoints', 'homePointsOfTurnovers', 'awayScore', 'quarter1away', 'quarter2away', 'quarter3away', 'quarter4away', 'quarter5away', 'awayFieldGoalsMade', 'awayFieldGoalsAttempted', 'awayThreePointersMade', 'awayThreePointersAttempted', 'awayFreeThrowsMade', 'awayFreeThrowsAttempted', 'awayOffRebounds', 'awayDefRebounds', 'awayTeamRebounds', 'awayRebounds', 'awayAssists', 'awayPersonalFouls', 'awaySteals', 'awayBlocks', 'awayTurnovers', 'awayLargestLead', 'awaySecondChancePoints', 'awayPointsOfTurnovers'])
        self.df_player = pd.DataFrame(columns=['gameId', 'name', 'number', 'team', 'starter', 'seconds', 'points', 'fieldGoalsMade', 'fieldGoalsAttempted', 'threePointersMade', 'threePointersAttempted', 'freeThrowsMade', 'freeThrowsAttempted', 'offRebounds', 'defRebounds', 'rebounds', 'assists', 'personalFouls', 'steals', 'blocks', 'turnovers', 'plusMinus'])
        self.df_playbyplay = pd.DataFrame(columns=['gameId', 'name', 'team', 'homeScore', 'awayScore', 'quarter', 'remainingMinutes', 'remainingSeconds', 'play', 'description'])
        self.matches = []
    
    def read(self) -> None:
        for filename in os.listdir("matches"):
            if filename.endswith(".txt") and not filename == "history.txt":
                f = open("matches/"+filename, "r")
                lines = f.read().splitlines()
                m = match()
                m.create_match(lines[0],
                                lines[1],
                                lines[2],
                                lines[3],
                                lines[4],
                                lines[5])
                homeplayers = lines[6]
                awayplayers = lines[7]
                m.add_lineups(homeplayers.split(";"), awayplayers.split(";"))
                
                m.start_match()
                added_events = 0
                n_events = len(lines)-8
                for n in range(8, 8+n_events):
                    eventstring = deepcopy(lines[n])
                    e = event()
                    b = e.extract_eventstring(eventstring)
                    if eventstring[:4] == "edit":
                        m.add_event(e)
                        added_events += 1
                        quarter = eventstring[4]
                    elif eventstring[0] == "H":
                        homestarters = eventstring[1:].split(",")
                        del e
                    elif eventstring[0] == "A":
                        awaystarters = eventstring[1:].split(",")
                        m.add_starters(quarter, homestarters, awaystarters)              
                        del e
                    elif b:
                        m.add_event(e)
                        added_events += 1
                    else:
                        del e
                
                print(f"selected match {m.matchID} with {n_events} written lines and {added_events} added events\n")
                self.matches.append(m)
        
        print(f"added a total of {len(self.matches)} matches\n")
                
    def boxscores(self, match):
        boxHome = boxscore()
        boxHome.create_boxscore(match.home)
        boxHome.add_gamelogs(match.events, match.all_quarters())
        boxHome.make_boxscore(match.events, match.all_quarters())
        
        boxAway = boxscore()
        boxAway.create_boxscore(match.away)
        boxAway.add_gamelogs(match.events, match.all_quarters())
        boxAway.make_boxscore(match.events, match.all_quarters())
        
        return boxHome, boxAway
            
    def add_match_data(self, match) -> None:
        match_data = []
        
        match_data.append(match.matchID)
        match_data.append(datetime.strptime(match.date + match.time, '%d-%m-%Y%H:%M'))
        match_data.append(match.home.name)
        match_data.append(match.away.name)
        match_data.append(match.score[0] - match.score[1])
        match_data.append(match.score[0] + match.score[1])
        match_data.append(len(match.all_quarters()))
        if all(ele in match.all_quarters() for ele in ['1', '2', '3', '4']):
            if '5' in match.all_quarters(): 
                match_data.append("F/OT")
            else: 
                match_data.append("Final")
        else:
            match_data.append("DNF")
        
        match_data.append(match.score[0])
        quarter1home = 0
        quarter2home = 0
        quarter3home = 0
        quarter4home = 0
        quarter5home = 0
        if '1' in match.all_quarters(): quarter1home += match.quarter_score('1')[0]
        if '2' in match.all_quarters(): quarter2home += match.quarter_score('2')[0]
        if '3' in match.all_quarters(): quarter3home += match.quarter_score('3')[0]
        if '4' in match.all_quarters(): quarter4home += match.quarter_score('4')[0]
        if '5' in match.all_quarters(): quarter5home += match.quarter_score('5')[0]
        if '6' in match.all_quarters(): quarter5home += match.quarter_score('6')[0]
        if '7' in match.all_quarters(): quarter5home += match.quarter_score('7')[0]
        if '8' in match.all_quarters(): quarter5home += match.quarter_score('8')[0]
        match_data.append(quarter1home)
        match_data.append(quarter2home)
        match_data.append(quarter3home)
        match_data.append(quarter4home)
        match_data.append(None) if quarter5home == 0 else match_data.append(quarter5home)
        
        boxHome, boxAway = self.boxscores(match)
        match_data.append(boxHome.fg)
        match_data.append(boxHome.fga)
        match_data.append(boxHome.tp)
        match_data.append(boxHome.tpa)
        match_data.append(boxHome.ft)
        match_data.append(boxHome.fta)
        
        match_data.append(boxHome.oreb)
        match_data.append(boxHome.dreb)
        match_data.append(boxHome.tmreb)
        match_data.append(boxHome.reb)
        match_data.append(boxHome.ast)
        match_data.append(boxHome.pf)
        match_data.append(boxHome.stl)
        match_data.append(boxHome.blk)
        match_data.append(boxHome.to)
        match_data.append(match.largest_lead(match.all_quarters())[0])
        match_data.append(match.second_chance_points(match.all_quarters())[0])
        match_data.append(match.points_off_turnovers(match.all_quarters())[0])

        match_data.append(match.score[1])
        quarter1away = 0
        quarter2away = 0
        quarter3away = 0
        quarter4away = 0
        quarter5away = 0
        if '1' in match.all_quarters(): quarter1away += match.quarter_score('1')[1]
        if '2' in match.all_quarters(): quarter2away += match.quarter_score('2')[1]
        if '3' in match.all_quarters(): quarter3away += match.quarter_score('3')[1]
        if '4' in match.all_quarters(): quarter4away += match.quarter_score('4')[1]
        if '5' in match.all_quarters(): quarter5away += match.quarter_score('5')[1]
        if '6' in match.all_quarters(): quarter5away += match.quarter_score('6')[1]
        if '7' in match.all_quarters(): quarter5away += match.quarter_score('7')[1]
        if '8' in match.all_quarters(): quarter5away += match.quarter_score('8')[1]
        match_data.append(quarter1away)
        match_data.append(quarter2away)
        match_data.append(quarter3away)
        match_data.append(quarter4away)
        match_data.append(None) if quarter5away == 0 else match_data.append(quarter5away)
        
        match_data.append(boxAway.fg)
        match_data.append(boxAway.fga)
        match_data.append(boxAway.tp)
        match_data.append(boxAway.tpa)
        match_data.append(boxAway.ft)
        match_data.append(boxAway.fta)
        
        match_data.append(boxAway.oreb)
        match_data.append(boxAway.dreb)
        match_data.append(boxAway.tmreb)
        match_data.append(boxAway.reb)
        match_data.append(boxAway.ast)
        match_data.append(boxAway.pf)
        match_data.append(boxAway.stl)
        match_data.append(boxAway.blk)
        match_data.append(boxAway.to)
        match_data.append(match.largest_lead(match.all_quarters())[1])
        match_data.append(match.second_chance_points(match.all_quarters())[1])
        match_data.append(match.points_off_turnovers(match.all_quarters())[1])

        self.df_match.loc[len(self.df_match.index)] = match_data
    
    def add_player_data(self, match) -> None:
        boxHome, boxAway = self.boxscores(match)
        for gamelog in boxHome.gamelogs.values():
            player_data = []
            player_data.append(match.matchID)
            player_data.append(gamelog.team.lineup.names[gamelog.player])
            player_data.append(gamelog.player)
            player_data.append(match.home.name)
            player_data.append(gamelog.starter)
            player_data.append(gamelog.sec)
            
            player_data.append(0) if gamelog.pts == None else player_data.append(gamelog.pts)
            player_data.append(0) if gamelog.fg == None else player_data.append(gamelog.fg)
            player_data.append(0) if gamelog.fga == None else player_data.append(gamelog.fga)
            player_data.append(0) if gamelog.tp == None else player_data.append(gamelog.tp)
            player_data.append(0) if gamelog.tpa == None else player_data.append(gamelog.tpa)
            player_data.append(0) if gamelog.ft == None else player_data.append(gamelog.ft)
            player_data.append(0) if gamelog.fta == None else player_data.append(gamelog.fta)
            player_data.append(0) if gamelog.oreb == None else player_data.append(gamelog.oreb)
            player_data.append(0) if gamelog.dreb == None else player_data.append(gamelog.dreb)
            player_data.append(0) if gamelog.reb == None else player_data.append(gamelog.reb)
            player_data.append(0) if gamelog.ast == None else player_data.append(gamelog.ast)
            player_data.append(0) if gamelog.pf == None else player_data.append(gamelog.pf)
            player_data.append(0) if gamelog.stl == None else player_data.append(gamelog.stl)
            player_data.append(0) if gamelog.blk == None else player_data.append(gamelog.blk)
            player_data.append(0) if gamelog.to == None else player_data.append(gamelog.to)
            player_data.append(0) if gamelog.pm == None else player_data.append(gamelog.pm)

            if not gamelog.sec == 0:
                self.df_player.loc[len(self.df_player.index)] = player_data
        
        for gamelog in boxAway.gamelogs.values():
            player_data = []
            player_data.append(match.matchID)
            player_data.append(gamelog.team.lineup.names[gamelog.player])
            player_data.append(gamelog.player)
            player_data.append(match.away.name)
            player_data.append(gamelog.starter)
            player_data.append(gamelog.sec)

            player_data.append(0) if gamelog.pts == None else player_data.append(gamelog.pts)
            player_data.append(0) if gamelog.fg == None else player_data.append(gamelog.fg)
            player_data.append(0) if gamelog.fga == None else player_data.append(gamelog.fga)
            player_data.append(0) if gamelog.tp == None else player_data.append(gamelog.tp)
            player_data.append(0) if gamelog.tpa == None else player_data.append(gamelog.tpa)
            player_data.append(0) if gamelog.ft == None else player_data.append(gamelog.ft)
            player_data.append(0) if gamelog.fta == None else player_data.append(gamelog.fta)
            player_data.append(0) if gamelog.oreb == None else player_data.append(gamelog.oreb)
            player_data.append(0) if gamelog.dreb == None else player_data.append(gamelog.dreb)
            player_data.append(0) if gamelog.reb == None else player_data.append(gamelog.reb)
            player_data.append(0) if gamelog.ast == None else player_data.append(gamelog.ast)
            player_data.append(0) if gamelog.pf == None else player_data.append(gamelog.pf)
            player_data.append(0) if gamelog.stl == None else player_data.append(gamelog.stl)
            player_data.append(0) if gamelog.blk == None else player_data.append(gamelog.blk)
            player_data.append(0) if gamelog.to == None else player_data.append(gamelog.to)
            player_data.append(0) if gamelog.pm == None else player_data.append(gamelog.pm)
            
            if not gamelog.sec == 0:
                self.df_player.loc[len(self.df_player.index)] = player_data
        
    def add_playbyplay_data(self, match) -> None:        
        for event in match.events:
            play = []
            play.append(match.matchID)
            play.append(event.playerID)
            if event.team == "H": 
                play.append(match.home.name)
            else:
                play.append(match.away.name)
            play.append(int(event.score[0]))
            play.append(int(event.score[1]))
            play.append(int(event.quarter))
            play.append(int(event.time[:2]))
            play.append(int(event.time[2:]))

            if event.actionID == "start":
                play.append("Period")
                play.append("Start of " + quarter_code[event.quarter])
            elif event.actionID == "end":
                play.append("Period")
                play.append("End of " + quarter_code[event.quarter])
            else:
                play.append(actions_code[event.actionID])
                if event.team == "H": 
                    if event.actionID == '1m':
                        play.append(f"{match.home.lineup.names[event.playerID]} makes free throw")
                    if event.actionID == '2m':
                        if not event.actionID2 == None:
                            play.append(f"{match.home.lineup.names[event.playerID]} makes two pointer assisted by {match.home.lineup.names[event.playerID2]}")
                        else:
                            play.append(f"{match.home.lineup.names[event.playerID]} makes two pointer")
                    if event.actionID == '3m':
                        if not event.actionID2 == None:
                            play.append(f"{match.home.lineup.names[event.playerID]} makes three pointer assisted by {match.home.lineup.names[event.playerID2]}")
                        else:
                            play.append(f"{match.home.lineup.names[event.playerID]} makes three pointer")
                    if event.actionID == '1':
                        play.append(f"{match.home.lineup.names[event.playerID]} misses free throw")
                    if event.actionID == '2':
                        if not event.actionID2 == None:
                            play.append(f"{match.home.lineup.names[event.playerID]} misses two pointer blocked by {match.away.lineup.names[event.playerID2]}")
                        else:
                            play.append(f"{match.home.lineup.names[event.playerID]} misses two pointer")
                    if event.actionID == '3':
                        if not event.actionID2 == None:
                            play.append(f"{match.home.lineup.names[event.playerID]} misses three pointer blocked by {match.away.lineup.names[event.playerID2]}")
                        else:
                            play.append(f"{match.home.lineup.names[event.playerID]} misses three pointer")
                    if event.actionID == 'f0':
                        play.append(f"Personal foul on {match.home.lineup.names[event.playerID]}")
                    if event.actionID == 'f1':
                        play.append(f"Shooting foul on {match.home.lineup.names[event.playerID]}") 
                    if event.actionID == 'f2':
                        play.append(f"Shooting foul on {match.home.lineup.names[event.playerID]}") 
                    if event.actionID == 'f3':
                        play.append(f"Shooting foul on {match.home.lineup.names[event.playerID]}") 
                    if event.actionID == 'ft':
                        if not event.playerID == None:
                            play.append(f"Technical foul on {match.home.lineup.names[event.playerID]}")
                        else:
                            play.append("Technical foul on coach or bench")
                    if event.actionID == 'fu':
                        play.append(f"Unsportsmanlike foul on {match.home.lineup.names[event.playerID]}")
                    if event.actionID == 'fd':
                        play.append(f"{match.home.lineup.names[event.playerID]} is disqualified")
                    if event.actionID == 'r':
                        if not event.playerID == None:
                            play.append(f"{match.home.lineup.names[event.playerID]} rebound")
                        else:
                            play.append("Team rebound")
                    if event.actionID == 't':
                        if not event.actionID2 == None:
                            play.append(f"Turnover on {match.home.lineup.names[event.playerID]} stolen by {match.away.lineup.names[event.playerID2]}")
                        else:
                            play.append(f"Turnover on {match.home.lineup.names[event.playerID]}")
                    if event.actionID == 'j':
                        play.append(f"Possession obtained by {match.home.name} after jumpball")
                    if event.actionID == 'to':
                        play.append("Timeout taken by team")
                    if event.actionID == 'out':
                        play.append(f"{match.home.lineup.names[event.playerID2]} enters game for {match.home.lineup.names[event.playerID]}")
                        
                if event.team == "A": 
                    if event.actionID == '1m':
                        play.append(f"{match.away.lineup.names[event.playerID]} makes free throw")
                    if event.actionID == '2m':
                        if not event.actionID2 == None:
                            play.append(f"{match.away.lineup.names[event.playerID]} makes two pointer assisted by {match.away.lineup.names[event.playerID2]}")
                        else:
                            play.append(f"{match.away.lineup.names[event.playerID]} makes two pointer")
                    if event.actionID == '3m':
                        if not event.actionID2 == None:
                            play.append(f"{match.away.lineup.names[event.playerID]} makes three pointer assisted by {match.away.lineup.names[event.playerID2]}")
                        else:
                            play.append(f"{match.away.lineup.names[event.playerID]} makes three pointer")
                    if event.actionID == '1':
                        play.append(f"{match.away.lineup.names[event.playerID]} misses free throw")
                    if event.actionID == '2':
                        if not event.actionID2 == None:
                            play.append(f"{match.away.lineup.names[event.playerID]} misses two pointer blocked by {match.home.lineup.names[event.playerID2]}")
                        else:
                            play.append(f"{match.away.lineup.names[event.playerID]} misses two pointer")
                    if event.actionID == '3':
                        if not event.actionID2 == None:
                            play.append(f"{match.away.lineup.names[event.playerID]} misses three pointer blocked by {match.home.lineup.names[event.playerID2]}")
                        else:
                            play.append(f"{match.away.lineup.names[event.playerID]} misses three pointer")
                    if event.actionID == 'f0':
                        play.append(f"Personal foul on {match.away.lineup.names[event.playerID]}")
                    if event.actionID == 'f1':
                        play.append(f"Shooting foul on {match.away.lineup.names[event.playerID]}") 
                    if event.actionID == 'f2':
                        play.append(f"Shooting foul on {match.away.lineup.names[event.playerID]}") 
                    if event.actionID == 'f3':
                        play.append(f"Shooting foul on {match.away.lineup.names[event.playerID]}") 
                    if event.actionID == 'ft':
                        if not event.playerID == None:
                            play.append(f"Technical foul on {match.away.lineup.names[event.playerID]}")
                        else:
                            play.append("Technical foul on coach or bench")
                    if event.actionID == 'fu':
                        play.append(f"Unsportsmanlike foul on {match.away.lineup.names[event.playerID]}")
                    if event.actionID == 'fd':
                        play.append(f"{match.away.lineup.names[event.playerID]} is disqualified")
                    if event.actionID == 'r':
                        if not event.playerID == None:
                            play.append(f"{match.away.lineup.names[event.playerID]} rebound")
                        else:
                            play.append("Team rebound")
                    if event.actionID == 't':
                        if not event.actionID2 == None:
                            play.append(f"Turnover on {match.away.lineup.names[event.playerID]} stolen by {match.home.lineup.names[event.playerID2]}")
                        else:
                            play.append(f"Turnover on {match.away.lineup.names[event.playerID]}")
                    if event.actionID == 'j':
                        play.append(f"Possession obtained by {match.away.name} after jumpball")
                    if event.actionID == 'to':
                        play.append("Timeout taken by team")
                    if event.actionID == 'out':
                        play.append(f"{match.away.lineup.names[event.playerID2]} enters game for {match.away.lineup.names[event.playerID]}")
                                  
            self.df_playbyplay.loc[len(self.df_playbyplay.index)] = play
        
    def add_data(self) -> None:
        for match in self.matches:
            self.add_match_data(match)
            self.add_player_data(match)
            self.add_playbyplay_data(match)
    
    def export(self) -> None:
        self.df_match.to_csv("data/match_data_dump.csv")
        self.df_player.to_csv("data/player_data_dump.csv")
        self.df_playbyplay.to_csv("data/playbyplay_data_dump.csv")