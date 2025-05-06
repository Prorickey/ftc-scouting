#!/usr/bin/env python3
import sqlite3
import requests
from requests.auth import HTTPBasicAuth
from dotenv import dotenv_values
from pathlib import Path
import database

__auth = None

def init():
    """
    Reads config files from .env and sets up authentication.
    """
    global __auth
    # Load secrets from .env file
    # Required secrets: USERNAME, TOKEN
    # Used to interact with the FTC Event API
    script_dir = Path(__name__).resolve().parent
    config = dotenv_values(dotenv_path=script_dir/".env")

    if "USERNAME" not in config:
        raise ValueError("USERNAME not provided in .env")
    if "TOKEN" not in config:
        raise ValueError("TOKEN not provided in .env")
    
    __auth = HTTPBasicAuth(username=config["USERNAME"], password=config["TOKEN"])

    database.init()

def cache_scores(event_code: str, season: int = 2024, qual_matches: bool = True) -> bool:
    """
    Retrieves match scores from the FTC Event API and caches them in the local SQL database.

    Args:
        event_code: the event code of the event to retrieve data for (e.g. FTCCMP1OCHO)
        season: the year that the event happened
        qual_matches: True = get qualification match data, False = get elimination match data
    
    Returns True if success, False if there was an error.
    """

    season = int(season)
    # JUST URLENCODE IT
    if not event_code.replace("'", "").replace("-", "").replace("(","").replace(")","").isalnum():
        return False
    
    if __auth is None:
        return False
    
    try:
        score_data = requests.get(f"https://ftc-api.firstinspires.org/v2.0/{season}/scores/{event_code}/{'qual' if qual_matches else 'playoff'}", auth=__auth).json()
    except:
        return False

    is_good = True
    for match_score in score_data['matchScores']:
        is_good = is_good and database.store_match_score(event_code, match_score, season=season)

    return is_good

def cache_matches(event_code: str, season: int = 2024) -> bool:
    """
    Retrieves matches (i.e. participating teams, final scores, start times, etc) from the FTC Event API and caches them in the local SQL database.

    Args:
        event_code: the event code of the event to retrieve data for (e.g. FTCCMP1OCHO)
        season: the year that the event happened
    
    Returns True if success, False if there was an error.
    """

    season = int(season)
    # JUST URLENCODE IT
    if not event_code.replace("'", "").replace("-", "").replace("(","").replace(")","").isalnum():
        return False
    
    if __auth is None:
        return False
    
    try:
        match_data = requests.get(f"https://ftc-api.firstinspires.org/v2.0/{season}/matches/{event_code}", auth=__auth).json()
    except:
        return False

    is_good = True
    for match in match_data['matches']:
        is_good = is_good and database.store_match(event_code, match, season=season)

    return is_good

def cache_schedule(event_code: str, season: int = 2024, qual_matches: bool = True) -> bool:
    """
    Retrieves schedule data from the FTC Event API and caches it in the local SQL database.

    Args:
        event_code: the event code of the event to retrieve data for (e.g. FTCCMP1OCHO)
        season: the year that the event happened
        qual_matches: True = get qualification match schedule, False = get elimination match schedule
    
    Returns True if success, False if there was an error.
    """

    season = int(season)
    # JUST URLENCODE IT
    if not event_code.replace("'", "").replace("-", "").replace("(","").replace(")","").isalnum():
        return False
    
    if __auth is None:
        return False
    
    try:
        schedule_data = requests.get(f"https://ftc-api.firstinspires.org/v2.0/{season}/schedule/{event_code}?tournamentLevel={'qual' if qual_matches else 'playoff'}", auth=__auth).json()
    except:
        return False

    is_good = True
    for match in schedule_data['schedule']:
        is_good = is_good and database.store_scheduled_match(event_code, match, season=season)

    return is_good

def get_all_events(season: int = 2024) -> list[str]:
    """
    Retrieves a list of all event codes for a given season from the FTC Event API.

    Args:
        season: the year to look for events in
    
    Returns a list of event codes for `season` if successful, and an empty list if there was an error.
    """
    season = int(season)

    if __auth is None:
        return []
    
    try:
        event_listings_data = requests.get(f"https://ftc-api.firstinspires.org/v2.0/{season}/events", auth=__auth).json()
    except:
        return []
    
    try:
        return list(map(lambda event: event["code"], event_listings_data["events"]))
    except:
        return []

import time

# Failed after 193 events on "NL'HKO"
# Stopping after ROCMP
# Failed at tempclone-1693972074

