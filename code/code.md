# Folder *code*

In deze folder zitten alle python-files die gebruikt zijn (of nog in de maak) voor de volgende functionaliteiten van het programma.

1. **Begin programma**: 
   Het opstarten van het programma via de terminal. Door `python3 code/main.py` te runnen in de juiste working directoy. 

    > **Files:**
    > 1. `main.py`: Geeft toegang tot alle functionaliteiten van het programma. 
   
   Optionele argumenten voor de gameclock-autofill (zie punt 6): `--csv`, `--anchor-clock`, `--anchor` en `--no-video-clock`.

2. **Game events**: 
   Het aanmaken/inladen van een wedstrijd, bijhouden van events in een wedstrijd, het zien van de boxscores and eventlogs in de terminal en het opslaan van de events data van de wedstrijd.

    > **Files:**
    > 1. `match.py`: Bevat de class *`match`* met alle functionaliteiten die behoren tot een wedstrijd. Deze class maakt gebruik van `event.py`, `boxscore.py`, `team.py` en `terminoligy.py`.
    > 2. `event.py`: Bevat de class *`event`* met alle functionaliteiten die behoren tot een enkele event in een wedstrijd. Deze class maakt gebruik van `terminoligy.py`. Een event in een wedstrijd is een enkele gebeurtenis op een bepaald tijdstip van de wedstrijd.
    > 3. `terminoligy.py`: Bevat verschillende string vertalingen van een specifieke term, in andere woorden, verschillende manieren om assist te printen.
    > 4. `boxscore.py`: Bevat de class *`boxscore`* met alle functionaliteiten die behoren tot een boxscore van een wedstrijd. Deze class maakt gebruik van `gamelog.py`, `team.py` en `terminoligy.py`. 
    > 5. `gamelog.py`: Bevat de class *`gamelog`* met alle functionaliteiten die behoren tot een gamelog van een wedstrijd. Denk aan het bijhouden van alle punten, fouten, schoten en andere statistieken in een wedstrijd.
    > 6. `team.py`: Bevat de class *`team`* met alle functionaliteiten die behoren tot een team van een wedstrijd. Deze class maakt gebruik van `players.py`. Denk aan welke spelers in een team zitten, welke spelers starten aan een wedstrijd, etc.
    > 7. `players.py`: Bevat de class *`players`* met alle functionaliteiten die behoren tot de spelers van een team van een wedstrijd. Denk aan het toevoegen van een speler aan een team voor een wedstrijd.

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

6. **Gameclock uit video**: 
   Het automatisch invullen van de tijd van een event, op basis van de video die open staat in QuickTime Player. In edit-mode (`edit1` t/m `edit8`) wordt de speelklok van de video automatisch als tijd van de event gebruikt, zodat alleen de actie nog getypt hoeft te worden.

    > **Files:**
    > 1. `gameclock.py`: Bevat de class *`GameClockTracker`*, die op de achtergrond de afspeelpositie van QuickTime Player uitleest en die via een CSV-log omzet naar de speelklok. De omzetting naar de vier cijfers van `event.get_time()` gebeurt in `clock_to_event_time()`. Deze class maakt gebruik van `quicktime_timestamp/tracker.py`.

   Werking en instellingen:

   - De klok wordt opgezet bij het betreden van het eerste edit-kwart, zodat een wedstrijd eerst aangemaakt/geselecteerd kan worden.
   - Bij **elk** `edit<N>`-commando wordt gevraagd of de video opnieuw gelijkgezet moet worden: `Sync video for quarter N? (y/n):`. Alleen een getypte `y` start het synchroniseren; bij `n`, een lege regel of wat dan ook blijft de bestaande synchronisatie van kracht voor dat kwart.
   - Bij een `y` wordt gevraagd de video op het beeld te zetten waar de speelklok van dát kwart voor het eerst `09:59` toont (`04:59` bij een verlenging van vijf minuten), en daarna op Enter te drukken. Het juiste beeld wordt per kwart uit de `period`-kolom van de CSV gehaald.
   - Is er nog geen synchronisatie, of staat er een andere video open in QuickTime Player, dan wordt er niet gevraagd maar meteen gesynchroniseerd — zonder offset valt er immers niets te behouden.
   - Met `--anchor`, zonder terminal of met `--no-video-clock` wordt de vraag overgeslagen.
   - De CSV heeft een optionele `period`-kolom met per regel het kwartnummer (`1`, `2`, …) of de context (`Pregame`, `Timeout`, `Break`, `Half Time`). Tijdens een onderbreking logt `game_clock` de aftelklok van die onderbreking zelf; de speelklok is dan de laatste waarde van het kwart dat onderbroken werd, en dát is wat er wordt ingevuld.
   - Staat de video in een ánder kwart dan het kwart dat je aan het invoeren bent, dan wordt er geen tijd ingevuld en blijft alleen het kwartcijfer staan. Dat is het signaal dat er opnieuw gesynchroniseerd moet worden.
   - De tijd wordt live bijgewerkt in de invoerregel zelf: de eerste vijf tekens (kwart + MMSS) volgen de video zolang de prompt open staat, dus de opgeslagen tijd is de speelklok op het moment van Enter. Pauzeer de video op de actie om een exacte tijd vast te leggen.
   - Alleen die vijf tekens veranderen; de actiecode die je typt blijft staan, net als de cursorpositie.
   - Pas je de tijd zelf aan, dan stoppen de automatische updates voor die regel. Wijzigingen in de actiecode doen dat niet.
   - Zonder QuickTime, zonder geldige mapping of met `--no-video-clock` blijft alles handmatig; pijltjestoetsen en Tab werken ongewijzigd. Een CSV zonder `period`-kolom blijft werken zoals voorheen.
   - Tests staan in `tests/test_gameclock.py` (mapping, `period`-kolom en kwart-anchors), `tests/test_quarter_sync.py` (de sync-vraag per kwart) en `tests/test_event_input.py` (live invoerregel).
