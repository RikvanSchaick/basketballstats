from stats import stats
from fpdf import FPDF
from datetime import datetime
import pandas as pd

class statsreport():
    def __init__(self) -> None:
        self.titlesize = 11
        self.bigtextsize = 10
        self.textsize = 9
        self.smalltextsize = 8
        self.page = False
        self.team = None

    def select_team(self) -> None:
        if not isinstance(self.matchDataFrame, pd.DataFrame): return

        DF1 = self.matchDataFrame['homeTeam']
        DF1.columns = ['Team']
        DF2 = self.matchDataFrame['awayTeam']
        DF2.columns = ['Team']
        self.teamCounts = pd.concat([DF1, DF2]).value_counts().rename_axis('Team').reset_index(name='Number of matches')
        print(self.teamCounts.head(15))
        self.team = self.teamCounts['Team'].iloc[int(input("select team by index: "))]
        print()
                
    def date_interval(self) -> None:
        oldest_date = self.matchDataFrame['dateTime'].min()
        newest_date = self.matchDataFrame['dateTime'].max()
        return oldest_date, newest_date
        
    def create_pdf(self) -> None:
        self.pdf = FPDF()
        self.pdf.set_margin(4)
  
    def footer(self):
        if self.page:
            self.pdf.set_font("Helvetica", size = self.smalltextsize)
            self.pdf.set_y(-20)
            self.pdf.cell(0, 10, str(self.pdf.page_no()),align='C')
            self.pdf.set_font("Helvetica", size = 6)
            self.pdf.set_y(-14)
            self.pdf.cell(0, 10, f"Copyright © {datetime.now().year} by Rik van Schaick",align='C')

    def new_page(self, pagetitle:str = None, subtitle:str = None) -> None:
        self.footer()
        self.pdf.add_page()
        self.page = True
        self.pdf.set_font("Helvetica", style="b", size = self.titlesize)
        with self.pdf.table(align="L",
                            borders_layout="NONE",
                            line_height=4,
                            col_widths=(1,1), 
                            text_align=("LEFT", "RIGHT")
        ) as table:                        
            row = table.row()
            row.cell("STATISTICS REPORT")
            row.cell(pagetitle)
            row = table.row()
            row.cell("")
            row.cell(subtitle)
            
        # self.pdf.set_font("Helvetica", style="b", size = self.textsize)
        # self.pdf.cell(w = 0, h = 4, txt = f"#{self.match.matchID}", ln = 1, align = 'L')
        # self.pdf.cell(w = 0, h = 4, txt = f"{self.match.home.name} against {self.match.away.name}", ln = 1, align = 'L')
        # d = datetime.strptime(self.match.date, '%d-%m-%Y')
        # d = date.strftime(d, "%d %B %Y")
        # self.pdf.cell(w = 0, h = 4, txt = f"{d}, {self.match.time}, {self.match.location}", ln = 1, align = 'L')
        # self.pdf.write(text='\n')
            
    def print_term(self, table:object, term:str, meaning:str, description:str, formula:str = None) -> None:
        self.pdf.set_font("Helvetica", style="b", size = self.bigtextsize)
        row = table.row()
        row.cell(term, colspan=2)
        self.pdf.set_font("Helvetica", style="b", size = self.smalltextsize)
        row = table.row()
        row.cell("Name")
        row.cell(meaning)
        row = table.row()
        row.cell("Description")
        row.cell(description)
        row = table.row()
        row.cell("", colspan=2)
        
    def pdf_glossary(self) -> None:
        self.footer()
        self.pdf.add_page()
        self.pdf.set_font("Helvetica", style="b", size = self.titlesize)
        self.pdf.cell(w = 0, h = 4, txt = f"GLOSSARY", ln = 1, align = 'L')
        self.pdf.write(text='\n')

        self.pdf.set_font("Helvetica", style="b", size = self.smalltextsize)        
        with self.pdf.table(align="L",
                            borders_layout="NONE",
                            line_height=3,
                            col_widths=(10, 90), 
                            text_align=("LEFT", "LEFT")
        ) as table:
            self.print_term(table, "2PTS", "Second Chance Points", "Any points scored by the offense (player or team) during a possession after an offensive player has already attempted one shot and missed.", None)
            self.print_term(table, "3P", "Three Pointers Made", "The number of 3 point field goals that a player or team has made.", None)
            self.print_term(table, "3PA", "Three Pointers Attempted", "The number of 3 point field goals that a player or team has attempted.", None)
            self.print_term(table, "+/-", "Plus-Minus", "The point differential when a player or team is on the floor.", None)
            self.print_term(table, "AST", "Assists", "The number of assists -- passes that lead directly to a made basket -- by a player.", None)
            self.print_term(table, "A/TO", "Assist to Turnover Ratio", "The number of assists for a player or team compared to the number of turnovers they have committed.", None)
            self.print_term(table, "BLK", "Blocked Shots", "A block occurs when an offensive player attempts a shot, and the defense player tips the ball, blocking their chance to score.", None)
            self.print_term(table, "DIF", "Points Differential", "The difference between a team's total points scored and points allowed.", None)
            self.print_term(table, "DRB", "Defensive Rebounds", "The number of rebounds a player or team has collected while they were on defense.", None)
            self.print_term(table, "EF%", "Effective Field Goal Percentage", "Measures field goal percentage adjusting for made 3-point field goals being 1.5 times more valuable than made 2-point field goals.", "((FGM + (0.5 * 3PM)) / FGA")
            self.print_term(table, "FG", "Field Goals Made", "The number of field goals that a player or team has made. This includes both 2 pointers and 3 pointers.", None)
            self.print_term(table, "FGA", "Field Goals Attempted", "The number of field goals that a player or team has attempted. This includes both 2 pointers and 3 pointers", None)
            self.print_term(table, "FT", "Free Throws Made", "The number of free throws that a player or team has made.", None)
            self.print_term(table, "FTA", "Free Throws Attempted", "The number of free throws that a player or team has attempted.", None)
            self.print_term(table, "G", "Games Played", "The number of games a player has played.", None)
            self.print_term(table, "GS", "Games Started", "The number of games a player has started.", None)
            self.print_term(table, "LEA", "Largest Lead", "The largest point differential of a team over its opponent in a game.", None)
            self.print_term(table, "MP", "Minutes Played", "The number of minutes played by a player or team.", None)
            self.print_term(table, "ORB", "Offensive Rebounds", "The number of rebounds a player or team has collected while they were on offense.", None)
            self.print_term(table, "OT", "Points Scored in Overtime", "The number of points a team has scored during overtime.", None)
            self.print_term(table, "PF", "Personal Fouls", "The number of personal fouls a player or team committed.", None)
            self.print_term(table, "PTO", "Points from Turnovers", "The number of points scored by a player or team following an opponent's turnover.", None)
            
        self.footer()
        self.pdf.add_page()
        self.pdf.set_font("Helvetica", style="b", size = self.titlesize)
        self.pdf.cell(w = 0, h = 4, txt = f"GLOSSARY", ln = 1, align = 'L')
        self.pdf.write(text='\n')

        self.pdf.set_font("Helvetica", style="b", size = self.smalltextsize)        
        with self.pdf.table(align="L",
                            borders_layout="NONE",
                            line_height=3,
                            col_widths=(10, 90), 
                            text_align=("LEFT", "LEFT")
        ) as table:            
            self.print_term(table, "PTS", "Points Scored", "The number of points scored by a player or team.", None)
            self.print_term(table, "Q1", "Points Scored in 1st Quarter", "The number of points a team has scored during the first quarter.", None)
            self.print_term(table, "Q2", "Points Scored in 2nd Quarter", "The number of points a team has scored during the second quarter.", None)
            self.print_term(table, "Q3", "Points Scored in 3rd Quarter", "The number of points a team has scored during the third quarter.", None)
            self.print_term(table, "Q4", "Points Scored in 4th Quarter", "The number of points a team has scored during the fourth quarter.", None)
            self.print_term(table, "STL", "Steals", "Number of times a defensive player or team takes the ball from a player on offense, causing a turnover.", None)
            self.print_term(table, "TMRB", "Team Rebounds", "In situations where the whistle stops play before there is player possession following a shot attempt a team rebound is credited.", None)
            self.print_term(table, "TMTO", "Team Turnovers", "A turnover by the team on offense, that loses the ball to the defense, where not a single player is responsible for the loss of possession.", None)
            self.print_term(table, "TOV", "Turnovers", "A turnover occurs when the player or team on offense loses the ball to the defense.", None)
            self.print_term(table, "TRB", "Total Rebounds", "A rebound occurs when a player recovers the ball after a missed shot. This statistic is the number of total rebounds a player or team has collected on either offense or defense.", None)
            self.print_term(table, "TS%", "True Shooting Percentage", "A shooting percentage that factors in the value of three-point field goals and free throws in addition to conventional two-point field goals.", "PTS/[2*(FGA+0.44*FTA)]")
       
    def pdf_export(self) -> None:
        self.footer()
        self.pdf.output(f"data/stats.pdf")

    def seasons_range(self, mindate:datetime, maxdate:datetime) -> {int, int}:
        firstseason = mindate.year-1 if mindate.month < 8 else mindate.year
        lastseason = maxdate.year if maxdate.month >= 8 else maxdate.year-1
        return firstseason, lastseason

    def stats_page(self, stats:stats) -> None:
        teamstats = stats.team_stats()
        self.pdf.set_font("Helvetica", style="b", size = 7)
        self.pdf.cell(w = 0, h = 4, txt = f"Team and Opponent Statistics", ln = 1, align = 'L')     
        self.pdf.set_font("Helvetica", style="b", size = 5)        
        data = [['', 'DIF', 'PTS', 'Q1', 'Q2', 'Q3', 'Q4', 'OT', 'FG', 'FGA', '3P', '3PA', 'FT', 'FTA', 'ORB', 'DRB', 'TRB', 'TMRB', 'AST', 'PF', 'STL', 'BLK', 'TOV', 'LEA', '2PTS', 'TMTO', 'PTO']]
        
        for idx, row in teamstats.T.iterrows():
            decimal = (idx in ['Team', 'Opponent']) 
            data.append([
            idx,
            f"{row['pointsDiff']:.0f}" if decimal else f"{row['pointsDiff']:.2f}",
            f"{row['Score']:.0f}" if decimal else f"{row['Score']:.2f}",
            f"{row['Quarter1']:.0f}" if decimal else f"{row['Quarter1']:.2f}",
            f"{row['Quarter2']:.0f}" if decimal else f"{row['Quarter2']:.2f}",
            f"{row['Quarter3']:.0f}" if decimal else f"{row['Quarter3']:.2f}",
            f"{row['Quarter4']:.0f}" if decimal else f"{row['Quarter4']:.2f}",
            f"{row['Quarter5']:.0f}" if decimal else f"{row['Quarter5']:.2f}",
            f"{row['FieldGoalsMade']:.0f}" if decimal else f"{row['FieldGoalsMade']:.2f}",
            f"{row['FieldGoalsAttempted']:.0f}" if decimal else f"{row['FieldGoalsAttempted']:.2f}",
            f"{row['ThreePointersMade']:.0f}" if decimal else f"{row['ThreePointersMade']:.2f}",
            f"{row['ThreePointersAttempted']:.0f}" if decimal else f"{row['ThreePointersAttempted']:.2f}",
            f"{row['FreeThrowsMade']:.0f}" if decimal else f"{row['FreeThrowsMade']:.2f}",
            f"{row['FreeThrowsAttempted']:.0f}" if decimal else f"{row['FreeThrowsAttempted']:.2f}",
            f"{row['OffRebounds']:.0f}" if decimal else f"{row['OffRebounds']:.2f}",
            f"{row['DefRebounds']:.0f}" if decimal else f"{row['DefRebounds']:.2f}",
            f"{row['Rebounds']:.0f}" if decimal else f"{row['Rebounds']:.2f}",
            f"{row['TeamRebounds']:.0f}" if decimal else f"{row['TeamRebounds']:.2f}",
            f"{row['Assists']:.0f}" if decimal else f"{row['Assists']:.2f}",
            f"{row['PersonalFouls']:.0f}" if decimal else f"{row['PersonalFouls']:.2f}",
            f"{row['Steals']:.0f}" if decimal else f"{row['Steals']:.2f}",
            f"{row['Blocks']:.0f}" if decimal else f"{row['Blocks']:.2f}",
            f"{row['Turnovers']:.0f}" if decimal else f"{row['Turnovers']:.2f}",
            f"{row['LargestLead']:.0f}" if decimal else f"{row['LargestLead']:.2f}",
            f"{row['SecondChancePoints']:.0f}" if decimal else f"{row['SecondChancePoints']:.2f}",
            f"{row['TeamTurnovers']:.0f}" if decimal else f"{row['TeamTurnovers']:.2f}",
            f"{row['PointsOfTurnovers']:.0f}" if decimal else f"{row['PointsOfTurnovers']:.2f}",
            ])
        self.pdf.set_line_width(0.15)
        with self.pdf.table(align="L",
                    borders_layout="SINGLE_TOP_LINE",
                    line_height=3,
                    col_widths=(6, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3), 
                    text_align=("Left", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER")
        ) as table:
            for data_row in data:
                row = table.row()
                for datum in data_row:
                    row.cell(datum)

        self.pdf.write(text='\n')        
        pergame = stats.per_game()
        self.pdf.set_font("Helvetica", style="b", size = 7)
        self.pdf.cell(w = 0, h = 4, txt = f"Player Statistics per Game", ln = 1, align = 'L')     
        self.pdf.set_font("Helvetica", style="b", size = 5.5)        
        data = [['Player', 'G', 'GS', 'MP', 'PTS', 'FG', 'FGA', 'FG%', '3P', '3PA', '3P%', '2P', '2PA', '2P%', 'FT', 'FTA', 'FT%', 'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF']]
        for idx, row in pergame.iterrows():
            data.append([
            str(row['Player']),
            str(int(row['G'])) if pd.notna(row['G']) else "",
            str(int(row['GS'])) if pd.notna(row['GS']) else "",
            f"{row['MP']:.2f}" if pd.notna(row['MP']) else "",
            f"{row['PTS']:.2f}" if pd.notna(row['PTS']) else "",
            f"{row['FG']:.2f}" if pd.notna(row['FG']) else "",
            f"{row['FGA']:.2f}" if pd.notna(row['FGA']) else "",
            f"{row['FG%']:.2f}" if pd.notna(row['FG%']) else "",
            f"{row['3P']:.2f}" if pd.notna(row['3P']) else "",
            f"{row['3PA']:.2f}" if pd.notna(row['3PA']) else "",
            f"{row['3P%']:.2f}" if pd.notna(row['3P%']) else "",
            f"{row['2P']:.2f}" if pd.notna(row['2P']) else "",
            f"{row['2PA']:.2f}" if pd.notna(row['2PA']) else "",
            f"{row['2P%']:.2f}" if pd.notna(row['2P%']) else "",
            f"{row['FT']:.2f}" if pd.notna(row['FT']) else "",
            f"{row['FTA']:.2f}" if pd.notna(row['FTA']) else "",
            f"{row['FT%']:.2f}" if pd.notna(row['FT%']) else "",
            f"{row['ORB']:.2f}" if pd.notna(row['ORB']) else "",
            f"{row['DRB']:.2f}" if pd.notna(row['DRB']) else "",
            f"{row['TRB']:.2f}" if pd.notna(row['TRB']) else "",
            f"{row['AST']:.2f}" if pd.notna(row['AST']) else "",
            f"{row['STL']:.2f}" if pd.notna(row['STL']) else "",
            f"{row['BLK']:.2f}" if pd.notna(row['BLK']) else "",
            f"{row['TOV']:.2f}" if pd.notna(row['TOV']) else "",
            f"{row['PF']:.2f}" if pd.notna(row['PF']) else ""
            ])
        self.pdf.set_line_width(0.15)
        with self.pdf.table(align="L",
                    borders_layout="SINGLE_TOP_LINE",
                    line_height=3,
                    col_widths=(12, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3), 
                    text_align=("LEFT", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER")
        ) as table:
            for data_row in data:
                row = table.row()
                for datum in data_row:
                    row.cell(datum)
        
        self.pdf.write(text='\n')
        totals = stats.totals()
        advanced = stats.advanced()
        self.pdf.set_font("Helvetica", style="b", size = 7)
        self.pdf.cell(w = 0, h = 4, txt = f"Total + Advanced Player Statistics", ln = 1, align = 'L')
        self.pdf.set_font("Helvetica", style="b", size = 5.5)
        data = [['Player', 'G', 'GS', 'MP', 'PTS', 'FG', 'FGA', '3P', '3PA', '2P', '2PA', 'FT', 'FTA', 'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'EF%', 'TS%', 'A/TO', '+/-']]
        for idx, row in totals.iterrows():
            data.append([
            str(row['Player']),
            str(int(row['G'])) if pd.notna(row['G']) else "",
            str(int(row['GS'])) if pd.notna(row['GS']) else "",
            f"{row['MP']}" if pd.notna(row['MP']) else "",
            f"{row['PTS']}" if pd.notna(row['PTS']) else "",
            f"{row['FG']}" if pd.notna(row['FG']) else "",
            f"{row['FGA']}" if pd.notna(row['FGA']) else "",
            f"{row['3P']}" if pd.notna(row['3P']) else "",
            f"{row['3PA']}" if pd.notna(row['3PA']) else "",
            f"{row['2P']}" if pd.notna(row['2P']) else "",
            f"{row['2PA']}" if pd.notna(row['2PA']) else "",
            f"{row['FT']}" if pd.notna(row['FT']) else "",
            f"{row['FTA']}" if pd.notna(row['FTA']) else "",
            f"{row['ORB']}" if pd.notna(row['ORB']) else "",
            f"{row['DRB']}" if pd.notna(row['DRB']) else "",
            f"{row['TRB']}" if pd.notna(row['TRB']) else "",
            f"{row['AST']}" if pd.notna(row['AST']) else "",
            f"{row['STL']}" if pd.notna(row['STL']) else "",
            f"{row['BLK']}" if pd.notna(row['BLK']) else "",
            f"{row['TOV']}" if pd.notna(row['TOV']) else "",
            f"{row['PF']}" if pd.notna(row['PF']) else "",
            f"{(advanced.loc[idx, 'EFG%'])/100:.2f}" if pd.notna(advanced.loc[idx, 'EFG%']) else "",
            f"{(advanced.loc[idx, 'TS%'])/100:.2f}" if pd.notna(advanced.loc[idx, 'TS%']) else "",
            f"{advanced.loc[idx, 'AST/TO']:.2f}" if pd.notna(advanced.loc[idx, 'AST/TO']) else "",
            f"{advanced.loc[idx, '+/-']}" if pd.notna(advanced.loc[idx, '+/-']) else ""
            ])
        self.pdf.set_line_width(0.15)
        with self.pdf.table(align="L",
                    borders_layout="SINGLE_TOP_LINE",
                    line_height=3,
                    col_widths=(12, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3), 
                    text_align=("LEFT", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER")
        ) as table:
            for data_row in data:
                row = table.row()
                for datum in data_row:
                    row.cell(datum)        

    def make_pdf(self) -> None:
        total = stats() 
        total.load()
        self.team = total.select_team()
        mask = (total.matchDataFrame['homeTeam'] == self.team) | (total.matchDataFrame['awayTeam'] == self.team)        
        firstseason, lastseason = self.seasons_range(total.matchDataFrame.loc[mask, 'dateTime'].min(), total.matchDataFrame.loc[mask, 'dateTime'].max())
        
        self.create_pdf()
        self.new_page(self.team, "ALL TIME")
        self.pdf.set_font("Helvetica", style="b", size = self.smalltextsize)

        self.stats_page(stats=total)
        for year in range(firstseason, lastseason + 1):
            season = f"SEASON {year}-{year + 1}"
            self.new_page(self.team, season)
            seasonal = stats() 
            seasonal.load()
            seasonal.select_team(self.team)
            seasonal.select_period(begin=datetime(year, 8, 1), end=datetime(year + 1, 7, 31))
            self.stats_page(stats=seasonal)

        self.pdf_glossary()
        self.pdf_export()
