from event import event
from match import match
from stats_export import statsreport
from gamereport import gamereport
# from rawstats import rawstats
from data_export import data
from copy import deepcopy
import os
import shutil
from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings

def prints(type:str):
    if type == "intro":
        print("\nOPTIONS")
        print("- create:\tcreate new match")
        print("- select:\tselect match")
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
        # print("- rawstats:\tsave rawstats of match in txt (sep=';')")
        print("- exit:\t\texit program")     
    
def event_input(quarter) -> None:
    f = open("matches/history.txt", "r")
    lines = f.readlines()
    f.close()
    counta = 0
    countb = 0
    default_text = f"{quarter}"

    bindings = KeyBindings()
    def update_defaulta():
        nonlocal default_text
        if counta > 0:
            default_text = lines[-counta].strip()
        else:
            default_text = f"{quarter}"

    def update_defaultb():
        nonlocal default_text
        if countb == 1:
            default_text = lines[-1].strip()[:5]
        elif countb == 2:
            default_text = lines[-1].strip()
        else:
            default_text = f"{quarter}"

    @bindings.add('up')
    def _(event):
        nonlocal counta
        nonlocal countb
        if counta < len(lines):
            countb = 2
            counta += 1
            update_defaulta()
            event.app.current_buffer.text = default_text
            event.app.current_buffer.cursor_position = len(default_text)

    @bindings.add('down')
    def _(event):
        nonlocal counta
        nonlocal countb
        if counta > 1:
            countb = 2
        elif counta == 1:
            countb = 0
        if counta > 0:
            counta -= 1
            update_defaulta()
            event.app.current_buffer.text = default_text
            event.app.current_buffer.cursor_position = len(default_text)
            
    @bindings.add('tab')
    def _(event):
        nonlocal counta
        nonlocal countb
        countb += 1
        countb = countb % 3
        update_defaultb()
        event.app.current_buffer.text = default_text
        event.app.current_buffer.cursor_position = len(default_text)
        if countb == 2:
            counta = 1
        else:
            counta = 0

    eventstring = prompt(default=default_text, key_bindings=bindings)
    return eventstring
    
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
                           input("location: "),
                           True)
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
                    f.close()
                    
                    m = match()
                    m.create_match(lines[0],
                                   lines[1],
                                   lines[2],
                                   lines[3],
                                   lines[4],
                                   lines[5],
                                   True)
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
            
        elif eventstring == "stats":
            d = data()
            if not d.n_exports():
                d.read(prnt=False)
                d.add_data()
                d.export()
            
            s = statsreport()
            s.make_pdf()
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
               
            # check of laatste line het einde was van hetzelfde kwart 
            f = open(f"matches/history.txt", "r")
            lines = f.readlines()
            lastline = lines[-1]
            if lastline[:-1] == (f"{quarter}end"):
                f.close()
                # laatste line verwijderen
                f = open("matches/history.txt", 'w')
                for line in lines[:-1]:
                    f.writelines(line)
                f.close()
            else:
                f.close()
                f = open(f"matches/history.txt", "a")
                f.writelines(eventstring + '\n')
                f.close()
            
            e = event()
            b = e.extract_eventstring(eventstring)
            m.add_event(e)

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
                eventstring = event_input(quarter)
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
            
            # Read file opnieuw om met de hand gefixte dingen in history.txt mee te nemen in de check
            f = open("matches/history.txt", "r")
            lines = f.read().splitlines()
            f.close()
            
            m = match()
            m.create_match(lines[0],
                            lines[1],
                            lines[2],
                            lines[3],
                            lines[4],
                            lines[5],
                            False)

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
            
            quarters = m.all_quarters()
            if m.check_boxscore(quarters)==True: print("exited succesfully")
        
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
                if m.check_boxscore(quarters)==True: m.print_boxscore(quarters)
            
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

        # if eventstring == "rawstats":
        #     rawstat = rawstats(m)
        #     rawstat.gameinfo()
        #     rawstat.create_boxscores()
        #     rawstat.save_teamstats()
        #     rawstat.save_playerstats()
                         
        if eventstring == "exit":
            exit()
            
if __name__ == '__main__':
    main()