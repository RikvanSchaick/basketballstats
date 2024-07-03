# Folder *code*

In deze folder zitten alle python-files die gebruikt zijn (of nog in de maak) voor de volgende functionaliteiten van het programma.

1. **Begin programma**: 
   Het opstarten van het programma via de terminal. Door `python3 code/main.py` te runnen in de juiste working directoy. 

    > **Files:**
    > 1. `main.py`: Geeft toegang tot alle functionaliteiten van het programma. 
   
2. **Game events**: 
   Het aanmaken/inladen van een wedstrijd, bijhouden van events in een wedstrijd, het zien van de boxscores and eventlogs in de terminal en het opslaan van de events data van de wedstrijd.

    > **Files:**
    > 1. `match.py`: Bevat de class *`match`* met alle functionaliteiten die behoren tot een wedstrijd. Deze class maakt gebruik van `event.py`, `boxscore.py`, `team.py` en `terminoligy.py`.
    > 2. `event.py`: Bevat de class *`event`* met alle functionaliteiten die behoren tot een enkele event in een wedstrijd. Deze class maakt gebruik van `terminoligy.py`. Een event in een wedstrijd is een enkele gebeurtenis op een bepaald tijdstip van de wedstrijd.
    > 3. `terminoligy.py`: Bevat verschillende string vertalingen van een specifieke term, in andere woorden, verschillende manieren om assist te printen.
    > 4. `boxscore.py`: Bevat de class *`boxscore`* met alle functionaliteiten die behoren tot een boxscore van een wedstrijd. Deze class maakt gebruik van `gamelog.py`, `team.py` en `terminoligy.py`. 
    > 5. `gamelog.py`: Bevat de class *`gamelog`* met alle functionaliteiten die behoren tot een gamelog van een wedstrijd. Denk aan het bijhouden van alle punten, fouten, schoten en andere statistieken in een wedstrijd.
    > 6. `team.py`: Bevat de class *`team`* met alle functionaliteiten die behoren tot een team van een wedstrijd. Deze class maakt gebruik van `lineup.py`. Denk aan welke spelers in een team zitten, welke spelers starten aan een wedstrijd, etc.
    > 7. `lineup.py`: Bevat de class *`lineup`* met alle functionaliteiten die behoren tot een lineup van een team van een wedstrijd. Denk aan het toevoegen van een speler aan een team voor een wedstrijd.

3. **Gamereports**: 
    Het aanmaken van txt- and pdf-files die informatie bevatten van de betreffende game, plus het opslaan van deze files.

    > **Files:**
    > 1. `gamereport.py`: Bevat de class *`gamereport`* met alle functionaliteiten die behoren tot het maken en opslaan van een verslag van een individuele wedstrijd. Denk aan het aanmaken van tabellen voor statistieken en het printen van de juiste events in de juiste volgorde. Deze class maakt gebruik van `match.py`, `boxscore.py`, `terminoligy.py` en `formulas.py`. 
    > 2. `formulas.py`: Bevat enkele formules die advanced statistieken berekenen.

4. **Statistieken**: 
    Het exporteren van alle data van de wedstrijden om vervolgens statistieken van elke wedstrijd te kunnen weergeven.

    > **Files:**
    > 1. `data.py`: Bevat de class *`data`* met alle functionaliteiten die behoren tot een wedstrijd. Deze class slaat de data van alle wedstrijden in de 'matches' folder op in drie verschillende csv-files. Deze class maakt gebruik van `match.py`, `event.py`, `boxscore.py` en `terminoligy.py`.
    > 2. `stats.py`: Bevat de class *`stats`* met alle functionaliteiten die behoren tot een wedstrijd. Deze class maakt gebruik van de drie csv-files gecreëerd door `data.py` en geeft de optie om per team, verschillende statistieken te weergeven. Deze class maakt gebruik van `formulas.py`.

5. **Scoreboard *(in progress...)***: 
   Het automatiseren van het scoreboard in thuiswedstrijden. Denk hierbij aan de tijd, te teamfouten, de score, etc...

    > **Files:**
    > 1. `scoreboard.py`: Bevat de class *`scoreboard`* met alle functionaliteiten die behoren tot het automatiseren van de gegevens uit het scoreboard van de Carla de Liefde hal. Functionaliteiten zijn nog niet af.
