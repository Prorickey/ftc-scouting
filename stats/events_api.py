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

def cache_all_events(season: int = 2024) -> bool:
    """
    Caches data from all events for a given season (needed for EPA calculations).

    Takes a long time.
    """
    event_codes = get_all_events(season)

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