from match import match
from boxscore import boxscore
from terminoligy import quarter_terms, actions_terms, team_terms, quarter_terms_lower, actions_terms_lower, team_terms_lower
from formulas import EFGpct, TSpct, ASTtoTO
from fpdf import FPDF
from fpdf.fonts import FontFace
from datetime import datetime, date

class gamereport():
    def __init__(self, match:match) -> None:
        self.txt = None
        self.match = match
        self.DIR = f"gamebooks/txt/{self.match.matchID}_gamebook.txt"
        self.titlesize = 11
        self.bigtextsize = 10
        self.textsize = 9
        self.smalltextsize = 8
        self.page = False
        
    def create_txt(self) -> None:
        self.file = open(self.DIR, "w")
        self.file.writelines("GAME REPORT" + '\n\n')
        self.file.writelines(f"{self.match.home.name} against {self.match.away.name} ({self.match.matchID})" + '\n')
        self.file.writelines(f"{self.match.date}, {self.match.time}, {self.match.location}" + '\n\n')
        self.file.writelines("\n\n")
        self.file.close()
        
    def txt_period_scores(self, quarters:list) -> None:
        quartersprint, totalpointshome, totalpointsaway = self.match.score_by_period(quarters)
        et1 = 16
        et2 = 5
        
        self.file = open(self.DIR, "a")
        self.file.writelines("PERIOD SCORES\t".expandtabs(et1))
        
        for quarterprint in quartersprint:
            self.file.writelines(f"{quarterprint}\t".expandtabs(et2))
        self.file.writelines("\n")
        self.file.writelines("Home\t".expandtabs(et1))
        
        for pointshome in totalpointshome:
            self.file.writelines(f"{pointshome}\t".expandtabs(et2))
        self.file.writelines("\n")
        self.file.writelines("Away\t".expandtabs(et1))
        
        for pointsaway in totalpointsaway:
            self.file.writelines(f"{pointsaway}\t".expandtabs(et2))
        self.file.writelines("\n\n")
        self.file.close()   
         
    def txt_lead_tracker(self, quarters:list) -> None:
        lc = self.match.lead_chances(quarters)
        ties = self.match.ties(quarters)
        
        et1 = 16
        et2 = 10
        
        self.file = open(self.DIR, "a")
        self.file.writelines("LEAD TRACKER\t".expandtabs(et1) + '\n')
        self.file.writelines(f"Ties {ties}\t".expandtabs(et2) + '\n')
        self.file.writelines(f"Lead Changes {lc}\t".expandtabs(et2) + '\n')
        self.file.writelines("\n")
        self.file.close()
            
    def txt_linescores(self, quarters:list, boxh:object, boxa:object, fullgame:bool) -> None:
        et1 = 16
        et2 = 9
        
        if fullgame:
            llH, llA = self.match.largest_lead(quarters)
            scp_H, scp_A = self.match.second_chance_points(quarters)
            pot_H, pot_A = self.match.points_off_turnovers(quarters)      

            efgp_H, efgp_A = EFGpct(boxh.fg, boxh.tp, boxh.fga), EFGpct(boxa.fg, boxa.tp, boxa.fga)
            tsp_H, tsp_A = TSpct(boxh.pts, boxh.fga, boxh.fta), TSpct(boxa.pts, boxa.fga, boxa.fta)
            att_H, att_A = ASTtoTO(boxh.ast, boxh.to), ASTtoTO(boxa.ast, boxa.to)
            
            self.file = open(self.DIR, "a")
            self.file.writelines("LINESCORES\t".expandtabs(et1) + "Big Ld\t".expandtabs(et2) + "2nd PTS\t".expandtabs(et2) + "TO PTS\t".expandtabs(et2) + "AST/TO\t".expandtabs(et2) + "Eff FG%\t".expandtabs(et2) + "TS%\t".expandtabs(et2) + '\n')
            self.file.writelines("Home\t".expandtabs(et1) + f"{llH}\t".expandtabs(et2) + f"{scp_H}\t".expandtabs(et2) + f"{pot_H}\t".expandtabs(et2) + f"{(att_H):.2f}\t".expandtabs(et2) + f"{(efgp_H):.1f}\t".expandtabs(et2) + f"{(tsp_H):.1f}\t".expandtabs(et2) + '\n')
            self.file.writelines("Away\t".expandtabs(et1) + f"{llA}\t".expandtabs(et2) + f"{scp_A}\t".expandtabs(et2) + f"{pot_A}\t".expandtabs(et2) + f"{(att_A):.2f}\t".expandtabs(et2) + f"{(efgp_A):.1f}\t".expandtabs(et2) + f"{(tsp_A):.1f}\t".expandtabs(et2) + '\n')
            self.file.writelines("\n")
            self.file.close()
        
        else:
            llH, llA = self.match.largest_lead(quarters)
            scp_H, scp_A = self.match.second_chance_points(quarters)
            pot_H, pot_A = self.match.points_off_turnovers(quarters)      

            self.file = open(self.DIR, "a")
            self.file.writelines("LINESCORES\t".expandtabs(et1) + "Big Ld\t".expandtabs(et2) + "2nd PTS\t".expandtabs(et2) + "TO PTS\t".expandtabs(et2) + '\n')
            self.file.writelines("Home\t".expandtabs(et1) + f"{llH}\t".expandtabs(et2) + f"{scp_H}\t".expandtabs(et2) + f"{pot_H}\t".expandtabs(et2) + '\n')
            self.file.writelines("Away\t".expandtabs(et1) + f"{llA}\t".expandtabs(et2) + f"{scp_A}\t".expandtabs(et2) + f"{pot_A}\t".expandtabs(et2) + '\n')
            self.file.writelines("\n")
            self.file.close()

    def txt_boxscore(self, quarters:list) -> None:
        boxh = boxscore()
        boxh.create_boxscore(self.match.home)
        boxh.add_gamelogs(self.match.events, quarters)
        boxh.make_boxscore(self.match.events, quarters)
        self.file = open(self.DIR, "a")
        self.file.writelines(f"{boxh.team.name} ({team_terms_lower[boxh.team.team]})" + '\n')
        self.file.writelines("\t".expandtabs(3) + "\t".expandtabs(24) + "MIN\t\tFG\tFGA\t3P\t3PA\tFT\tFTA\tOR\tDR\tTOT\tAST\tPF\tSTL\tBLK\tTO\t+/-\tPTS".expandtabs(4) + '\n')
        starters = True
        for gamelog in boxh.gamelogs.values():
            if not gamelog.player in boxh.starters:
                if starters: self.file.writelines('\n')
                starters = False
            player_name = gamelog.team.lineup.names[gamelog.player]
            self.file.writelines(f"{gamelog.player}\t".expandtabs(3) + f"{player_name}\t".expandtabs(24) + f"{gamelog.sec//60:02d}:{gamelog.sec%60:02d}\t{int(gamelog.fg or 0)}\t{int(gamelog.fga or 0)}\t{int(gamelog.tp or 0)}\t{int(gamelog.tpa or 0)}\t{int(gamelog.ft or 0)}\t{int(gamelog.fta or 0)}\t{int(gamelog.oreb or 0)}\t{int(gamelog.dreb or 0)}\t{int(gamelog.reb or 0)}\t{int(gamelog.ast or 0)}\t{int(gamelog.pf or 0)}\t{int(gamelog.stl or 0)}\t{int(gamelog.blk or 0)}\t{int(gamelog.to or 0)}\t{int(gamelog.pm or 0)}\t{int(gamelog.pts or 0)}".expandtabs(4) + '\n')
        self.file.writelines("\t".expandtabs(3) + "\t".expandtabs(24) + f"{boxh.sec//60:02d}:{boxh.sec%60:02d}\t{boxh.fg}\t{boxh.fga}\t{boxh.tp}\t{boxh.tpa}\t{boxh.ft}\t{boxh.fta}\t{boxh.oreb}\t{boxh.dreb}\t{boxh.reb}\t{boxh.ast}\t{boxh.pf}\t{boxh.stl}\t{boxh.blk}\t{boxh.to}\t{boxh.pm}\t{boxh.pts}".expandtabs(4) + '\n')
        self.file.writelines("\t".expandtabs(3) + "\t".expandtabs(24) + f"\t\t {(boxh.fgpct):.1f}%\t {(boxh.tppct):.1f}%\t {(boxh.ftpct):.1f}%\t TM REB: {boxh.tmreb}".expandtabs(4) + '\n')
        self.file.close()
        
        boxa = boxscore()
        boxa.create_boxscore(self.match.away)
        boxa.add_gamelogs(self.match.events, quarters)
        boxa.make_boxscore(self.match.events, quarters)
        self.file = open(self.DIR, "a")
        self.file.writelines(f"{boxa.team.name} ({team_terms_lower[boxa.team.team]})" + '\n')
        self.file.writelines("\t".expandtabs(3) + "\t".expandtabs(24) + "MIN\t\tFG\tFGA\t3P\t3PA\tFT\tFTA\tOR\tDR\tTOT\tAST\tPF\tSTL\tBLK\tTO\t+/-\tPTS".expandtabs(4) + '\n')
        starters = True
        for gamelog in boxa.gamelogs.values():
            if not gamelog.player in boxa.starters:
                if starters: self.file.writelines('\n')
                starters = False
            player_name = gamelog.team.lineup.names[gamelog.player]
            self.file.writelines(f"{gamelog.player}\t".expandtabs(3) + f"{player_name}\t".expandtabs(24) + f"{gamelog.sec//60:02d}:{gamelog.sec%60:02d}\t{int(gamelog.fg or 0)}\t{int(gamelog.fga or 0)}\t{int(gamelog.tp or 0)}\t{int(gamelog.tpa or 0)}\t{int(gamelog.ft or 0)}\t{int(gamelog.fta or 0)}\t{int(gamelog.oreb or 0)}\t{int(gamelog.dreb or 0)}\t{int(gamelog.reb or 0)}\t{int(gamelog.ast or 0)}\t{int(gamelog.pf or 0)}\t{int(gamelog.stl or 0)}\t{int(gamelog.blk or 0)}\t{int(gamelog.to or 0)}\t{int(gamelog.pm or 0)}\t{int(gamelog.pts or 0)}".expandtabs(4) + '\n')
        self.file.writelines("\t".expandtabs(3) + "\t".expandtabs(24) + f"{boxa.sec//60:02d}:{boxa.sec%60:02d}\t{boxa.fg}\t{boxa.fga}\t{boxa.tp}\t{boxa.tpa}\t{boxa.ft}\t{boxa.fta}\t{boxa.oreb}\t{boxa.dreb}\t{boxa.reb}\t{boxa.ast}\t{boxa.pf}\t{boxa.stl}\t{boxa.blk}\t{boxa.to}\t{boxa.pm}\t{boxa.pts}".expandtabs(4) + '\n')
        self.file.writelines("\t".expandtabs(3) + "\t".expandtabs(24) + f"\t\t {(boxa.fgpct):.1f}%\t {(boxa.tppct):.1f}%\t {(boxa.ftpct):.1f}%\t TM REB: {boxa.tmreb}".expandtabs(4) + '\n')
        self.file.writelines("\n")
        self.file.close()
        return boxh, boxa
                      
    def txt_add_boxscores(self, quarters:list) -> None:
        i = len(quarters) - 4
        boxes = [[["1"],                                "1st quarter only"],
                 [["2"],                                "2nd quarter only"],
                 [["1","2"],                            "first half"],
                 [["3"],                                "3rd quarter only"],
                 [["1","2","3"],                        "1st quarter - 3rd quarter"],
                 [["4"],                                "4th quarter only"],
                 [["3","4"],                            "second half"],
                 [["5"],                                "5th overtime only"],
                 [["6"],                                "6th overtime only"],
                 [["7"],                                "7th overtime only"],
                 [["8"],                                "8th overtime only"],
                 [["1","2","3","4"],                    "final boxscore"],
                 [["1","2","3","4","5"],                "final boxscore"],
                 [["1","2","3","4","5","6"],            "final boxscore"],
                 [["1","2","3","4","5","6","7"],        "final boxscore"],
                 [["1","2","3","4","5","6","7","8"],    "final boxscore"]]
        
        self.file = open(self.DIR, "a")
        self.file.writelines(f"BOXSCORE ({boxes[11+i][1]})\n")
        self.file.close()
        boxh, boxa = self.txt_boxscore(boxes[11+i][0])
        self.txt_period_scores(boxes[11+i][0])
        self.txt_lead_tracker(boxes[11+i][0])
        self.txt_linescores(boxes[11+i][0], boxh, boxa, True)
        self.file = open(self.DIR, "a")
        self.file.writelines("\n\n")
        self.file.close()
        
        for box in boxes[:(6+i)]:
            self.file = open(self.DIR, "a")
            self.file.writelines(f"BOXSCORE ({box[1]})\n")
            self.file.close()
            boxh, boxa = self.txt_boxscore(box[0])
            self.txt_period_scores(box[0])
            self.txt_lead_tracker(box[0])
            self.txt_linescores(box[0], boxh, boxa, False)
            self.file = open(self.DIR, "a")
            self.file.writelines("\n\n")
            self.file.close()
                              
    def txt_eventlogs(self, quarter:str) -> None:
        for event in self.match.events:
            if event.quarter == quarter:
                self.file = open(self.DIR, "a")
                if event.actionID == "start":
                    self.file.writelines(f"PLAY-BY-PLAY ({quarter_terms_lower[event.quarter]})".expandtabs(8) + '\n')
                    self.file.writelines(f"{self.match.home.name} starters:\t".expandtabs(26))
                    for starter in self.match.home.starters[int(quarter)-1]:
                        self.file.writelines(f"{starter}\t".expandtabs(3))
                    self.file.writelines(f"\n{self.match.away.name} starters:\t".expandtabs(26))
                    for starter in self.match.away.starters[int(quarter)-1]:
                        self.file.writelines(f"{starter}\t".expandtabs(3))
                    self.file.writelines("\n")
                    self.file.writelines(f"Time\t".expandtabs(8) + f"{self.match.home.name}\t".expandtabs(30) + f"Score\tLead\t{self.match.away.name}".expandtabs(8) + '\n')
                elif event.actionID == "end":
                    self.file.writelines(f"End of {quarter_terms_lower[event.quarter]} ({event.print_score(False)})".expandtabs(8) + '\n')
                if event.team == "H":
                    if event.actionID in {"2m","3m","1m"}:
                        self.file.writelines(f"{event.time[:2]}:{event.time[2:]}\t".expandtabs(8) + f"{event.print_event(actions_terms_lower)}\t".expandtabs(30) + f"{event.print_score(True)[0]}\t".expandtabs(8) + f"{event.print_score(True)[1]}" + '\n')
                    elif event.actionID in {"2", "3", "t"} and not event.actionID2 == None:
                        self.file.writelines(f"{event.time[:2]}:{event.time[2:]}\t".expandtabs(8) + f"{event.print_event(actions_terms_lower)[0]}\t".expandtabs(30) + f"\t\t".expandtabs(8) + f"{event.print_event(actions_terms_lower)[1]}" + '\n')
                    else:
                        self.file.writelines(f"{event.time[:2]}:{event.time[2:]}\t".expandtabs(8) + f"{event.print_event(actions_terms_lower)}\t".expandtabs(30) + '\n')
                if event.team == "A":
                    if event.actionID in {"2m","3m","1m"}:
                        self.file.writelines(f"{event.time[:2]}:{event.time[2:]}\t".expandtabs(8) + f"\t".expandtabs(30) + f"{event.print_score(True)[0]}\t".expandtabs(8) + f"{event.print_score(True)[1]}\t".expandtabs(8) + f"{event.print_event(actions_terms_lower)}" + '\n')
                    elif event.actionID in {"2", "3", "t"} and not event.actionID2 == None:
                        self.file.writelines(f"{event.time[:2]}:{event.time[2:]}\t".expandtabs(8) + f"{event.print_event(actions_terms_lower)[1]}\t".expandtabs(30) + f"\t\t".expandtabs(8) + f"{event.print_event(actions_terms_lower)[0]}" + '\n')
                    else:
                        self.file.writelines(f"{event.time[:2]}:{event.time[2:]}\t".expandtabs(8) + f"\t".expandtabs(30) + f"\t\t".expandtabs(8) + f"{event.print_event(actions_terms_lower)}" + '\n')
                self.file.close()

    def txt_add_eventlogs(self, quarters:list) -> None:
        for quarter in quarters:                
            self.txt_eventlogs(quarter)
            self.file = open(self.DIR, "a")
            self.file.writelines("\n")
            self.file.close()
        self.file = open(self.DIR, "a")
        self.file.writelines("\n\n")
        self.file.close()
        
    def txt_end(self) -> None:
        self.file = open(self.DIR, "a")
        self.file.writelines(f"GLOSSARY" + '\n')
        self.file.writelines(f"+/-:\t Plus-Minus".expandtabs(10) + '\n')
        self.file.writelines(f"2nd PTS:\t Second Chance Points".expandtabs(10) + '\n')
        self.file.writelines(f"3P:\t Three Pointers Made".expandtabs(10) + '\n')
        self.file.writelines(f"3PA:\t Three Pointers Attempted".expandtabs(10) + '\n')
        self.file.writelines(f"AST:\t Assists".expandtabs(10) + '\n')
        self.file.writelines(f"AST/TO:\t Assist to Turnover Ratio".expandtabs(10) + '\n')
        self.file.writelines(f"Big Ld:\t Biggest Lead".expandtabs(10) + '\n')
        self.file.writelines(f"BLK:\t Blocks".expandtabs(10) + '\n')
        self.file.writelines(f"DR:\t Defensive Rebounds".expandtabs(10) + '\n')
        self.file.writelines(f"Eff FG%:\t Effective Field Goal Percentage".expandtabs(10) + '\n')
        self.file.writelines(f"FG:\t Field Goals Made".expandtabs(10) + '\n')
        self.file.writelines(f"FGA:\t Field Goals Attempted".expandtabs(10) + '\n')
        self.file.writelines(f"FT:\t Free Throws Made".expandtabs(10) + '\n')
        self.file.writelines(f"FTA:\t Free Throws Attempted".expandtabs(10) + '\n')
        self.file.writelines(f"MIN:\t Minutes Played".expandtabs(10) + '\n')
        self.file.writelines(f"OR:\t Offensive Rebounds".expandtabs(10) + '\n')
        self.file.writelines(f"PF:\t Personal Fouls".expandtabs(10) + '\n')
        self.file.writelines(f"PTS:\t Points Scored".expandtabs(10) + '\n')
        self.file.writelines(f"STL:\t Steals".expandtabs(10) + '\n')
        self.file.writelines(f"TO:\t Turnovers".expandtabs(10) + '\n')
        self.file.writelines(f"TO PTS:\t Points from Turnovers".expandtabs(10) + '\n')
        self.file.writelines(f"TOT:\t Total Rebounds".expandtabs(10) + '\n')
        self.file.writelines(f"TM REB:\t Team Rebounds".expandtabs(10) + '\n')
        self.file.writelines(f"TS%:\t True Shooting Percentage".expandtabs(10) + '\n')
        self.file.close()

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
            row.cell("GAME REPORT")
            row.cell(pagetitle)
            row = table.row()
            row.cell("")
            row.cell(subtitle)
            
        self.pdf.set_font("Helvetica", style="b", size = self.textsize)
        self.pdf.cell(w = 0, h = 4, txt = f"#{self.match.matchID}", ln = 1, align = 'L')
        self.pdf.cell(w = 0, h = 4, txt = f"{self.match.home.name} against {self.match.away.name}", ln = 1, align = 'L')
        d = datetime.strptime(self.match.date, '%d-%m-%Y')
        d = date.strftime(d, "%d %B %Y")
        self.pdf.cell(w = 0, h = 4, txt = f"{d}, {self.match.time}, {self.match.location}", ln = 1, align = 'L')
        self.pdf.write(text='\n')
                
    def create_pdf(self) -> None:
        self.pdf = FPDF()
        self.pdf.set_margin(4)
   
    def pdf_period_scores(self, quarters:list) -> None:
        quartersprint, totalpointshome, totalpointsaway = self.match.score_by_period(quarters)
        quartersprint.insert(0, "SCORE BY PERIOD")
        totalpointshome.insert(0, self.match.home.name)
        totalpointsaway.insert(0, self.match.away.name)        
        data = [map(str, quartersprint), map(str, totalpointshome), map(str, totalpointsaway)]

        width = 158     # base: 140
        width_col1 = 42 # base: 24
        width_coln = 9  # base: 9
        self.pdf.set_line_width(0)
        with self.pdf.table(width=width,
                            align="L",
                            borders_layout="SINGLE_TOP_LINE",
                            line_height=4,
                            col_widths=(width_col1,width_coln,width_coln,width_coln,width_coln,width_coln,width_coln,width_coln,width_coln,width_coln), 
                            text_align=("RIGHT", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER")
        ) as table:
            for data_row in data:
                row = table.row()
                for datum in data_row:
                    row.cell(datum)

    def pdf_lead_tracker(self, quarters:list) -> None:
        ties = self.match.ties(quarters)
        lc = self.match.lead_chances(quarters)
        self.pdf.set_font("Helvetica", style="b", size = self.smalltextsize)
        self.pdf.cell(w = 0, h = 4, txt = f"Times Tied: {ties}", ln = 1, align = 'L')
        self.pdf.cell(w = 0, h = 4, txt = f"Lead Chances: {lc}", ln = 1, align = 'L')
            
    def pdf_linescores(self, quarters:list, boxh:object, boxa:object, fullgame:bool) -> None:
        self.pdf.set_font("Helvetica", style="b", size = self.smalltextsize)
        
        if fullgame:
            llH, llA = self.match.largest_lead(quarters)
            scp_H, scp_A = self.match.second_chance_points(quarters)
            pot_H, pot_A = self.match.points_off_turnovers(quarters)      

            efgp_H, efgp_A = EFGpct(boxh.fg, boxh.tp, boxh.fga), EFGpct(boxa.fg, boxa.tp, boxa.fga)
            tsp_H, tsp_A = TSpct(boxh.pts, boxh.fga, boxh.fta), TSpct(boxa.pts, boxa.fga, boxa.fta)
            att_H, att_A = ASTtoTO(boxh.ast, boxh.to), ASTtoTO(boxa.ast, boxa.to)
            
            self.pdf.cell(w = 0, h = 4, txt = f"Largest Lead: HOME {llH}, AWAY {llA}", ln = 1, align = 'L')
            self.pdf.cell(w = 0, h = 4, txt = f"Second Chance Points: HOME {scp_H}, AWAY {scp_A}", ln = 1, align = 'L')
            self.pdf.cell(w = 0, h = 4, txt = f"Points off Turnovers: HOME {pot_H}, AWAY {pot_A}", ln = 1, align = 'L')
            self.pdf.cell(w = 0, h = 4, txt = f"Effective Field Goal %: HOME {(efgp_H):.1f}, AWAY {(efgp_A):.1f}", ln = 1, align = 'L')
            self.pdf.cell(w = 0, h = 4, txt = f"True Shooting %: HOME {(tsp_H):.1f}, AWAY {(tsp_A):.1f}", ln = 1, align = 'L')
            self.pdf.cell(w = 0, h = 4, txt = f"Assist/Turnover Ratio: HOME {(att_H):.2f}, AWAY {(att_A):.2f}", ln = 1, align = 'L')
            self.pdf.write(text='\n')
        
        else:
            llH, llA = self.match.largest_lead(quarters)
            scp_H, scp_A = self.match.second_chance_points(quarters)
            pot_H, pot_A = self.match.points_off_turnovers(quarters)   
            
            self.pdf.cell(w = 0, h = 4, txt = f"Largest Lead: HOME {llH}, AWAY {llA}", ln = 1, align = 'L')
            self.pdf.cell(w = 0, h = 4, txt = f"2nd Chance Points: HOME {scp_H}, AWAY {scp_A}", ln = 1, align = 'L')
            self.pdf.cell(w = 0, h = 4, txt = f"Points off Turnovers: HOME {pot_H}, AWAY {pot_A}", ln = 1, align = 'L')
            self.pdf.write(text='\n')
   
    def pdf_add_boxscore(self, boxscore:object) -> None:        
        self.pdf.set_font("Helvetica", style="b", size = self.textsize)
        data = [[f"{team_terms[boxscore.team.team]}: {boxscore.team.name}","MIN","FG","FGA","3P","3PA","FT","FTA","OR","DR","TOT","A","PF","ST","BS","TO","+/-","PTS"]]
        starters = True
        for gamelog in boxscore.gamelogs.values():
            if not gamelog.player in boxscore.starters:
                if starters: data.append([])
                starters = False
            data.append([f"{gamelog.player}",f"{gamelog.team.lineup.names[gamelog.player]}",f"{gamelog.sec//60:02d}:{gamelog.sec%60:02d}",f"{int(gamelog.fg or 0)}",f"{int(gamelog.fga or 0)}",f"{int(gamelog.tp or 0)}",f"{int(gamelog.tpa or 0)}",f"{int(gamelog.ft or 0)}",f"{int(gamelog.fta or 0)}",f"{int(gamelog.oreb or 0)}",f"{int(gamelog.dreb or 0)}",f"{int(gamelog.reb or 0)}",f"{int(gamelog.ast or 0)}",f"{int(gamelog.pf or 0)}",f"{int(gamelog.stl or 0)}",f"{int(gamelog.blk or 0)}",f"{int(gamelog.to or 0)}",f"{int(gamelog.pm or 0)}",f"{int(gamelog.pts or 0)}"])
        data.append(["","",f"{boxscore.sec//60:02d}:{boxscore.sec%60:02d}",f"{boxscore.fg}",f"{boxscore.fga}",f"{boxscore.tp}",f"{boxscore.tpa}",f"{boxscore.ft}",f"{boxscore.fta}",f"{boxscore.oreb}",f"{boxscore.dreb}",f"{boxscore.reb}",f"{boxscore.ast}",f"{boxscore.pf}",f"{boxscore.stl}",f"{boxscore.blk}",f"{boxscore.to}",f"{boxscore.pm}",f"{boxscore.pts}"])

        self.pdf.set_line_width(0.3)
        with self.pdf.table(align="L",
                            borders_layout="SINGLE_TOP_LINE",
                            line_height=4,
                            col_widths=(4, 30, 7, 5, 5, 5, 5, 5, 5, 4, 4, 5, 4, 4, 4, 4, 4, 5, 5), 
                            text_align=("CENTER", "LEFT", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER")
        ) as table:
            for idx, data_row in enumerate(data[:-2]):
                row = table.row()
                for idy, datum in enumerate(data_row):
                    if idx == 0 and idy == 0:
                        row.cell(datum, colspan=2, align="LEFT", style=FontFace(size_pt=9))
                    else:
                        row.cell(datum)
        
        self.pdf.set_line_width(0.3)
        with self.pdf.table(align="L",
                            borders_layout="SINGLE_TOP_LINE",
                            line_height=4,
                            col_widths=(4, 30, 7, 5, 5, 5, 5, 5, 5, 4, 4, 5, 4, 4, 4, 4, 4, 5, 5), 
                            text_align=("CENTER", "LEFT", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER")
        ) as table:
            for idx, data_row in enumerate(data[-2:]):
                row = table.row()
                for datum in data_row:
                    row.cell(datum)
                        
            row = table.row()
            row.cell("", colspan=3)
            row.cell(f"{(boxscore.fgpct):.1f}%", colspan=2)
            row.cell(f"{(boxscore.tppct):.1f}%", colspan=2)
            row.cell(f"{(boxscore.ftpct):.1f}%", colspan=2)
            row.cell(f"TM REB: {boxscore.tmreb}", colspan=3)
            row.cell("", colspan=7)
                      
    def pdf_create_boxscores(self, quarters:list) -> None:
        self.boxh = boxscore()
        self.boxh.create_boxscore(self.match.home)
        self.boxh.add_gamelogs(self.match.events, quarters)
        self.boxh.make_boxscore(self.match.events, quarters)
        self.pdf_add_boxscore(self.boxh)
        self.pdf.set_font("Helvetica", style="b", size = self.smalltextsize)
        self.pdf.write(text='\n')
        
        self.boxa = boxscore()
        self.boxa.create_boxscore(self.match.away)
        self.boxa.add_gamelogs(self.match.events, quarters)
        self.boxa.make_boxscore(self.match.events, quarters)
        self.pdf_add_boxscore(self.boxa)
                
    def all_boxscores(self, quarters:list) -> None:        
        i = len(quarters) - 4
        boxes = [[["1"],                                "1st QUARTER ONLY"],
                 [["2"],                                "2nd QUARTER ONLY"],
                 [["1","2"],                            "FIRST HALF"],
                 [["3"],                                "3rd QUARTER ONLY"],
                 [["1","2","3"],                        "1st QUARTER - 3rd QUARTER"],
                 [["4"],                                "4th QUARTER ONLY"],
                 [["3","4"],                            "SECOND HALF"],
                 [["5"],                                "1st OVERTIME ONLY"],
                 [["6"],                                "2nd OVERTIME ONLY"],
                 [["7"],                                "3rd OVERTIME ONLY"],
                 [["8"],                                "4th OVERTIME ONLY"],
                 [["1","2","3","4"],                    "FINAL"],
                 [["1","2","3","4","5"],                "FINAL"],
                 [["1","2","3","4","5","6"],            "FINAL"],
                 [["1","2","3","4","5","6","7"],        "FINAL"],
                 [["1","2","3","4","5","6","7","8"],    "FINAL"]]
        
        self.pdf.set_font("Helvetica", style="b", size = self.titlesize)
        self.new_page("BOXSCORE", f"{boxes[11+i][1]}")
        self.pdf_create_boxscores(boxes[11+i][0])
        self.pdf.write(text='\n')
        self.pdf_period_scores(boxes[11+i][0])
        self.pdf.write(text='\n')
        self.pdf_lead_tracker(boxes[11+i][0])
        self.pdf_linescores(boxes[11+i][0], self.boxh, self.boxa, True)
        for box in boxes[:(7+i)]:
            self.new_page("BOXSCORE", f"{box[1]}")
            self.pdf.set_font("Helvetica", style="b", size = self.titlesize)
            self.pdf_create_boxscores(box[0])
            self.pdf.write(text='\n')
            self.pdf_period_scores(box[0])
            self.pdf.write(text='\n')
            self.pdf_lead_tracker(box[0])
            self.pdf_linescores(box[0], self.boxh, self.boxa, False)
                              
    def pdf_eventlogs(self, quarter:str) -> None:
        
        self.pdf.set_font("Helvetica", style="b", size = self.smalltextsize)
        self.pdf.cell(w = 0, h = 3, txt = f"HOME Starters: {', '.join([str(self.match.home.lineup.names[starter]) for starter in self.match.home.starters[int(quarter)-1]])}", ln = 1, align = 'L')
        self.pdf.cell(w = 0, h = 3, txt = f"AWAY Starters: {', '.join([str(self.match.away.lineup.names[starter]) for starter in self.match.away.starters[int(quarter)-1]])}", ln = 1, align = 'L')
        self.pdf.write(text='\n')
        
        data = [[f"Time", f"{self.match.home.name}", f"Score", f"Lead", f"{self.match.away.name}"]]
        for event in self.match.events:
            if event.quarter == quarter:
                if event.actionID == "start":
                    pass
                elif event.actionID == "end":
                    pass
                if event.team == "H":
                    if event.actionID in {"2m","3m","1m"}:
                        data.append([f"{event.time[:2]}:{event.time[2:]}", f"{event.print_event(actions_terms,self.match.home.lineup)}", f"{event.print_score(True)[0]}", f"{event.print_score(True)[1]}", ""])
                    elif event.actionID in {"2", "3", "t"} and not event.actionID2 == None:
                        data.append([f"{event.time[:2]}:{event.time[2:]}", f"{event.print_event(actions_terms,self.match.home.lineup,self.match.away.lineup)[0]}", "", "", f"{event.print_event(actions_terms,self.match.home.lineup,self.match.away.lineup)[1]}"])
                    else:
                        data.append([f"{event.time[:2]}:{event.time[2:]}", f"{event.print_event(actions_terms,self.match.home.lineup)}", "", "", ""])
                if event.team == "A":
                    if event.actionID in {"2m","3m","1m"}:
                        data.append([f"{event.time[:2]}:{event.time[2:]}","",f"{event.print_score(True)[0]}",f"{event.print_score(True)[1]}",f"{event.print_event(actions_terms,self.match.away.lineup)}"])
                    elif event.actionID in {"2", "3", "t"} and not event.actionID2 == None:
                        data.append([f"{event.time[:2]}:{event.time[2:]}",f"{event.print_event(actions_terms,self.match.away.lineup,self.match.home.lineup)[1]}","","",f"{event.print_event(actions_terms,self.match.away.lineup,self.match.home.lineup)[0]}"])
                    else:
                        data.append([f"{event.time[:2]}:{event.time[2:]}","","","",f"{event.print_event(actions_terms,self.match.away.lineup)}"])
                
        self.pdf.set_line_width(0)
        with self.pdf.table(align="L",
                            borders_layout="SINGLE_TOP_LINE",
                            line_height=4,
                            col_widths=(4,35,4,4,35), 
                            text_align=("CENTER", "LEFT", "LEFT", "LEFT", "LEFT")
        ) as table:         
            for data_row in data:
                row = table.row()
                for datum in data_row:
                    row.cell(datum)

        self.pdf.cell(w = 0, h = 4, txt = f"End of {quarter_terms_lower[quarter]}", ln = 1, align = 'L')
        
    def pdf_add_eventlogs(self, quarters:list) -> None:

        for quarter in quarters:
            self.new_page(f"PLAY-BY-PLAY", quarter_terms[quarter])
            self.pdf_eventlogs(quarter)
            
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
        
        with self.pdf.table(align="L",
                            borders_layout="NONE",
                            line_height=3,
                            col_widths=(10, 90), 
                            text_align=("LEFT", "LEFT")
        ) as table:
            # self.print_term(table, "2nd PTS", "Second Chance Points", "Any points scored by the offense (player or team) during a possession after an offensive player has already attempted one shot and missed.", None)
            self.print_term(table, "3P", "Three Pointers Made", "The number of 3 point field goals that a player or team has made.", None)
            self.print_term(table, "3PA", "Three Pointers Attempted", "The number of 3 point field goals that a player or team has attempted.", None)
            self.print_term(table, "+/-", "Plus-Minus", "The point differential when a player or team is on the floor.", None)
            self.print_term(table, "A", "Assists", "The number of assists -- passes that lead directly to a made basket -- by a player.", None)
            # self.print_term(table, "AST/TO", "Assist to Turnover Ratio", "The number of assists for a player or team compared to the number of turnovers they have committed.", None)
            self.print_term(table, "BS", "Blocked Shots", "A block occurs when an offensive player attempts a shot, and the defense player tips the ball, blocking their chance to score.", None)
            self.print_term(table, "DR", "Defensive Rebounds", "The number of rebounds a player or team has collected while they were on defense.", None)
            # self.print_term(table, "eFG%", "Effective Field Goal Percentage", "Measures field goal percentage adjusting for made 3-point field goals being 1.5 times more valuable than made 2-point field goals.", "((FGM + (0.5 * 3PM)) / FGA")
            self.print_term(table, "FG", "Field Goals Made", "The number of field goals that a player or team has made. This includes both 2 pointers and 3 pointers.", None)
            self.print_term(table, "FGA", "Field Goals Attempted", "The number of field goals that a player or team has attempted. This includes both 2 pointers and 3 pointers", None)
            self.print_term(table, "FT", "Free Throws Made", "The number of free throws that a player or team has made.", None)
            self.print_term(table, "FTA", "Free Throws Attempted", "The number of free throws that a player or team has attempted.", None)
            self.print_term(table, "MIN", "Minutes Played", "The number of minutes played by a player or team.", None)
            self.print_term(table, "OR", "Offensive Rebounds", "The number of rebounds a player or team has collected while they were on offense.", None)
            self.print_term(table, "PF", "Personal Fouls", "The number of personal fouls a player or team committed.", None)
            self.print_term(table, "PTS", "Points Scored", "The number of points scored by a player or team.", None)
            # self.print_term(table, "PTS OFF TO", "Points from Turnovers", "The number of points scored by a player or team following an opponent's turnover.", None)
            self.print_term(table, "ST", "Steals", "Number of times a defensive player or team takes the ball from a player on offense, causing a turnover.", None)
            self.print_term(table, "TO", "Turnovers", "A turnover occurs when the player or team on offense loses the ball to the defense.", None)
            self.print_term(table, "TOT", "Total Rebounds", "A rebound occurs when a player recovers the ball after a missed shot. This statistic is the number of total rebounds a player or team has collected on either offense or defense.", None)
            self.print_term(table, "TM REB", "Team Rebounds", "In situations where the whistle stops play before there is player possession following a shot attempt a team rebound is credited.", None)
            # self.print_term(table, "TS%", "True Shooting Percentage", "A shooting percentage that factors in the value of three-point field goals and free throws in addition to conventional two-point field goals.", "PTS/[2*(FGA+0.44*FTA)]")

    def pdf_export(self) -> None:
        self.footer()
        self.pdf.output(f"gamebooks/pdf/{self.match.matchID}_gamebook.pdf")
        
    def make_txt(self, quarters:list) -> None:
        self.create_txt()
        self.txt_add_boxscores(quarters)
        self.txt_add_eventlogs(quarters)
        self.txt_end()
    
    def make_pdf(self, quarters:list) -> None:
        self.create_pdf()
        self.all_boxscores(quarters)
        self.pdf_add_eventlogs(quarters)
        self.pdf_glossary()
        self.pdf_export()
