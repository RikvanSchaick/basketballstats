def EFGpct(FG, TP, FGA):
    return (FG + 0.5*TP)*100/FGA

def TSpct(PTS, FGA, FTA):
    return 0.5*PTS*100/(FGA+0.44*FTA)

def ASTtoTO(AST, TO):
    return AST/TO