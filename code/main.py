from event import event
from match import match
from stats import stats
from gamereport import gamereport
from rawstats import rawstats
from data import data
from copy import deepcopy
import os
import shutil

def prints(type:str):
    if type == "intro":
        print("\nOPTIONS")
        print("- create:\tcreate new match")
        print("- select:\tselect match")
        print("- data:\t\texport data of all matches as csv")
        print("- stats:\tsee all stats of certain team")
        print("- exit:\t\texit program")
    
    if type == "match":
        print("\nOPTIONS")
        print("- edit:\t\tedit match")
        print("- summary:\tview summary of match")
        print("- log:\t\tview gamelog of match")
        print("- box:\t\tview boxscore of match")
        print("- save:\t\tsave match as txt")
        print("- export:\texport stats of match as txt/pdf")
        print("- rawstats:\tsave rawstats of match in txt (sep=';')")
        print("- exit:\t\texit program")     
    
def main():
    eventstring = None
    while not eventstring in {"create", "select", "exit"}:
        prints("intro")
        eventstring = input()
        
        if eventstring == "create":
            m = match()
            m.create_match(input("game ID: "), 
                           input("home team: "), 
                           input("away team: "), 
                           input("date: "), 
                           input("time: "), 
                           input("location: "))
            b = False
            while not b:
                homeplayers = input("players (home)\n")
                awayplayers = input("players (away)\n")
                b = m.add_lineups(homeplayers.split(";"), awayplayers.split(";"))
            
            f = open(f"matches/history.txt", "w")
            f.writelines(m.matchID + '\n')
            f.writelines(m.home.name + '\n')
            f.writelines(m.away.name + '\n')
            f.writelines(m.date + '\n')
            f.writelines(m.time + '\n')
            f.writelines(m.location + '\n')
            f.writelines(homeplayers + '\n')
            f.writelines(awayplayers + '\n')
            f.close()
                                    
        elif eventstring == "select":
            matches = []
            for file in os.listdir("matches"):
                if file.endswith(".txt") and not file == "history.txt":
                    matches.append(file.split('.')[0])
                    print("game " + file.split('.')[0])
                    
            if len(matches) == 0: 
                print("no matches found")
                eventstring = None
            
            else:
                id = input("SELECT MATCH BY ID: ")
                
                if id in matches:
                    shutil.copyfile(f"matches/{id}.txt", "matches/history.txt") 
                            
                    f = open("matches/history.txt", "r")
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

                    print(f"selected match {id} with {n_events} written lines and {added_events} added events")
                    eventstring = "select"
                else:
                    print("invalid matchID")
                    eventstring = None

        elif eventstring == "data":
            d = data()
            d.read()
            d.add_data()
            d.export()
            
        elif eventstring == "stats":
            s = stats()
            s.load()
            s.select_team()
            s.team_stats()
            s.per_game()
            s.totals()   
            s.advanced()         
            exit()

        elif eventstring == "exit":
            exit()
                    
    while not eventstring in {"exit"}:
        
        prints("match")
        eventstring = input()
            
        if eventstring[:4] == "edit" and len(eventstring) == 5:            
            if m.events == None:
                m.start_match()
            
            quarter = eventstring[4]
            if not quarter in {"1","2","3","4","5","6","7","8"}: print("invalid quarter")
                
            e = event()
            b = e.extract_eventstring(eventstring)
            m.add_event(e)
                                
            f = open(f"matches/history.txt", "a")
            f.writelines(eventstring + '\n')
            f.close()
                
            if m.count_events(quarter) < 2:
                b = False
                while not b:
                    print("ADD STARTERS")
                    homestarters = input("home: ")
                    awaystarters = input("away: ")
                    b = m.add_starters(quarter, homestarters.split(","), awaystarters.split(","))
                    if b:  
                        f = open(f"matches/history.txt", "a")
                        f.writelines(f"H{str(homestarters)}" + '\n')
                        f.writelines(f"A{str(awaystarters)}" + '\n')
                        f.close()
                    
            print("ADD EVENTS (enter 'end' to stop)")
            while not eventstring == quarter + "end":
                eventstring = quarter + input(quarter)
                e = event()
                b = e.extract_eventstring(eventstring)
                if b:                    
                    m.add_event(e)

                    f = open(f"matches/history.txt", "a")
                    f.writelines(eventstring + '\n')
                    f.close()
                else:
                    del e
                    print("invalid event")
        
        if eventstring == "summary":
            if m.events == None or len(m.events) == 0:
                print("no events")
            else:
                # quarters = m.all_quarters()
                quarters = input("which quarter(s)? ").split(",")
                if all(quarter in m.all_quarters() for quarter in quarters):
                    m.print_summary(quarters)
                    
        if eventstring == "log":
            quarters = input("which quarter(s)? ").split(",")
            if m.events == None or len(m.events) == 0:
                print("no events")
            else:
                m.print_events(quarters)
            
        if eventstring == "box":
            if m.events == None or len(m.events) == 0:
                print("no events")
            else:
                quarters = input("which quarter(s)? ").split(",")
                m.print_boxscore(quarters)
            
        if eventstring == "save":
            if os.path.isfile(f"matches/{m.matchID}.txt"):
                print(f"match is already saved under {m.matchID}.txt")
                if input("overwrite existing file? (y/n) ") == "y":
                    shutil.copyfile("matches/history.txt", f"matches/{m.matchID}.txt") 
            else:
                shutil.copyfile("matches/history.txt", f"matches/{m.matchID}.txt") 

        if eventstring == "export":
            if input(f"want to make a game report of match {m.matchID}? (y/n) ") == "y":
                gamebook = gamereport(m)
                quarters = m.all_quarters()
                gamebook.make_txt(quarters)
                gamebook.make_pdf(quarters)

        if eventstring == "rawstats":
            rawstat = rawstats(m)
            rawstat.gameinfo()
            rawstat.create_boxscores()
            rawstat.save_teamstats()
            rawstat.save_playerstats()
                         
        if eventstring == "exit":
            exit()
            
if __name__ == '__main__':
    main()