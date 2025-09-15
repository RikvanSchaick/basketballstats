class gamelog():
    def __init__(self, player, team, starter) -> None:
        self.player = player
        self.team = team
        self.starter = starter
        self.subbedin = []
        self.subbedout = []
        self.sec = None
        self.fg = None
        self.fga = None
        self.tp = None
        self.tpa = None        
        self.ft = None
        self.fta = None
        self.oreb = None
        self.dreb = None
        self.reb = None
        self.ast = None
        self.pf = None
        # self.pfc = None # Fouls committed
        # self.pfd = None # Fouls drawn
        self.stl = None
        self.blk = None
        self.blkd = None # Blocked
        self.to = None
        self.pir = None # PERFORMANCE INDEX RATING
        self.pm = None
        self.pts = None
        
    def add(self, action:str, boolean:str) -> None:        
        if action == "1m":
            if self.ft == None: self.ft = 0
            self.ft += 1
            if self.fta == None: self.fta = 0
            self.fta += 1
            if self.pts == None: self.pts = 0
            self.pts += 1
            
        if action == "2m":
            if self.fg == None: self.fg = 0
            self.fg += 1
            if self.fga == None: self.fga = 0
            self.fga += 1
            if self.pts == None: self.pts = 0
            self.pts += 2
            
        if action == "3m":
            if self.fg == None: self.fg = 0
            self.fg += 1
            if self.fga == None: self.fga = 0
            self.fga += 1
            if self.tp == None: self.tp = 0
            self.tp += 1
            if self.tpa == None: self.tpa = 0       
            self.tpa += 1
            if self.pts == None: self.pts = 0
            self.pts += 3
            
        if action == "1":
            if self.fta == None: self.fta = 0
            self.fta += 1
        
        if action == "2":
            if self.fga == None: self.fga = 0
            self.fga += 1
        
        if action == "3":
            if self.fga == None: self.fga = 0
            self.fga += 1
            if self.tpa == None: self.tpa = 0       
            self.tpa += 1
        
        if action in {"f0", "f1", "f2", "f3", "ft", "fu"}:
            # if self.pfc == None: self.pfc = 0
            # self.pfc += 1
            if self.pf == None: self.pf = 0
            self.pf += 1
        
        if action == "r":
            if self.reb == None: self.reb = 0
            self.reb += 1
            if boolean:
                if self.oreb == None: self.oreb = 0
                self.oreb += 1
            else:
                if self.dreb == None: self.dreb = 0
                self.dreb += 1
                    
        if action == "a":
            if self.ast == None: self.ast = 0
            self.ast += 1
                    
        if action == "s":
            if self.stl == None: self.stl = 0
            self.stl += 1
        
        if action == "b":
            if self.blk == None: self.blk = 0
            self.blk += 1
        
        if action == "t":
            if self.to == None: self.to = 0
            self.to += 1

        # BLOCKED:
        if action == "blkd":
            if self.blkd == None: self.blkd = 0
            self.blkd += 1
            
        # FOULS DRAWN:
        if action == "pfd":
            if self.pfd == None: self.pfd = 0
            self.pfd += 1

    def sub(self, action:str, quarter:str, time:str, lead:int) -> None:
        if action == "start":
            self.subbedin.append([quarter, time, lead])
        
        if action == "end":
            if not len(self.subbedin) == len(self.subbedout):
                self.subbedout.append([quarter, time, lead])
        
        if action == "out":
            self.subbedout.append([quarter, time, lead])
        
        if action == "in":            
            self.subbedin.append([quarter, time, lead])
    
    def time_subtraction(self, intime:str, outtime:str) -> int:
        intime_sec = int(intime[:2])*60 + int(intime[2:])
        outtime_sec = int(outtime[:2])*60 + int(outtime[2:])
        dss = intime_sec - outtime_sec
        return dss
    
    def minutes(self, quarters:list) -> None:
        if self.sec == None: self.sec = 0
        for i in range(len(self.subbedin)):
            if self.subbedin[i][0] in quarters:
                self.sec += self.time_subtraction(self.subbedin[i][1], self.subbedout[i][1])
                
    # PERFORMANCE INDEX RATING:
    def performanceindexrating(self, quarters:list) -> None:
        if self.pir == None: self.pir = 0
        for i in range(len(self.subbedin)):
            if self.subbedin[i][0] in quarters:
                self.pir = (self.pts + self.reb + self.ast + self.stl + self.blk + self.pfd) - ((self.fga - self.fg) + (self.fta - self.ft) + self.to + self.blkd + self.pfc)
                
    def plusminus(self, quarters:list) -> None:
        if self.pm == None: self.pm = 0
        for i in range(len(self.subbedin)):
            if self.subbedin[i][0] in quarters:
                if self.team.team == "H":
                    self.pm += (self.subbedout[i][2] - self.subbedin[i][2])
                if self.team.team == "A":
                    self.pm += -(self.subbedout[i][2] - self.subbedin[i][2])