def cache_all_events(season: int = 2024) -> bool:
    # event_codes = get_all_events(season)
    event_codes = ['USMNVAV2', 'USMIAAV', 'USNJSOPD', 'USNYEXUTKO', 'USAKFAKO', 'GBHUS', 'USNDBIKO', 'USPALAWS', 'USMITCOS3', 'USARLRAS', 'USMIUCOS', 'USTXSAS1', 'USTXLUV', 'USCHSHAKO', 'USCANOSJWS', 'USCTSOS1', 'USFLPLKO', 'USNVLVS', 'USMITEKO', 'USPAPHWS2', 'USMIFRKO', 'GBBES1', 'USMIFRKO2', 'USOKADS', 'USCHSBEKO', 'USARTBS', 'FPEMX', 'USTXREV', 'GBBES2', 'USTNKNKO', 'USSCCOS', 'USMNVAV', 'USILCHKO', 'USMANAKO', 'USORPOWS1', 'USMNAVS', 'USNYEXBUKO', 'USMIHOKO2', 'USCANOSJV', 'USMICAKO', 'USNJPHS2', 'USFLDBKO', 'FPEEU', 'USDEDOS', 'USPALAWS7', 'GBBOS', 'USMSGUPD1', 'USTXHAS', 'USIACRKO', 'BRREOS', 'USNYEXCOKO', 'USNYEXPEKO', 'USMILAV', 'USFLJAKO', 'USMOKSCHKO', 'USMIAAOS', 'USMIMCKO', 'USKYRAKO', 'USORHIKO', 'USOKMUKO', 'USPAEXKO', 'GBEDS1', 'USNDFAKO', 'USNJPHV', 'USIADMS', 'FPERR', 'USCALAMOKO', 'USNYNYNYWS3', 'USCOLOS', 'GBGLS', 'USFLBRS', 'USCOLIKO', 'USTNNAKO', 'USILEDKO', 'USSCCHS', 'USNVLVWS2', 'USILPEKO', 'USGAATKO', 'USVTM(KO', 'FPECRI', 'USMIPOOS', 'USCASDSDKO', 'USNHNAS', 'USNVREWS2', 'USFLFLS', 'USGAWRKO', 'USPAPHWS3', 'USTXFMV', 'USLATBKO', 'USPALAWS6', 'USNJUNWS', 'TRSIKO', 'USKYBGKO', 'USMOKSROKO', 'USCODEWS', 'USNVLVKO', 'GBCMP', 'USCASDDMOS', 'USALHUDE', 'GBOMS', 'USMILOKO', 'USWIMUOS', 'USNMALKO', 'NLROS', 'USNYNYNYWS6', 'CAABEDKO', 'USCALSLAS', 'USWIMAKO2', 'GBABS', 'USMIDEV', 'USMSOXS1', 'USOKOCS2', 'USTXAUS', 'USILSCKO', 'USCTSTOS1', 'USOHAUOS', 'USMIMAKO2', 'USAKFAKO2', 'LYBEKO', 'CABCVAKO', 'USALHUKO', 'USDEWIS2', 'USSCGRS', 'CAABCAKO', 'USMIMDM1', 'USNJETWS', 'USCHSCHKO', 'USINBLKO', 'ZATZS', 'USTXCCOS2', 'USOKALS', 'USFLORKO', 'GBBRS', 'CABCVIV', 'USFLNIKO', 'CAABEDOS', 'USORROKO', 'USTXCCOS3', 'USCOGRS', 'USPAYOKO', 'USWARIKO', 'GBCHS', 'USMIPOV', 'USTXLUV2', 'USMSPEPD1', 'USNDBIWS', 'ITBOKO', 'USDEDOKO', 'USTXATKO', 'USWIMAKO', 'USMITCKO', 'USMSFLKO', 'USAZTEKO', 'GBLOKO', 'USRIPRKO', 'USNCDUOS', 'USCHSRIKO', 'USMOKSKCKO', 'USWIMIKO', 'USOHDAKO', 'ROBUKO', 'USOHLOKO', 'USSCCOKO', 'USMOKSSLKO', 'USINWLKO', 'USMINBKO', 'USTXAUS2', 'USFLSEKO', 'USMITCOS', 'USARBEKO', 'USPALAWS2', 'USTXLUS3', 'USNDBIWS2', 'USNYNYNYS1', 'USTXFMS', 'USAKJUS1', 'CABCVIS1', 'USNYEXPOKO', "NL'HKO", 'USNVREKO', 'USVTSBKO', 'USMITCOS1', 'USMIAAKO', 'USIANOKO', 'USCOFCS', 'USIDFIKO', 'USFLFMS', 'USAKANKO', 'USIDJES', 'USNJPHS1', 'USTXWAS', 'USTXAUKO', 'USDEWIS4', 'USMITCOS2', 'USWABOS1', 'tempclone-1693972074', 'USILRIKO', 'USTXCCOS4', 'USNYNYNYWS1', 'USPAKSKO', 'CABCVIWS', 'USIACOS', 'USOHKIKO', 'USMOKSKNKO', 'USIATASM7', 'USMOKSCNTM6', 'GBOXS', 'USIACRS1', 'USNYNYNYWS2', 'USMOKSCGKO', 'USTXFMOS', 'USWYCAS', 'USTXCCOS5', 'USHIKAKO', 'USNMALKO2', 'USNYLISBKO', 'USNYNYNYWS5', 'USTXFTKO', 'BRRJQ', 'USTXHOSPDE', 'USNVLVWS1', 'GBGLS2', 'LYSAKO', 'USNJLIKO', 'GBLOS', 'USCHSLAKO', 'USMINOKO', 'USNJMHPD', 'USORROS', 'GBBIS', 'LYTOKO', 'USMOKSSPKO', 'USOKMUOS', 'USALORWS', 'USMSOXV', 'LYBAKO', 'USNJETPD', 'USNJNEPD', 'USPALAWS4', 'USTXODS', 'USFLWPKO', 'USARBEOS', 'GBLIS', 'USFLTAS', 'USMIBHKO', 'CAONPIV', 'USWAAUKO', 'USMITRV', 'FPEMI', 'USTXHOSLS', 'USCHSMCKO', 'USPALAWS5', 'USIAICV', 'USMIHOKO', 'USNJBRDE', 'LYTRKO', 'USNYNYNYWS7', 'USCOLAS', 'USINOSKO', 'USNJTEPD', 'USOHNEKO', 'AUWES', 'USFLROWS', 'USMIMAKO', 'USNHWOS', 'USOHSHOS', 'USNYEXBSKO', 'USILWCKO', 'USNHWIS', 'GBHES', 'USMIFLKO', 'USAKJUKO', 'USNJHPPD', 'USFLTAKO', 'USPAPHKO', 'USTXWAKO', 'USCASDSDV1', 'USIAICWS', 'USMOKSSCKO', 'USOREUKO', 'USIDMEKO', 'USMIDEOS', 'USCHSLAKO1', 'FPECA', 'USCOGJS', 'ROBUOS1', 'GBEDS', 'USMNBLKO', 'USTXSAKO', 'USIABERM3', 'USTXHOPAS1', 'USALHUV', 'USNJHIKO', 'USNHMAKO', 'USPAPHWS4', 'USIAWMS', 'USINAVKO', 'GBSTS', 'USMIUCV', 'USPALAKO', 'USILROKO', 'USTXLUKO', 'USNYNYNYWS4', 'USMTKAKO', 'USTXCCKO', 'USORLOKO', 'CABCVIS2', 'USAKJUS2', 'USDEWIS3', 'RONM6', 'FPECR', 'USOKOCKO', 'USTXPLV', 'USCANOSMOS', 'USTXAUS3', 'USWABEKO', 'USIAICS', 'USWAKEV', 'USCHSDCKO', 'USCHSNOKO', 'ROSM10', 'USCALAOJKO', 'USALHUS', 'USMOKSCAKO', 'USDEWIS1', 'USCOMOS', 'USWAOLKO', 'USPALAWS3', 'USCALAWIKO', 'USTXSAOS1', 'USPALAWS1', 'GBSUS', 'USPAMAKO', 'USFLORS', 'GBSTS2', 'USMITROS', 'USNVREWS1', 'NFSJS', 'USOKOCS1', 'USPAPHWS1', 'USMIOCM1', 'USWALLKO']

    print(f"Preparing to cache {len(event_codes)} events")

    if event_codes == []:
        return False
    
    for code in event_codes:
        print(f"Caching qual scores from {code}")
        if not cache_scores(code, season, qual_matches=True): return False
        print(f"Caching elim scores from {code}")
        if not cache_scores(code, season, qual_matches=False): return False
        print(f"Caching qual schedule from {code}")
        if not cache_schedule(code, season, qual_matches=True): return False
        print(f"Caching elim schedule from {code}")
        if not cache_schedule(code, season, qual_matches=False): return False
        print(f"Caching matches from {code}")
        if not cache_matches(code, season): return False
        print("-------------------------------------")
    
    return True