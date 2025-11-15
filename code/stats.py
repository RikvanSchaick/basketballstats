import pandas as pd
from formulas import EFGpct, TSpct, ASTtoTO
from datetime import datetime

pd.options.mode.chained_assignment = None

class stats:
    def __init__(self) -> None:
        self.team = None
        self.matchDataFrame = None
        self.playerDataFrame = None
        self.playbyplayDataFrame = None
        self.begin = None
        self.end = None
        self.team = None
        self.player = None
        self.teamMatchData = None
        self.oppMatchData = None
        self.teamPlayerData = None
        self.teamCounts = None
        self.playerCounts = None
    
    def load(self) -> None:
        self.matchDataFrame = pd.read_csv('data/match_data_dump.csv')
        self.playerDataFrame = pd.read_csv('data/player_data_dump.csv')
        self.playbyplayDataFrame = pd.read_csv('data/playbyplay_data_dump.csv')        
        self.matchDataFrame['dateTime'] = pd.to_datetime(self.matchDataFrame['dateTime'], format='%Y-%m-%d %H:%M:%S')

    def select_period(self, begin:datetime, end:datetime) -> None:
        if begin:
            start_date = begin
        else:
            print("Select begin of time period")
            self.begin = input("from: ")        
            if self.begin == "": 
                start_date = datetime(2000, 1, 1)
            elif len(self.begin) == 4:
                start_date = datetime(int(self.begin), 1, 1)
            elif len(self.begin) == 10:
                start_date = datetime.strptime(self.begin, '%d-%m-%Y')

        if end:
            end_date = end
        else:
            self.end = input("until: ")
            if self.end == "": 
                end_date = datetime(3000, 12, 31)
            elif len(self.end) == 4:
                end_date = datetime(int(self.end), 12, 31)
            elif len(self.end) == 10:
                end_date = datetime.strptime(self.end, '%d-%m-%Y')
            
        self.matchDataFrame = self.matchDataFrame[(self.matchDataFrame['dateTime'] > start_date) & (self.matchDataFrame['dateTime'] < end_date)]
    
    def select_team_or_player(self) -> bool:
        return int(input("want to select team (0) or player (1)? "))

    def select_team(self, team:str=None) -> str:
        if not isinstance(self.matchDataFrame, pd.DataFrame): return

        if team != None:
            self.team = team
        else:
            DF1 = self.matchDataFrame['homeTeam']
            DF1.columns = ['Team']
            DF2 = self.matchDataFrame['awayTeam']
            DF2.columns = ['Team']
            self.teamCounts = pd.concat([DF1, DF2]).value_counts().rename_axis('Team').reset_index(name='Number of matches')
            print(self.teamCounts.head(15))
            self.team = self.teamCounts['Team'].iloc[int(input("select team by index: "))]
            print()
        return self.team
        
    def select_player(self) -> None:
        if not isinstance(self.playerDataFrame, pd.DataFrame): return
        
        self.playerCounts = self.playerDataFrame['name'].value_counts().rename_axis('Player').reset_index(name='Number of matches')
        print(self.playerCounts.head(10))
        self.player = self.playerCounts['Player'].iloc[int(input("select player by index: "))]
        print()
        
    def teamData(self) -> None:
        if not isinstance(self.team, str): return
        if not isinstance(self.matchDataFrame, pd.DataFrame): return
        
        DF1 = self.matchDataFrame.loc[self.matchDataFrame['homeTeam'] == self.team, ['gameId', 'pointsDiff', 'homeScore', 'quarter1home', 'quarter2home', 'quarter3home', 'quarter4home', 'quarter5home', 'homeFieldGoalsMade', 'homeFieldGoalsAttempted', 'homeThreePointersMade', 'homeThreePointersAttempted', 'homeFreeThrowsMade', 'homeFreeThrowsAttempted', 'homeOffRebounds', 'homeDefRebounds', 'homeTeamRebounds', 'homeRebounds', 'homeAssists', 'homePersonalFouls', 'homeSteals', 'homeBlocks', 'homeTurnovers', 'homeLargestLead', 'homeSecondChancePoints', 'homeTeamTurnovers', 'homePointsOfTurnovers']]
        DF1.columns = ['gameId', 'pointsDiff', 'Score', 'Quarter1', 'Quarter2', 'Quarter3', 'Quarter4', 'Quarter5', 'FieldGoalsMade', 'FieldGoalsAttempted', 'ThreePointersMade', 'ThreePointersAttempted', 'FreeThrowsMade', 'FreeThrowsAttempted', 'OffRebounds', 'DefRebounds', 'TeamRebounds', 'Rebounds', 'Assists', 'PersonalFouls', 'Steals', 'Blocks', 'Turnovers', 'LargestLead', 'SecondChancePoints', 'TeamTurnovers', 'PointsOfTurnovers']
        DF1.insert(1, 'home_away', "home")
        DF2 = self.matchDataFrame.loc[self.matchDataFrame['awayTeam'] == self.team, ['gameId', 'pointsDiff', 'awayScore', 'quarter1away', 'quarter2away', 'quarter3away', 'quarter4away', 'quarter5away', 'awayFieldGoalsMade', 'awayFieldGoalsAttempted', 'awayThreePointersMade', 'awayThreePointersAttempted', 'awayFreeThrowsMade', 'awayFreeThrowsAttempted', 'awayOffRebounds', 'awayDefRebounds', 'awayTeamRebounds', 'awayRebounds', 'awayAssists', 'awayPersonalFouls', 'awaySteals', 'awayBlocks', 'awayTurnovers', 'awayLargestLead', 'awaySecondChancePoints', 'awayTeamTurnovers', 'awayPointsOfTurnovers']]
        DF2['pointsDiff'] = DF2['pointsDiff'].apply(lambda x: x*-1)
        DF2.columns = ['gameId', 'pointsDiff', 'Score', 'Quarter1', 'Quarter2', 'Quarter3', 'Quarter4', 'Quarter5', 'FieldGoalsMade', 'FieldGoalsAttempted', 'ThreePointersMade', 'ThreePointersAttempted', 'FreeThrowsMade', 'FreeThrowsAttempted', 'OffRebounds', 'DefRebounds', 'TeamRebounds', 'Rebounds', 'Assists', 'PersonalFouls', 'Steals', 'Blocks', 'Turnovers', 'LargestLead', 'SecondChancePoints', 'TeamTurnovers', 'PointsOfTurnovers']
        DF2.insert(1, 'home_away', "away")
        self.teamMatchData = pd.concat([DF1, DF2])   

    def oppData(self) -> None:
        if not isinstance(self.team, str): return
        if not isinstance(self.matchDataFrame, pd.DataFrame): return
        
        DF1 = self.matchDataFrame.loc[self.matchDataFrame['homeTeam'] == self.team, ['gameId', 'pointsDiff', 'awayScore', 'quarter1away', 'quarter2away', 'quarter3away', 'quarter4away', 'quarter5away', 'awayFieldGoalsMade', 'awayFieldGoalsAttempted', 'awayThreePointersMade', 'awayThreePointersAttempted', 'awayFreeThrowsMade', 'awayFreeThrowsAttempted', 'awayOffRebounds', 'awayDefRebounds', 'awayTeamRebounds', 'awayRebounds', 'awayAssists', 'awayPersonalFouls', 'awaySteals', 'awayBlocks', 'awayTurnovers', 'awayLargestLead', 'awaySecondChancePoints', 'awayTeamTurnovers', 'awayPointsOfTurnovers']]
        DF1['pointsDiff'] = DF1['pointsDiff'].apply(lambda x: x*-1)
        DF1.columns = ['gameId', 'pointsDiff', 'Score', 'Quarter1', 'Quarter2', 'Quarter3', 'Quarter4', 'Quarter5', 'FieldGoalsMade', 'FieldGoalsAttempted', 'ThreePointersMade', 'ThreePointersAttempted', 'FreeThrowsMade', 'FreeThrowsAttempted', 'OffRebounds', 'DefRebounds', 'TeamRebounds', 'Rebounds', 'Assists', 'PersonalFouls', 'Steals', 'Blocks', 'Turnovers', 'LargestLead', 'SecondChancePoints', 'TeamTurnovers', 'PointsOfTurnovers']
        DF1.insert(1, 'home_away', "away")
        DF2 = self.matchDataFrame.loc[self.matchDataFrame['awayTeam'] == self.team, ['gameId', 'pointsDiff', 'homeScore', 'quarter1home', 'quarter2home', 'quarter3home', 'quarter4home', 'quarter5home', 'homeFieldGoalsMade', 'homeFieldGoalsAttempted', 'homeThreePointersMade', 'homeThreePointersAttempted', 'homeFreeThrowsMade', 'homeFreeThrowsAttempted', 'homeOffRebounds', 'homeDefRebounds', 'homeTeamRebounds', 'homeRebounds', 'homeAssists', 'homePersonalFouls', 'homeSteals', 'homeBlocks', 'homeTurnovers', 'homeLargestLead', 'homeSecondChancePoints', 'homeTeamTurnovers', 'homePointsOfTurnovers']]
        DF2.columns = ['gameId', 'pointsDiff', 'Score', 'Quarter1', 'Quarter2', 'Quarter3', 'Quarter4', 'Quarter5', 'FieldGoalsMade', 'FieldGoalsAttempted', 'ThreePointersMade', 'ThreePointersAttempted', 'FreeThrowsMade', 'FreeThrowsAttempted', 'OffRebounds', 'DefRebounds', 'TeamRebounds', 'Rebounds', 'Assists', 'PersonalFouls', 'Steals', 'Blocks', 'Turnovers', 'LargestLead', 'SecondChancePoints', 'TeamTurnovers', 'PointsOfTurnovers']
        DF2.insert(1, 'home_away', "home")
        self.oppMatchData = pd.concat([DF1, DF2])
    
    def playerData(self) -> None:
        if not isinstance(self.team, str): return
        if not isinstance(self.teamMatchData, pd.DataFrame): return
        if not isinstance(self.playerDataFrame, pd.DataFrame): return
        
        self.teamPlayerData = self.playerDataFrame[(self.playerDataFrame['team'] == self.team) & (self.playerDataFrame['gameId'].isin(list(self.teamMatchData['gameId'].unique())))]        
        self.teamPlayerData = self.teamPlayerData[self.teamPlayerData['seconds'] != 0]
        self.teamPlayerData = self.teamPlayerData.drop(['Unnamed: 0'], axis=1)
        self.teamPlayerData['minutes'] = (self.teamPlayerData['seconds'] / 60).apply(lambda x: int(x))
        self.teamPlayerData['twoPointersMade'] = (self.teamPlayerData['fieldGoalsMade']-self.teamPlayerData['threePointersMade'])
        self.teamPlayerData['twoPointersAttempted'] = (self.teamPlayerData['fieldGoalsAttempted']-self.teamPlayerData['threePointersAttempted'])
        self.playerCounts = self.teamPlayerData['name'].value_counts().rename_axis('Player').reset_index(name='Number of matches')

    def team_stats(self) -> pd.DataFrame:
        self.teamData()
        if not isinstance(self.teamMatchData, pd.DataFrame): return
                
        DF1 = self.teamMatchData.drop(['gameId', 'home_away'], axis=1).sum(skipna=True).astype(int)
        DF2 = self.teamMatchData.drop(['gameId', 'home_away'], axis=1).mean(skipna=True).apply(lambda x: round(x, 2))
        
        self.oppData()
        if not isinstance(self.oppMatchData, pd.DataFrame): return
        
        DF3 = self.oppMatchData.drop(['gameId', 'home_away'], axis=1).sum(skipna=True).astype(int)
        DF4 = self.oppMatchData.drop(['gameId', 'home_away'], axis=1).mean(skipna=True).apply(lambda x: round(x, 2))
        DF5 = pd.concat([DF1, DF2, DF3, DF4], axis=1)
        DF5.columns = ['Team', 'Team/G', 'Opponent', 'Opponent/G']
        return DF5
    
    def per_game(self) -> pd.DataFrame:
        self.playerData()
        if not isinstance(self.teamPlayerData, pd.DataFrame): return
        
        DF1 = self.teamPlayerData.drop(['gameId', 'number', 'team'], axis=1)
        DF2 = DF1.groupby('name', as_index=False).mean().apply(lambda x: round(x, 2))        
        DF2['FG%'] = (DF2['fieldGoalsMade']/DF2['fieldGoalsAttempted']).apply(lambda x: round(x, 2))
        DF2['3P%'] = (DF2['threePointersMade']/DF2['threePointersAttempted']).apply(lambda x: round(x, 2))
        DF2['2P%'] = (DF2['twoPointersMade']/DF2['twoPointersAttempted']).apply(lambda x: round(x, 2))
        DF2['FT%'] = (DF2['freeThrowsMade']/DF2['freeThrowsAttempted']).apply(lambda x: round(x, 2))
        DF3 = DF1.groupby('name', as_index=False).size()
        DF4 = pd.merge(DF2, DF3, on='name')
        DF5 = DF1.groupby('name')['starter'].sum()
        DF6 = pd.merge(DF4, DF5, on='name')   
        DF7 = DF6[['name', 'size', 'starter_y', 'minutes', 'points', 'fieldGoalsMade', 'fieldGoalsAttempted', 'FG%', 'threePointersMade', 'threePointersAttempted', '3P%', 'twoPointersMade', 'twoPointersAttempted', '2P%', 'freeThrowsMade', 'freeThrowsAttempted', 'FT%', 'offRebounds', 'defRebounds', 'rebounds', 'assists', 'steals', 'blocks', 'turnovers', 'personalFouls']]
        DF7.columns = ['Player', 'G', 'GS', 'MP', 'PTS', 'FG', 'FGA', 'FG%', '3P', '3PA', '3P%', '2P', '2PA', '2P%', 'FT', 'FTA', 'FT%', 'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF']
        DF8 = DF7.sort_values(by=['MP'], ascending=False).reset_index(drop=True)
        return DF8
    
    def totals(self) -> pd.DataFrame:
        self.playerData()
        if not isinstance(self.teamPlayerData, pd.DataFrame): return
        
        DF1 = self.teamPlayerData.drop(['gameId', 'number', 'team'], axis=1)
        DF2 = DF1.groupby('name', as_index=False).sum()
        DF3 = DF1.groupby('name', as_index=False).size()
        DF4 = pd.merge(DF2, DF3, on='name')
        DF5 = DF1.groupby('name')['starter'].sum()
        DF6 = pd.merge(DF4, DF5, on='name')   
        DF7 = DF6[['name', 'size', 'starter_y', 'minutes', 'points', 'fieldGoalsMade', 'fieldGoalsAttempted', 'threePointersMade', 'threePointersAttempted', 'twoPointersMade', 'twoPointersAttempted', 'freeThrowsMade', 'freeThrowsAttempted', 'offRebounds', 'defRebounds', 'rebounds', 'assists', 'steals', 'blocks', 'turnovers', 'personalFouls']]
        DF7.columns = ['Player', 'G', 'GS', 'MP', 'PTS', 'FG', 'FGA', '3P', '3PA', '2P', '2PA', 'FT', 'FTA', 'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF']
        DF8 = DF7.sort_values(by=['MP'], ascending=False).reset_index(drop=True)
        return DF8

    def advanced(self) -> pd.DataFrame:
        self.playerData()
        if not isinstance(self.teamPlayerData, pd.DataFrame): return
        
        DF1 = self.teamPlayerData.drop(['gameId', 'number', 'team'], axis=1)
        DF2 = DF1.groupby('name', as_index=False).sum()
        DF3 = DF1.groupby('name', as_index=False).size()
        DF4 = pd.merge(DF2, DF3, on='name')
        DF5 = DF1.groupby('name')['starter'].sum()
        DF6 = pd.merge(DF4, DF5, on='name')
        DF6['EFG%'] = (EFGpct(DF6['fieldGoalsMade'], DF6['threePointersMade'], DF6['fieldGoalsAttempted'])).apply(lambda x: round(x, 2))
        DF6['TS%'] = (TSpct(DF6['points'], DF6['fieldGoalsAttempted'], DF6['freeThrowsAttempted'])).apply(lambda x: round(x, 2))
        DF6['AST/TO'] = (ASTtoTO(DF6['assists'], DF6['turnovers'])).apply(lambda x: round(x, 2))
        DF7 = DF6[['name', 'size', 'starter_y', 'minutes', 'EFG%', 'TS%', 'AST/TO', 'plusMinus']]
        DF7.columns = ['Player', 'G', 'GS', 'MP', 'EFG%', 'TS%', 'AST/TO', '+/-']
        DF8 = DF7.sort_values(by=['MP'], ascending=False).reset_index(drop=True)
        return DF8

    def player_logs(self, player, season = None) -> None:
        if season == None:
            DF1 = self.teamPlayerData[(self.teamPlayerData['name'] == player)]
        else:
            DF1 = self.teamPlayerData[(self.teamPlayerData['name'] == player) & (self.teamPlayerData['season'] == season)]
        DF2 = DF1[['gameId', 'name', 'points', 'fieldGoalsMade', 'fieldGoalsAttempted', 'ThreePointersMade', 'ThreePointersAttempted', 'freeThrowsMade', 'freeThrowsAttempted', 'offRebounds', 'defRebounds', 'rebounds', 'assists', 'steals', 'blocks', 'turnovers', 'personalFouls']]

        print(f"PLAYER LOGS: ({player})")
        print(DF2)
        print()