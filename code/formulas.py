def EFGpct(FG, TP, FGA):
    return (FG+0.5*TP)*100/FGA

def TSpct(PTS, FGA, FTA):
    return 0.5*PTS*100/(FGA+0.44*FTA)

def ASTtoTO(AST, TO):
    return AST/TO

def POSSteam(FGA, FTA, OR, OppDR, FGM, TO):
    return FGA+0.44*FTA-1.07*(OR/(OR+OppDR))*(FGA-FGM)+TO
 
def POSS(POSS1, POSS2):
    return (POSS1+POSS2)/2

def PACE(POSS, MIN):
    return POSS/(MIN)*40