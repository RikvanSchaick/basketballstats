from terminoligy import actions_terms

class event():
    def __init__(self) -> None:
        self.quarter = None
        self.time = None
        self.actionID = None
        self.actionID2 = None
        self.team = None
        self.playerID = None
        self.playerID2 = None
        self.score = None        
        self.lead = None
        
    def get_quarter(self, eventstring:str) -> bool:
        if len(eventstring) < 1: return False
        if eventstring[0].isnumeric():
            self.quarter = eventstring[0]
            return True
        else:
            return False
        
    def get_time(self, eventstring:str) -> bool:
        if len(eventstring) < 6: return False
        if eventstring[1:5].isnumeric():
            if int(eventstring[3]) > 6: return False 
            if int(eventstring[1]) > 1: return False 
            if int(eventstring[3]) == 6:
                if not int(eventstring[4]) == 0: return False
            if int(eventstring[1]) == 1:
                if not (int(eventstring[4]) + int(eventstring[3]) + int(eventstring[2])) == 0: return False
            self.time = eventstring[1:5]
            return True
        else:
            return False
        
    def get_action(self, eventstring:str) -> {bool, int}:
        if len(eventstring) < 7: return False
        if eventstring[5:8] == "out":
            self.actionID = eventstring[5:8]
            return 3
        elif eventstring[5:7] in {"2m", "3m", "1m", "f0", "f1", "f2", "f3", "ft", "fu", "fd", "to"}:
            self.actionID = eventstring[5:7]
            return 2
        elif eventstring[5] in {"r","a","s","b","2","3","1","t","j"}:
            self.actionID = eventstring[5]
            return 1
        else:
            return False

    def get_team(self,eventstring:str, i:int) -> {bool, int}:
        if len(eventstring) < 6+i: return False
        if eventstring[5+i] in {'H','A'}:
            self.team = eventstring[5+i]
            return True
        else:
            return False

    def get_player(self, eventstring:str, i:int) -> {bool, int}:
        if len(eventstring) < 7+i: return False
        if eventstring[5+i] in {'H','A'} and eventstring[6+i].isnumeric():
            self.team = eventstring[5+i]
            if 7+i == len(eventstring):
                self.playerID = eventstring[6+i]
                return 1
            elif eventstring[7+i].isnumeric():
                self.playerID = eventstring[6+i:8+i]
                return 3
            else:
                self.playerID = eventstring[6+i]
                return 2
        else: 
            return False
        
    def get_action2(self, eventstring:str, i:int) -> {bool}:
        if len(eventstring) < 8+i: return True        
        if eventstring[5+i] in {"a", "s", "b"}:
            self.actionID2 = eventstring[5+i]
            if len(eventstring) < 8+i: return False
            if eventstring[6+i] in {'H','A'} and eventstring[7+i].isnumeric():
                if 8+i == len(eventstring):
                    self.playerID2 = eventstring[7+i]
                elif eventstring[8+i].isnumeric():
                    self.playerID2 = eventstring[7+i:9+i]
                else:
                    self.playerID2 = eventstring[7+i]
                return True
        
    def get_substitute(self, eventstring:str, i:int) -> bool:
        if len(eventstring) < 8+i: return False        
        if eventstring[5+i:7+i] == "in":
            self.actionID2 = eventstring[5+i:7+i]
            if len(eventstring) < 9+i: return False
            if eventstring[7+i] in {'H','A'} and eventstring[8+i].isnumeric():
                if 9+i == len(eventstring):
                    self.playerID2 = eventstring[8+i]
                elif eventstring[9+i].isnumeric():
                    self.playerID2 = eventstring[8+i:10+i]
                else:
                    self.playerID2 = eventstring[8+i]
                return True
            else: 
                return False   
        else: 
            return False
                
    def start_quarter(self, eventstring:str) -> bool:
        if eventstring[:4] == "edit": 
            if eventstring[4].isnumeric():
                if eventstring[4] in {"1","2","3","4"}:
                    self.quarter = eventstring[4]
                    self.time = "1000"
                    self.actionID = "start"
                    return True
                elif eventstring[4] in {"5","6","7","8"}:
                    self.quarter = eventstring[4]
                    self.time = "0500"
                    self.actionID = "start"
                    return True
                return False                
            return False
        return False
    
    def end_quarter(self, eventstring:str) -> bool:
        if eventstring[1:4] == "end": 
            if eventstring[0].isnumeric() and eventstring[0] in {"1","2","3","4","5","6","7","8"}:
                self.quarter = eventstring[0]
                self.time = "0000"
                self.actionID = "end"
                return True
            return False
        return False
                
    def extract_eventstring(self, eventstring:str) -> bool:
        if self.start_quarter(eventstring): return True
        if self.end_quarter(eventstring): return True
        
        if not self.get_quarter(eventstring): return False
        if not self.get_time(eventstring): return False
        i = self.get_action(eventstring)
        if i==False: return False
        if self.actionID in {"ft", "r"}:
            if not self.get_player(eventstring, i):
                if not self.get_team(eventstring, i): return False
        elif self.actionID in {"j", "to"}:
            if not self.get_team(eventstring, i): return False
        else:
            j = self.get_player(eventstring, i)
            if j==False: return False
        if self.actionID in {"1m", "2m", "3m", "2", "3", "t"} and j > 1:
            if not self.get_action2(eventstring, i+j): return False
        if self.actionID == "out":
            if not self.get_substitute(eventstring, i+j): return False
        return True
    
    def print_score(self, lead:bool) -> {str, str}:
        if lead: 
            if self.lead == 0: return f"{self.score[0]}-{self.score[1]}", f"TIE"
            if self.lead > 0: return f"{self.score[0]}-{self.score[1]}", f"+{self.lead}"
            return f"{self.score[0]}-{self.score[1]}", f"{self.lead}"
        return f"{self.score[0]}-{self.score[1]}"
    
    def print_event(self, terms:object, lineup:list = None, lineup2:list = None) -> str:
        if self.actionID in {"j", "to"}:
            return f"{terms[self.actionID]}"
        if self.actionID == "ft" and self.playerID == None:
            return f"{terms[self.actionID]}"
        if self.actionID == "r" and self.playerID == None:
            return f"{terms[self.actionID]}"
        if self.actionID == "out":
            if lineup == None:
                return f"{terms[self.actionID]}: #{self.playerID} {terms[self.actionID2]} #{self.playerID2}"
            return f"{terms[self.actionID]}: {lineup.names[self.playerID]} {terms[self.actionID2]} {lineup.names[self.playerID2]}"
        if self.actionID in {'t', '2', '3'} and not self.actionID2 == None:
            if lineup == None:
                return f"#{self.playerID} {terms[self.actionID]}", f"#{self.playerID2} {terms[self.actionID2]}"
            return f"{lineup.names[self.playerID]} {terms[self.actionID]}", f"{lineup2.names[self.playerID2]} {terms[self.actionID2]}"
        if self.actionID in {'1', '2', '3'}:
            if lineup == None:
                return f"#{self.playerID} {terms[self.actionID]}"
            return f"{lineup.names[self.playerID]} {terms[self.actionID]}"
        if self.actionID in {'2m', '3m'} and not self.playerID2 == None:
            if lineup == None:
                return f"#{self.playerID} {terms[self.actionID]} (#{self.playerID2} {terms[self.actionID2]})"
            return f"{lineup.names[self.playerID]} {terms[self.actionID]} ({lineup.names[self.playerID2]} {terms[self.actionID2]})"
        elif self.actionID in {'2m', '3m'}:
            if lineup == None:
                return f"#{self.playerID} {terms[self.actionID]}"
            return f"{lineup.names[self.playerID]} {terms[self.actionID]}"
        if lineup == None:
            return f"#{self.playerID} {terms[self.actionID]}"
        return f"{lineup.names[self.playerID]} {terms[self.actionID]}"