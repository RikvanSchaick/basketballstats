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
        self.matchDataFrame = pd.read_csv('data/match_data_dump.csv', index_col=0)
        self.playerDataFrame = pd.read_csv('data/player_data_dump.csv', index_col=0)
        self.playbyplayDataFrame = pd.read_csv('data/playbyplay_data_dump.csv', index_col=0)
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

    def selector(self, Counts:pd.DataFrame, Team:str=True) -> str:
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit import prompt
        bindings = KeyBindings()
        rowidx = 0
        col = "Team" if Team else "Player"
        default_text = f"{Counts[col].iloc[rowidx]} [{Counts['Number of matches'].iloc[rowidx]}]"
        
        @bindings.add('up')
        def _(event):
            nonlocal rowidx
            if rowidx > 0:
                rowidx -= 1
            default_text = f"{Counts[col].iloc[rowidx]} [{Counts['Number of matches'].iloc[rowidx]}]"
            event.app.current_buffer.text = default_text
            event.app.current_buffer.cursor_position = len(default_text)
        
        @bindings.add('down')
        def _(event):
            nonlocal rowidx
            if rowidx < 30 and rowidx < len(Counts)-1:
                rowidx += 1
            default_text = f"{Counts[col].iloc[rowidx]} [{Counts['Number of matches'].iloc[rowidx]}]"
            event.app.current_buffer.text = default_text
            event.app.current_buffer.cursor_position = len(default_text)
        
        team = prompt(default=default_text, key_bindings=bindings)
        team = team.split(" [", 1)[0].strip()
        return team
    
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
            self.team = self.selector(Counts=self.teamCounts, Team=True)
        return self.team
        
    def select_player(self, player:str=None) -> str:
        if not isinstance(self.playerDataFrame, pd.DataFrame): return

        if player != None:
            self.player = player
            return self.player

        while True:
            player_name = input("select player by name: ")
            nameDataFrame = self.playerDataFrame[self.playerDataFrame['name'].str.contains(player_name, case=False, na=False)]        
            self.playerCounts = nameDataFrame['name'].value_counts().rename_axis('Player').reset_index(name='Number of matches')
            if len(self.playerCounts) == 0:
                print("No players found.")
                continue
            elif len(self.playerCounts) == 1:
                self.player = self.playerCounts['Player'].iloc[0]
                print(f"selected {self.player}")
                break
            else:
                self.player = self.selector(Counts=self.playerCounts, Team=False)
                break
            
        self.team = list(self.playerDataFrame[self.playerDataFrame['name'] == self.player]['team'].unique())
        return self.player, self.team

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
        
    def careerhighs(self) -> dict:
        if not isinstance(self.player, str): return
        if not isinstance(self.matchDataFrame, pd.DataFrame): return
        DF1 = self.playerDataFrame[self.playerDataFrame['name'] == self.player]
        pts_max = DF1['points'].max()
        reb_max = DF1['rebounds'].max()
        ast_max = DF1['assists'].max()
        stl_max = DF1['steals'].max()
        blk_max = DF1['blocks'].max()
        return {"pts": pts_max, "reb": reb_max, "ast": ast_max, "stl": stl_max, "blk": blk_max}
    
    def player_career_averages(self) -> pd.DataFrame:
        if not isinstance(self.player, str): return pd.DataFrame()
        if not isinstance(self.matchDataFrame, pd.DataFrame): return pd.DataFrame()
        DF1 = self.playerDataFrame[self.playerDataFrame['name'] == self.player]
        DF2 = DF1.merge(self.matchDataFrame[['gameId', 'dateTime']], on='gameId', how='left')
        DF2['season'] = DF2['dateTime'].apply(lambda x: f"{x.year}-{str(x.year+1)[-2:]}" if x.month >= 8 else f"{x.year-1}-{str(x.year)[-2:]}")
        DF3 = DF2.drop(['gameId', 'starter', 'name', 'number', 'team', 'dateTime'], axis=1)
        DF4 = DF3.groupby('season', as_index=False).mean().apply(lambda x: round(x, 1))
        DF4['twoPointersMade'] = (DF4['fieldGoalsMade']-DF4['threePointersMade'])
        DF4['twoPointersAttempted'] = (DF4['fieldGoalsAttempted']-DF4['threePointersAttempted'])
        DF4['minutes'] = (DF4['seconds'] / 60).apply(lambda x: round(x, 3))
        DF4['FG%'] = (DF4['fieldGoalsMade']/DF4['fieldGoalsAttempted']).apply(lambda x: round(x, 3))
        DF4['3P%'] = (DF4['threePointersMade']/DF4['threePointersAttempted']).apply(lambda x: round(x, 3))
        DF4['2P%'] = (DF4['twoPointersMade']/DF4['twoPointersAttempted']).apply(lambda x: round(x, 3))
        DF4['FT%'] = (DF4['freeThrowsMade']/DF4['freeThrowsAttempted']).apply(lambda x: round(x, 3))
        DF5 = DF2.groupby('season', as_index=False).size()
        DF6 = pd.merge(DF4, DF5, on='season')
        DF7 = DF2.groupby('season')['starter'].sum()
        DF8 = pd.merge(DF6, DF7, on='season')
        DF9 = DF8[['season', 'size', 'starter', 'minutes', 'points', 'fieldGoalsMade', 'fieldGoalsAttempted', 'FG%', 'threePointersMade', 'threePointersAttempted', '3P%', 'twoPointersMade', 'twoPointersAttempted', '2P%', 'freeThrowsMade', 'freeThrowsAttempted', 'FT%', 'offRebounds', 'defRebounds', 'rebounds', 'assists', 'steals', 'blocks', 'turnovers', 'personalFouls']]
        DF9.columns = ['Season', 'G', 'GS', 'MP', 'PTS', 'FG', 'FGA', 'FG%', '3P', '3PA', '3P%', '2P', '2PA', '2P%', 'FT', 'FTA', 'FT%', 'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF']
        
        DF10 = DF3.drop(['season'], axis=1, errors='ignore').mean(skipna=True)    
        DF10['Season'] = f"{int(DF2['season'].nunique())} seasons"
        DF10['twoPointersMade'] = DF10['fieldGoalsMade'] - DF10['threePointersMade']
        DF10['twoPointersAttempted'] = DF10['fieldGoalsAttempted'] - DF10['threePointersAttempted']
        DF10['minutes'] = round(DF10['seconds'] / 60, 3)
        DF10['FG%'] = round(DF10['fieldGoalsMade'] / DF10['fieldGoalsAttempted'], 3)
        DF10['3P%'] = round(DF10['threePointersMade'] / DF10['threePointersAttempted'], 3)
        DF10['2P%'] = round(DF10['twoPointersMade'] / DF10['twoPointersAttempted'], 3)
        DF10['FT%'] = round(DF10['freeThrowsMade'] / DF10['freeThrowsAttempted'], 3)
        DF10['G'] = len(DF2['gameId'].unique())
        DF10['GS'] = DF2['starter'].sum()
        DF10 = DF10[['Season', 'G', 'GS', 'minutes', 'points', 'fieldGoalsMade', 'fieldGoalsAttempted', 'FG%', 'threePointersMade', 'threePointersAttempted', '3P%', 'twoPointersMade', 'twoPointersAttempted', '2P%', 'freeThrowsMade', 'freeThrowsAttempted', 'FT%', 'offRebounds', 'defRebounds', 'rebounds', 'assists', 'steals', 'blocks', 'turnovers', 'personalFouls']]
        DF11 = pd.DataFrame([DF10.values], columns=DF10.index)
        DF11.columns = ['Season', 'G', 'GS', 'MP', 'PTS', 'FG', 'FGA', 'FG%', '3P', '3PA', '3P%', '2P', '2PA', '2P%', 'FT', 'FTA', 'FT%', 'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF']
        DF12 = pd.concat([DF9, DF11], ignore_index=True)
        return DF12
    
    def player_career_totals(self) -> pd.DataFrame:
        if not isinstance(self.player, str): return pd.DataFrame()
        if not isinstance(self.matchDataFrame, pd.DataFrame): return pd.DataFrame()
        DF1 = self.playerDataFrame[self.playerDataFrame['name'] == self.player]
        DF2 = DF1.merge(self.matchDataFrame[['gameId', 'dateTime']], on='gameId', how='left')
        DF2['season'] = DF2['dateTime'].apply(lambda x: f"{x.year}-{str(x.year+1)[-2:]}" if x.month >= 8 else f"{x.year-1}-{str(x.year)[-2:]}")
        DF3 = DF2.drop(['gameId', 'starter', 'name', 'number', 'team', 'dateTime'], axis=1)
        DF4 = DF3.groupby('season', as_index=False).sum().apply(lambda x: round(x, 0))
        DF4['twoPointersMade'] = (DF4['fieldGoalsMade']-DF4['threePointersMade'])
        DF4['twoPointersAttempted'] = (DF4['fieldGoalsAttempted']-DF4['threePointersAttempted'])
        DF4['minutes'] = (DF4['seconds'] / 60).apply(lambda x: round(x, 0))
        DF4['FG%'] = (DF4['fieldGoalsMade']/DF4['fieldGoalsAttempted']).apply(lambda x: round(x, 3))
        DF4['3P%'] = (DF4['threePointersMade']/DF4['threePointersAttempted']).apply(lambda x: round(x, 3))
        DF4['2P%'] = (DF4['twoPointersMade']/DF4['twoPointersAttempted']).apply(lambda x: round(x, 3))
        DF4['FT%'] = (DF4['freeThrowsMade']/DF4['freeThrowsAttempted']).apply(lambda x: round(x, 3))
        DF5 = DF2.groupby('season', as_index=False).size()
        DF6 = pd.merge(DF4, DF5, on='season')
        DF7 = DF2.groupby('season')['starter'].sum()
        DF8 = pd.merge(DF6, DF7, on='season')
        DF9 = DF8[['season', 'size', 'starter', 'minutes', 'points', 'fieldGoalsMade', 'fieldGoalsAttempted', 'FG%', 'threePointersMade', 'threePointersAttempted', '3P%', 'twoPointersMade', 'twoPointersAttempted', '2P%', 'freeThrowsMade', 'freeThrowsAttempted', 'FT%', 'offRebounds', 'defRebounds', 'rebounds', 'assists', 'steals', 'blocks', 'turnovers', 'personalFouls']]
        DF9.columns = ['Season', 'G', 'GS', 'MP', 'PTS', 'FG', 'FGA', 'FG%', '3P', '3PA', '3P%', '2P', '2PA', '2P%', 'FT', 'FTA', 'FT%', 'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF']
        
        DF10 = DF3.drop(['season'], axis=1, errors='ignore').sum(skipna=True)    
        DF10['Season'] = f"{int(DF2['season'].nunique())} seasons"
        DF10['twoPointersMade'] = DF10['fieldGoalsMade'] - DF10['threePointersMade']
        DF10['twoPointersAttempted'] = DF10['fieldGoalsAttempted'] - DF10['threePointersAttempted']
        DF10['minutes'] = round(DF10['seconds'] / 60, 0)
        DF10['FG%'] = round(DF10['fieldGoalsMade'] / DF10['fieldGoalsAttempted'], 3)
        DF10['3P%'] = round(DF10['threePointersMade'] / DF10['threePointersAttempted'], 3)
        DF10['2P%'] = round(DF10['twoPointersMade'] / DF10['twoPointersAttempted'], 3)
        DF10['FT%'] = round(DF10['freeThrowsMade'] / DF10['freeThrowsAttempted'], 3)
        DF10['G'] = len(DF2['gameId'].unique())
        DF10['GS'] = DF2['starter'].sum()
        DF10 = DF10[['Season', 'G', 'GS', 'minutes', 'points', 'fieldGoalsMade', 'fieldGoalsAttempted', 'FG%', 'threePointersMade', 'threePointersAttempted', '3P%', 'twoPointersMade', 'twoPointersAttempted', '2P%', 'freeThrowsMade', 'freeThrowsAttempted', 'FT%', 'offRebounds', 'defRebounds', 'rebounds', 'assists', 'steals', 'blocks', 'turnovers', 'personalFouls']]
        DF11 = pd.DataFrame([DF10.values], columns=DF10.index)
        DF11.columns = ['Season', 'G', 'GS', 'MP', 'PTS', 'FG', 'FGA', 'FG%', '3P', '3PA', '3P%', '2P', '2PA', '2P%', 'FT', 'FTA', 'FT%', 'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF']
        DF12 = pd.concat([DF9, DF11], ignore_index=True)
        return DF12

    def check_playerData(self) -> bool:
        if not isinstance(self.player, str): return pd.DataFrame()
        if not isinstance(self.playerDataFrame, pd.DataFrame): return pd.DataFrame()
        DF1 = self.playerDataFrame[self.playerDataFrame['name'] == self.player]
        if len(DF1['gameId'][DF1['gameId'].isin(self.matchDataFrame['gameId'])]) == 0:
            return False        
        return True
    
    def gamelog_summary(self) -> pd.DataFrame:
        if not isinstance(self.player, str): return pd.DataFrame()
        if not isinstance(self.playerDataFrame, pd.DataFrame): return pd.DataFrame()
        DF1 = self.playerDataFrame[self.playerDataFrame['name'] == self.player]
        DF1 = DF1[DF1['gameId'].isin(self.matchDataFrame['gameId'])]
        DF1['minutes'] = round(DF1['seconds'] / 60, 1)
        
        MP_count = []
        for minute in [(0,10), (10,20), (20,30), (30,40), (40, 999)]:
            count = len(DF1[(DF1['minutes'] >= minute[0]) & (DF1['minutes'] < minute[1])])
            if count > 0: 
                if minute[1] == 999:
                    MP_count.append((f"{minute[0]}+", count))
                else:
                    MP_count.append((f"{minute[0]}-{minute[1]}", count))

        PTS_count = []
        for point in [(0,5), (5,10), (10,15), (15,20), (20, 999)]:
            count = len(DF1[(DF1['points'] >= point[0]) & (DF1['points'] < point[1])])
            if count > 0: 
                if point[1] == 999:
                    PTS_count.append((f"{point[0]}+", count))
                else:
                    PTS_count.append((f"{point[0]}-{point[1]-1}", count))        

        REB_count = []
        for rebound in [(0,3), (3,6), (6,10), (10,14), (14, 999)]:
            count = len(DF1[(DF1['rebounds'] >= rebound[0]) & (DF1['rebounds'] < rebound[1])])
            if count > 0: 
                if rebound[1] == 999:
                    REB_count.append((f"{rebound[0]}+", count))
                else:
                    REB_count.append((f"{rebound[0]}-{rebound[1]-1}", count))

        AST_count = []
        for assist in [(0,3), (3,6), (6,10), (10,14), (14, 999)]:
            count = len(DF1[(DF1['assists'] >= assist[0]) & (DF1['assists'] < assist[1])])
            if count > 0: 
                if assist[1] == 999:
                    AST_count.append((f"{assist[0]}+", count))
                else:
                    AST_count.append((f"{assist[0]}-{assist[1]-1}", count))
        
        STL_count = []
        for steal in [(0,1), (1,3), (3,5), (5,7), (7, 999)]:
            count = len(DF1[(DF1['steals'] >= steal[0]) & (DF1['steals'] < steal[1])])
            if count > 0: 
                if steal[1] == 999:
                    STL_count.append((f"{steal[0]}+", count))
                elif steal[0] == 0:
                    STL_count.append((f"{steal[0]}", count))
                else:
                    STL_count.append((f"{steal[0]}-{steal[1]-1}", count))
        
        BLK_count = []
        for block in [(0,1), (1,3), (3,5), (5,7), (7, 999)]:
            count = len(DF1[(DF1['blocks'] >= block[0]) & (DF1['blocks'] < block[1])])
            if count > 0: 
                if block[1] == 999:
                    BLK_count.append((f"{block[0]}+", count))
                elif block[0] == 0:
                    BLK_count.append((f"{block[0]}", count))
                else:
                    BLK_count.append((f"{block[0]}-{block[1]-1}", count))

        TOV_count = []
        for turnover in [(0,1), (1,3), (3,5), (5,7), (7, 999)]:
            count = len(DF1[(DF1['turnovers'] >= turnover[0]) & (DF1['turnovers'] < turnover[1])])
            if count > 0: 
                if turnover[1] == 999:
                    TOV_count.append((f"{turnover[0]}+", count))
                elif turnover[0] == 0:
                    TOV_count.append((f"{turnover[0]}", count))
                else:
                    TOV_count.append((f"{turnover[0]}-{turnover[1]-1}", count))
        
        PF_count = []
        for foul in [(0,1), (1,3), (3,5), (5, 999)]:
            count = len(DF1[(DF1['personalFouls'] >= foul[0]) & (DF1['personalFouls'] < foul[1])])
            if count > 0: 
                if foul[1] == 999:
                    PF_count.append((f"{foul[0]}+", count))
                elif foul[0] == 0:
                    PF_count.append((f"{foul[0]}", count))
                else:
                    PF_count.append((f"{foul[0]}-{foul[1]-1}", count))
        
        max_len = max(len(MP_count), len(PTS_count), len(REB_count), len(AST_count), len(STL_count), len(BLK_count), len(TOV_count), len(PF_count))
        for _ in range(max_len - len(MP_count)):
            MP_count.append(("", ""))
        for _ in range(max_len - len(PTS_count)):
            PTS_count.append(("", ""))
        for _ in range(max_len - len(REB_count)):
            REB_count.append(("", ""))
        for _ in range(max_len - len(AST_count)):
            AST_count.append(("", ""))
        for _ in range(max_len - len(STL_count)):
            STL_count.append(("", ""))
        for _ in range(max_len - len(BLK_count)):
            BLK_count.append(("", ""))
        for _ in range(max_len - len(TOV_count)):
            TOV_count.append(("", ""))
        for _ in range(max_len - len(PF_count)):
            PF_count.append(("", ""))
        
        return [MP_count, PTS_count, REB_count, AST_count, STL_count, BLK_count, TOV_count, PF_count]