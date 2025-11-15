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
            self.print_term(table, "2nd PTS", "Second Chance Points", "Any points scored by the offense (player or team) during a possession after an offensive player has already attempted one shot and missed.", None)
            self.print_term(table, "3P", "Three Pointers Made", "The number of 3 point field goals that a player or team has made.", None)
            self.print_term(table, "3PA", "Three Pointers Attempted", "The number of 3 point field goals that a player or team has attempted.", None)
            self.print_term(table, "+/-", "Plus-Minus", "The point differential when a player or team is on the floor.", None)
            self.print_term(table, "A", "Assists", "The number of assists -- passes that lead directly to a made basket -- by a player.", None)
            self.print_term(table, "A/TO", "Assist to Turnover Ratio", "The number of assists for a player or team compared to the number of turnovers they have committed.", None)
            self.print_term(table, "BS", "Blocked Shots", "A block occurs when an offensive player attempts a shot, and the defense player tips the ball, blocking their chance to score.", None)
            self.print_term(table, "DR", "Defensive Rebounds", "The number of rebounds a player or team has collected while they were on defense.", None)
            self.print_term(table, "EF%", "Effective Field Goal Percentage", "Measures field goal percentage adjusting for made 3-point field goals being 1.5 times more valuable than made 2-point field goals.", "((FGM + (0.5 * 3PM)) / FGA")
            self.print_term(table, "FG", "Field Goals Made", "The number of field goals that a player or team has made. This includes both 2 pointers and 3 pointers.", None)
            self.print_term(table, "FGA", "Field Goals Attempted", "The number of field goals that a player or team has attempted. This includes both 2 pointers and 3 pointers", None)
            self.print_term(table, "FT", "Free Throws Made", "The number of free throws that a player or team has made.", None)
            self.print_term(table, "FTA", "Free Throws Attempted", "The number of free throws that a player or team has attempted.", None)
            self.print_term(table, "MIN", "Minutes Played", "The number of minutes played by a player or team.", None)
            self.print_term(table, "OR", "Offensive Rebounds", "The number of rebounds a player or team has collected while they were on offense.", None)
            self.print_term(table, "PF", "Personal Fouls", "The number of personal fouls a player or team committed.", None)
            self.print_term(table, "PTS", "Points Scored", "The number of points scored by a player or team.", None)
            self.print_term(table, "PTSoTO", "Points from Turnovers", "The number of points scored by a player or team following an opponent's turnover.", None)
            self.print_term(table, "ST", "Steals", "Number of times a defensive player or team takes the ball from a player on offense, causing a turnover.", None)
            self.print_term(table, "TO", "Turnovers", "A turnover occurs when the player or team on offense loses the ball to the defense.", None)
            self.print_term(table, "TOT", "Total Rebounds", "A rebound occurs when a player recovers the ball after a missed shot. This statistic is the number of total rebounds a player or team has collected on either offense or defense.", None)
            self.print_term(table, "TM REB", "Team Rebounds", "In situations where the whistle stops play before there is player possession following a shot attempt a team rebound is credited.", None)
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
        data = [['', 'PDi', 'PTS', 'Q1', 'Q2', 'Q3', 'Q4', 'OT', 'FG', 'FGA', '3P', '3PA', 'FT', 'FTA', 'ORB', 'DRB', 'TMRB', 'TOT', 'AST', 'PF', 'STL', 'BLK', 'TO', 'LaLe', '2ndP', 'TMTO', 'PoTO']]
        
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
            f"{row['TeamRebounds']:.0f}" if decimal else f"{row['TeamRebounds']:.2f}",
            f"{row['Rebounds']:.0f}" if decimal else f"{row['Rebounds']:.2f}",
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
   
   
   
   
   
   
   
   
   
   # =========================================================================================
   
    # def pdf_period_scores(self, quarters:list) -> None:
    #     quartersprint, totalpointshome, totalpointsaway = self.match.score_by_period(quarters)
    #     quartersprint.insert(0, "SCORE BY PERIOD")
    #     totalpointshome.insert(0, self.match.home.name)
    #     totalpointsaway.insert(0, self.match.away.name)        
    #     data = [map(str, quartersprint), map(str, totalpointshome), map(str, totalpointsaway)]

    #     width = 158     # base: 140
    #     width_col1 = 42 # base: 24
    #     width_coln = 9  # base: 9
    #     self.pdf.set_line_width(0)
    #     with self.pdf.table(width=width,
    #                         align="L",
    #                         borders_layout="SINGLE_TOP_LINE",
    #                         line_height=4,
    #                         col_widths=(width_col1,width_coln,width_coln,width_coln,width_coln,width_coln,width_coln,width_coln,width_coln,width_coln), 
    #                         text_align=("RIGHT", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER")
    #     ) as table:
    #         for data_row in data:
    #             row = table.row()
    #             for datum in data_row:
    #                 row.cell(datum)

    # def pdf_lead_tracker(self, quarters:list) -> None:
    #     ties = self.match.ties(quarters)
    #     lc = self.match.lead_chances(quarters)
    #     self.pdf.set_font("Helvetica", style="b", size = self.smalltextsize)
    #     self.pdf.cell(w = 0, h = 4, txt = f"Times Tied: {ties}", ln = 1, align = 'L')
    #     self.pdf.cell(w = 0, h = 4, txt = f"Lead Chances: {lc}", ln = 1, align = 'L')
            
    # def pdf_linescores(self, quarters:list, boxh:object, boxa:object, fullgame:bool) -> None:
    #     self.pdf.set_font("Helvetica", style="b", size = self.smalltextsize)
        
    #     if fullgame:
    #         llH, llA = self.match.largest_lead(quarters)
    #         scp_H, scp_A = self.match.second_chance_points(quarters)
    #         tmto_H, tmto_A = self.match.team_turnovers(quarters)      
    #         pot_H, pot_A = self.match.points_off_turnovers(quarters)      

    #         efgp_H, efgp_A = EFGpct(boxh.fg, boxh.tp, boxh.fga), EFGpct(boxa.fg, boxa.tp, boxa.fga)
    #         tsp_H, tsp_A = TSpct(boxh.pts, boxh.fga, boxh.fta), TSpct(boxa.pts, boxa.fga, boxa.fta)
    #         att_H, att_A = ASTtoTO(boxh.ast, boxh.to), ASTtoTO(boxa.ast, boxa.to)
            
    #         self.pdf.cell(w = 0, h = 4, txt = f"Largest Lead: HOME {llH}, AWAY {llA}", ln = 1, align = 'L')
    #         self.pdf.cell(w = 0, h = 4, txt = f"Second Chance Points: HOME {scp_H}, AWAY {scp_A}", ln = 1, align = 'L')
    #         self.pdf.cell(w = 0, h = 4, txt = f"Team Turnovers: HOME {tmto_H}, AWAY {tmto_A}", ln = 1, align = 'L')
    #         self.pdf.cell(w = 0, h = 4, txt = f"Points off Turnovers: HOME {pot_H}, AWAY {pot_A}", ln = 1, align = 'L')
    #         self.pdf.cell(w = 0, h = 4, txt = f"Effective Field Goal %: HOME {(efgp_H):.1f}, AWAY {(efgp_A):.1f}", ln = 1, align = 'L')
    #         self.pdf.cell(w = 0, h = 4, txt = f"True Shooting %: HOME {(tsp_H):.1f}, AWAY {(tsp_A):.1f}", ln = 1, align = 'L')
    #         self.pdf.cell(w = 0, h = 4, txt = f"Assist/Turnover Ratio: HOME {(att_H):.2f}, AWAY {(att_A):.2f}", ln = 1, align = 'L')
    #         self.pdf.write(text='\n')
        
    #     else:
    #         llH, llA = self.match.largest_lead(quarters)
    #         scp_H, scp_A = self.match.second_chance_points(quarters)
    #         tmto_H, tmto_A = self.match.team_turnovers(quarters)      
    #         pot_H, pot_A = self.match.points_off_turnovers(quarters)   
            
    #         self.pdf.cell(w = 0, h = 4, txt = f"Largest Lead: HOME {llH}, AWAY {llA}", ln = 1, align = 'L')
    #         self.pdf.cell(w = 0, h = 4, txt = f"Second Chance Points: HOME {scp_H}, AWAY {scp_A}", ln = 1, align = 'L')
    #         self.pdf.cell(w = 0, h = 4, txt = f"Team Turnovers: HOME {tmto_H}, AWAY {tmto_A}", ln = 1, align = 'L')
    #         self.pdf.cell(w = 0, h = 4, txt = f"Points off Turnovers: HOME {pot_H}, AWAY {pot_A}", ln = 1, align = 'L')
    #         self.pdf.write(text='\n')
   
    # def pdf_add_boxscore(self, boxscore:object) -> None:        
    #     self.pdf.set_font("Helvetica", style="b", size = self.textsize)
    #     data = [[f"{team_terms[boxscore.team.team]}: {boxscore.team.name}","MIN","FG","FGA","3P","3PA","FT","FTA","OR","DR","TOT","A","PF","ST","BS","TO","+/-","PTS"]]
    #     starters = True
    #     for gamelog in boxscore.gamelogs.values():
    #         if not gamelog.player in boxscore.starters:
    #             if starters: data.append([])
    #             starters = False
    #         data.append([f"{gamelog.player}",f"{gamelog.team.lineup.names[gamelog.player]}",f"{gamelog.sec//60:02d}:{gamelog.sec%60:02d}",f"{int(gamelog.fg or 0)}",f"{int(gamelog.fga or 0)}",f"{int(gamelog.tp or 0)}",f"{int(gamelog.tpa or 0)}",f"{int(gamelog.ft or 0)}",f"{int(gamelog.fta or 0)}",f"{int(gamelog.oreb or 0)}",f"{int(gamelog.dreb or 0)}",f"{int(gamelog.reb or 0)}",f"{int(gamelog.ast or 0)}",f"{int(gamelog.pf or 0)}",f"{int(gamelog.stl or 0)}",f"{int(gamelog.blk or 0)}",f"{int(gamelog.to or 0)}",f"{int(gamelog.pm or 0)}",f"{int(gamelog.pts or 0)}"])
    #     data.append(["","",f"{boxscore.sec//60:02d}:{boxscore.sec%60:02d}",f"{boxscore.fg}",f"{boxscore.fga}",f"{boxscore.tp}",f"{boxscore.tpa}",f"{boxscore.ft}",f"{boxscore.fta}",f"{boxscore.oreb}",f"{boxscore.dreb}",f"{boxscore.reb}",f"{boxscore.ast}",f"{boxscore.pf}",f"{boxscore.stl}",f"{boxscore.blk}",f"{boxscore.to}",f"{boxscore.pm}",f"{boxscore.pts}"])

    #     self.pdf.set_line_width(0.3)
    #     with self.pdf.table(align="L",
    #                         borders_layout="SINGLE_TOP_LINE",
    #                         line_height=4,
    #                         col_widths=(4, 30, 7, 5, 5, 5, 5, 5, 5, 4, 4, 5, 4, 4, 4, 4, 4, 5, 5), 
    #                         text_align=("CENTER", "LEFT", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER")
    #     ) as table:
    #         for idx, data_row in enumerate(data[:-2]):
    #             row = table.row()
    #             for idy, datum in enumerate(data_row):
    #                 if idx == 0 and idy == 0:
    #                     row.cell(datum, colspan=2, align="LEFT", style=FontFace(size_pt=9))
    #                 else:
    #                     row.cell(datum)
        
    #     self.pdf.set_line_width(0.3)
    #     with self.pdf.table(align="L",
    #                         borders_layout="SINGLE_TOP_LINE",
    #                         line_height=4,
    #                         col_widths=(4, 30, 7, 5, 5, 5, 5, 5, 5, 4, 4, 5, 4, 4, 4, 4, 4, 5, 5), 
    #                         text_align=("CENTER", "LEFT", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER")
    #     ) as table:
    #         for idx, data_row in enumerate(data[-2:]):
    #             row = table.row()
    #             for datum in data_row:
    #                 row.cell(datum)
                        
    #         row = table.row()
    #         row.cell("", colspan=3)
    #         row.cell(f"{(boxscore.fgpct):.1f}%", colspan=2)
    #         row.cell(f"{(boxscore.tppct):.1f}%", colspan=2)
    #         row.cell(f"{(boxscore.ftpct):.1f}%", colspan=2)
    #         row.cell(f"TM REB: {boxscore.tmreb}", colspan=3)
    #         row.cell("", colspan=7)
                      
    # def pdf_create_boxscores(self, quarters:list) -> None:
    #     self.boxh = boxscore()
    #     self.boxh.create_boxscore(self.match.home)
    #     self.boxh.add_gamelogs(self.match.events, quarters)
    #     self.boxh.make_boxscore(self.match.events, quarters)
    #     self.pdf_add_boxscore(self.boxh)
    #     self.pdf.set_font("Helvetica", style="b", size = self.smalltextsize)
    #     self.pdf.write(text='\n')
        
    #     self.boxa = boxscore()
    #     self.boxa.create_boxscore(self.match.away)
    #     self.boxa.add_gamelogs(self.match.events, quarters)
    #     self.boxa.make_boxscore(self.match.events, quarters)
    #     self.pdf_add_boxscore(self.boxa)
                
    # def all_boxscores(self, quarters:list) -> None:        
    #     i = len(quarters) - 4
    #     boxes = [[["1"],                                "1st QUARTER ONLY"],
    #              [["2"],                                "2nd QUARTER ONLY"],
    #              [["1","2"],                            "FIRST HALF"],
    #              [["3"],                                "3rd QUARTER ONLY"],
    #              [["1","2","3"],                        "1st QUARTER - 3rd QUARTER"],
    #              [["4"],                                "4th QUARTER ONLY"],
    #              [["3","4"],                            "SECOND HALF"],
    #              [["5"],                                "1st OVERTIME ONLY"],
    #              [["6"],                                "2nd OVERTIME ONLY"],
    #              [["7"],                                "3rd OVERTIME ONLY"],
    #              [["8"],                                "4th OVERTIME ONLY"],
    #              [["1","2","3","4"],                    "FINAL"],
    #              [["1","2","3","4","5"],                "FINAL"],
    #              [["1","2","3","4","5","6"],            "FINAL"],
    #              [["1","2","3","4","5","6","7"],        "FINAL"],
    #              [["1","2","3","4","5","6","7","8"],    "FINAL"]]
        
    #     self.pdf.set_font("Helvetica", style="b", size = self.titlesize)
    #     self.new_page("BOXSCORE", f"{boxes[11+i][1]}")
    #     self.pdf_create_boxscores(boxes[11+i][0])
    #     self.pdf.write(text='\n')
    #     self.pdf_period_scores(boxes[11+i][0])
    #     self.pdf.write(text='\n')
    #     self.pdf_lead_tracker(boxes[11+i][0])
    #     self.pdf_linescores(boxes[11+i][0], self.boxh, self.boxa, True)
    #     for box in boxes[:(7+i)]:
    #         self.new_page("BOXSCORE", f"{box[1]}")
    #         self.pdf.set_font("Helvetica", style="b", size = self.titlesize)
    #         self.pdf_create_boxscores(box[0])
    #         self.pdf.write(text='\n')
    #         self.pdf_period_scores(box[0])
    #         self.pdf.write(text='\n')
    #         self.pdf_lead_tracker(box[0])
    #         self.pdf_linescores(box[0], self.boxh, self.boxa, False)
                              
    # def pdf_eventlogs(self, quarter:str) -> None:
        
    #     self.pdf.set_font("Helvetica", style="b", size = self.smalltextsize)
    #     self.pdf.cell(w = 0, h = 3, txt = f"HOME Starters: {', '.join([str(self.match.home.lineup.names[starter]) for starter in self.match.home.starters[int(quarter)-1]])}", ln = 1, align = 'L')
    #     self.pdf.cell(w = 0, h = 3, txt = f"AWAY Starters: {', '.join([str(self.match.away.lineup.names[starter]) for starter in self.match.away.starters[int(quarter)-1]])}", ln = 1, align = 'L')
    #     self.pdf.write(text='\n')
        
    #     data = [[f"Time", f"{self.match.home.name}", f"Score", f"Lead", f"{self.match.away.name}"]]
    #     for event in self.match.events:
    #         if event.quarter == quarter:
    #             if event.actionID == "start":
    #                 pass
    #             elif event.actionID == "end":
    #                 pass
    #             if event.team == "H":
    #                 if event.actionID in {"2m","3m","1m"}:
    #                     data.append([f"{event.time[:2]}:{event.time[2:]}", f"{event.print_event(actions_terms,self.match.home.lineup)}", f"{event.print_score(True)[0]}", f"{event.print_score(True)[1]}", ""])
    #                 elif event.actionID in {"2", "3", "t"} and not event.actionID2 == None:
    #                     data.append([f"{event.time[:2]}:{event.time[2:]}", f"{event.print_event(actions_terms,self.match.home.lineup,self.match.away.lineup)[0]}", "", "", f"{event.print_event(actions_terms,self.match.home.lineup,self.match.away.lineup)[1]}"])
    #                 else:
    #                     data.append([f"{event.time[:2]}:{event.time[2:]}", f"{event.print_event(actions_terms,self.match.home.lineup)}", "", "", ""])
    #             if event.team == "A":
    #                 if event.actionID in {"2m","3m","1m"}:
    #                     data.append([f"{event.time[:2]}:{event.time[2:]}","",f"{event.print_score(True)[0]}",f"{event.print_score(True)[1]}",f"{event.print_event(actions_terms,self.match.away.lineup)}"])
    #                 elif event.actionID in {"2", "3", "t"} and not event.actionID2 == None:
    #                     data.append([f"{event.time[:2]}:{event.time[2:]}",f"{event.print_event(actions_terms,self.match.away.lineup,self.match.home.lineup)[1]}","","",f"{event.print_event(actions_terms,self.match.away.lineup,self.match.home.lineup)[0]}"])
    #                 else:
    #                     data.append([f"{event.time[:2]}:{event.time[2:]}","","","",f"{event.print_event(actions_terms,self.match.away.lineup)}"])
                
    #     self.pdf.set_line_width(0)
    #     with self.pdf.table(align="L",
    #                         borders_layout="SINGLE_TOP_LINE",
    #                         line_height=4,
    #                         col_widths=(4,35,4,4,35), 
    #                         text_align=("CENTER", "LEFT", "LEFT", "LEFT", "LEFT")
    #     ) as table:         
    #         for data_row in data:
    #             row = table.row()
    #             for datum in data_row:
    #                 row.cell(datum)

    #     self.pdf.cell(w = 0, h = 4, txt = f"End of {quarter_terms_lower[quarter]}", ln = 1, align = 'L')
        
    # def pdf_add_eventlogs(self, quarters:list) -> None:
    #     for quarter in quarters:
    #         self.new_page(f"PLAY-BY-PLAY", quarter_terms[quarter])
    #         self.pdf_eventlogs(quarter)
            
    # def print_term(self, table:object, term:str, meaning:str, description:str, formula:str = None) -> None:
    #     self.pdf.set_font("Helvetica", style="b", size = self.bigtextsize)
    #     row = table.row()
    #     row.cell(term, colspan=2)
    #     self.pdf.set_font("Helvetica", style="b", size = self.smalltextsize)
    #     row = table.row()
    #     row.cell("Name")
    #     row.cell(meaning)
    #     row = table.row()
    #     row.cell("Description")
    #     row.cell(description)
    #     row = table.row()
    #     row.cell("", colspan=2)
        
    # def pdf_glossary(self) -> None:
    #     self.footer()
    #     self.pdf.add_page()
    #     self.pdf.set_font("Helvetica", style="b", size = self.titlesize)
    #     self.pdf.cell(w = 0, h = 4, txt = f"GLOSSARY", ln = 1, align = 'L')
    #     self.pdf.write(text='\n')
        
    #     with self.pdf.table(align="L",
    #                         borders_layout="NONE",
    #                         line_height=3,
    #                         col_widths=(10, 90), 
    #                         text_align=("LEFT", "LEFT")
    #     ) as table:
    #         # self.print_term(table, "2nd PTS", "Second Chance Points", "Any points scored by the offense (player or team) during a possession after an offensive player has already attempted one shot and missed.", None)
    #         self.print_term(table, "3P", "Three Pointers Made", "The number of 3 point field goals that a player or team has made.", None)
    #         self.print_term(table, "3PA", "Three Pointers Attempted", "The number of 3 point field goals that a player or team has attempted.", None)
    #         self.print_term(table, "+/-", "Plus-Minus", "The point differential when a player or team is on the floor.", None)
    #         self.print_term(table, "A", "Assists", "The number of assists -- passes that lead directly to a made basket -- by a player.", None)
    #         # self.print_term(table, "AST/TO", "Assist to Turnover Ratio", "The number of assists for a player or team compared to the number of turnovers they have committed.", None)
    #         self.print_term(table, "BS", "Blocked Shots", "A block occurs when an offensive player attempts a shot, and the defense player tips the ball, blocking their chance to score.", None)
    #         self.print_term(table, "DR", "Defensive Rebounds", "The number of rebounds a player or team has collected while they were on defense.", None)
    #         # self.print_term(table, "eFG%", "Effective Field Goal Percentage", "Measures field goal percentage adjusting for made 3-point field goals being 1.5 times more valuable than made 2-point field goals.", "((FGM + (0.5 * 3PM)) / FGA")
    #         self.print_term(table, "FG", "Field Goals Made", "The number of field goals that a player or team has made. This includes both 2 pointers and 3 pointers.", None)
    #         self.print_term(table, "FGA", "Field Goals Attempted", "The number of field goals that a player or team has attempted. This includes both 2 pointers and 3 pointers", None)
    #         self.print_term(table, "FT", "Free Throws Made", "The number of free throws that a player or team has made.", None)
    #         self.print_term(table, "FTA", "Free Throws Attempted", "The number of free throws that a player or team has attempted.", None)
    #         self.print_term(table, "MIN", "Minutes Played", "The number of minutes played by a player or team.", None)
    #         self.print_term(table, "OR", "Offensive Rebounds", "The number of rebounds a player or team has collected while they were on offense.", None)
    #         self.print_term(table, "PF", "Personal Fouls", "The number of personal fouls a player or team committed.", None)
    #         self.print_term(table, "PTS", "Points Scored", "The number of points scored by a player or team.", None)
    #         # self.print_term(table, "PTS OFF TO", "Points from Turnovers", "The number of points scored by a player or team following an opponent's turnover.", None)
    #         self.print_term(table, "ST", "Steals", "Number of times a defensive player or team takes the ball from a player on offense, causing a turnover.", None)
    #         self.print_term(table, "TO", "Turnovers", "A turnover occurs when the player or team on offense loses the ball to the defense.", None)
    #         self.print_term(table, "TOT", "Total Rebounds", "A rebound occurs when a player recovers the ball after a missed shot. This statistic is the number of total rebounds a player or team has collected on either offense or defense.", None)
    #         self.print_term(table, "TM REB", "Team Rebounds", "In situations where the whistle stops play before there is player possession following a shot attempt a team rebound is credited.", None)
    #         # self.print_term(table, "TS%", "True Shooting Percentage", "A shooting percentage that factors in the value of three-point field goals and free throws in addition to conventional two-point field goals.", "PTS/[2*(FGA+0.44*FTA)]")

    # def pdf_export(self) -> None:
    #     self.footer()
    #     self.pdf.output(f"gamebooks/pdf/{self.match.matchID}_gamebook.pdf")

    # def make_pdf(self, quarters:list) -> None:
    #     self.load()
    #     self.create_pdf()
    #     self.all_boxscores(quarters)
    #     self.pdf_add_eventlogs(quarters)
    #     self.pdf_glossary()
    #     self.pdf_export()
