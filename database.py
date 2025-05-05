from queue import Queue
import secrets
import sqlite3
import hashlib
import string
from functools import reduce
from helper import *

schema_file = "schema.sql"

# Connection pool for SQLite database connections
# I had to do this because flask is handling my requests 
# on seperate threads. This solution helps avoid using one
# connection on different threads and allows my application
# to scale better
__connection_pool = Queue(maxsize=5)
for _ in range(5):
    __connection_pool.put(sqlite3.connect("database.db", check_same_thread=False))

def get_connection() -> sqlite3.Connection:
    return __connection_pool.get()

def release_connection(connection: sqlite3.Connection):
    __connection_pool.put(connection)

def init():
    """
    Connect to the SQLite database and create the tables if they don't exist.
    """

    conn = get_connection()
    try:
        # This just creates all the tables that are defined in the schema file
        with open(schema_file) as f:
            schema = f.read()

        conn.executescript(schema)
        conn.commit()
    finally:
        release_connection(conn)

def login(email: str, password: str) -> int:
    """
    Login a user with the given email and password.
    """

    # Grab a connection from the pool
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT password, salt, rowid FROM users WHERE email=?", (email.lower(),))
        user = cursor.fetchone()

        if user is None:
            return None
        
        print(user)
        
        password_digest = user[0]
        password_salt = user[1]

        # Hash the password with the salt
        hashed_password = hashlib.sha256((password_salt + password).encode()).hexdigest()

        if hashed_password == password_digest:
            return int(user[2])
    finally:
        # Release the connection back to the pool
        release_connection(conn)

    return None


def register(email: str, password: str, name: str) -> int:
    """
    Register a new user with the given email and password. If the email is already taken, false will be returned.
    """

    # Grab a connection from the pool
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=?", (email.lower(),))
        existing_user = cursor.fetchone()

        if existing_user is not None:
            return None

        # Generate a random salt
        salt = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))

        # Hash the password with the salt
        hashed_password = hashlib.sha256((salt + password).encode()).hexdigest()

        # Insert the new user into the database
        cursor.execute("INSERT INTO users (email, name, password, salt) VALUES (?, ?, ?, ?)", (email.lower(), name, hashed_password, salt))
        id = cursor.lastrowid
        conn.commit()
        return id
    finally:
        # Release the connection back to the pool
        release_connection(conn)

def store_match_score(event_code: str, score_data: dict, season: int = 2024) -> bool:
    """
    Saves latest match score details. If we already have old data for the match, it will be overwritten.

    Args:
        event_code: the code of the event that this match is part of
        score_data: the dictionary storing the JSON data from a single match, obtained from the FTC Event API
        season: the year the event happened
    
    Returns True if the operation succeeded, False if it failed.
    """
    if season != 2024:
        # Every year has a unique score format. Only 2024-2025 is supported for now.
        return False
    
    # Grab a connection from the pool
    conn = get_connection()
    try:
        cursor = conn.cursor()
        allianceScores = score_data['alliances']
        for alliance in ["Red", "Blue"]:
            this_alliance: dict = next(filter(lambda allianceScore: allianceScore['alliance'] == alliance, allianceScores))

            individual_alliance_keys = ['alliance', 'team', 'robot1Auto', 'robot2Auto', 'autoSampleNet', 'autoSampleLow', 'autoSampleHigh', 'autoSpecimenLow', 'autoSpecimenHigh', 'teleopSampleNet', 'teleopSampleLow', 'teleopSampleHigh', 'teleopSpecimenLow', 'teleopSpecimenHigh', 'robot1Teleop', 'robot2Teleop', 'minorFouls', 'majorFouls', 'autoSamplePoints', 'autoSpecimenPoints', 'teleopSamplePoints', 'teleopSpecimenPoints', 'teleopParkPoints', 'teleopAscentPoints', 'autoPoints', 'teleopPoints', 'endGamePoints', 'foulPointsCommitted', 'preFoulTotal', 'totalPoints']
            individual_alliance_values = [this_alliance[key] for key in individual_alliance_keys]

            query = f"INSERT OR REPLACE INTO scores (season, eventCode, matchLevel, matchSeries, matchNumber, {', '.join(individual_alliance_keys)}) VALUES (?, ?, ?, ?, ?, {', '.join(['?']*len(individual_alliance_keys))})"

            cursor.execute(query,
                           (season, event_code, score_data["matchLevel"], score_data["matchSeries"], score_data["matchNumber"], *individual_alliance_values))

            conn.commit()
    finally:
        # Release the connection back to the pool
        release_connection(conn)
    
    return True

def store_match(event_code: str, match_data: dict, season: int = 2024) -> bool:
    """
    Saves latest match details. If we already have old data for the match, it will be overwritten.

    Args:
        event_code: the code of the event that this match is part of
        score_data: the dictionary storing the JSON data from a single match, obtained from the FTC Event API
        season: the year the event happened
    
    Returns True if the operation succeeded, False if it failed.
    """
    if season != 2024:
        # Every year has a unique score format. Only 2024-2025 is supported for now.
        return False
    
    # Grab a connection from the pool
    conn = get_connection()
    try:
        cursor = conn.cursor()
        teams = match_data['teams']

        match_keys = ["actualStartTime","description","tournamentLevel","series","matchNumber","scoreRedFinal","scoreRedFoul","scoreRedAuto","scoreBlueFinal","scoreBlueFoul","scoreBlueAuto","postResultTime","modifiedOn"]
        match_values = [match_data[key] for key in match_keys]

        for team in teams:
            query = f"INSERT OR REPLACE INTO matches (season, eventCode, teamNumber, station, dq, onField, {', '.join(match_keys)}) VALUES (?, ?, ?, ?, ?, ?, {', '.join(['?']*len(match_keys))})"

            cursor.execute(query,
                           (season, event_code, team["teamNumber"], team["station"], team["dq"], team["onField"], *match_values))

            conn.commit()
    finally:
        # Release the connection back to the pool
        release_connection(conn)
    
    return True

# This example query gets the number of points that 22377's alliance scored in every match they played that is in the database
# SELECT scores.totalPoints FROM scores INNER JOIN matches ON scores.season=matches.season AND scores.eventCode=matches.eventCode AND scores.matchLevel=matches.tournamentLevel AND scores.matchSeries=matches.series AND scores.matchNumber=matches.matchNumber AND INSTR(matches.station, scores.alliance) > 0 WHERE matches.teamNumber=22377;

def store_new_team(name: str, number: int, created_by_id: int) -> bool:
    # Grab a connection from the pool
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM teams WHERE team_number=?", (number,))
        existing_user = cursor.fetchone()

        if existing_user is not None:
            return False

        # Insert the new user into the database
        cursor.execute("INSERT INTO teams (name, team_number) VALUES (?, ?)", (name, number,))
        team_id = cursor.lastrowid

        if team_id is None: # Ideally, should never happen
            print("ERROR: Storing a new team returned no id")
            return False
        
        cursor.execute("INSERT INTO users_teams (user_id, team_id, role) VALUES (?, ?, 1)", (created_by_id, team_id,))
        conn.commit()
    finally:
        # Release the connection back to the pool
        release_connection(conn)

    return True

def store_scheduled_match(event_code: str, scheduled_match_data: dict, season: int = 2024) -> bool:
    """
    Saves latest scheduled matches. If we already have old data for the match, it will be overwritten.

    Args:
        event_code: the code of the event that this match is part of
        score_data: the dictionary storing the JSON data from a single scheduled match, obtained from the FTC Event API
        season: the year the event happened
    
    Returns True if the operation succeeded, False if it failed.
    """
    if season != 2024:
        # Every year has a unique score format. Only 2024-2025 is supported for now.
        return False
    
    # Grab a connection from the pool
    conn = get_connection()
    try:
        cursor = conn.cursor()
        teams = scheduled_match_data['teams']

        scheduled_match_keys = ["description","field","tournamentLevel","startTime","series","matchNumber","modifiedOn"]
        scheduled_match_values = [scheduled_match_data[key] for key in scheduled_match_keys]

        for team in teams:
            query = f"INSERT OR REPLACE INTO schedule (season, eventCode, teamNumber, displayTeamNumber, station, team, teamName, surrogate, noShow, {', '.join(scheduled_match_keys)}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, {', '.join(['?']*len(scheduled_match_keys))})"

            cursor.execute(query,
                           (season, event_code, team["teamNumber"], team["displayTeamNumber"], team["station"], team["team"], team["teamName"], team["surrogate"], team["noShow"], *scheduled_match_values))

            conn.commit()
    finally:
        # Release the connection back to the pool
        release_connection(conn)
    
    return True

class MatchKey:
    event_code: str
    match_level: str
    match_series: int
    match_number: int
    alliance: str
    season: int = 2024

    def __init__(self, event_code: str, match_level: str, match_series: int, match_number: int, alliance: str, season: int = 2024):
        self.event_code = event_code
        self.match_level = match_level
        self.match_series = match_series
        self.match_number = match_number
        self.alliance = alliance
        self.season = season

    def __repr__(self) -> str:
        return f'MatchKey(event_code="{self.event_code}", match_level="{self.match_level}", match_series={self.match_series}, match_number={self.match_number}, alliance="{self.alliance}", season={self.season})'
    
    def __hash__(self) -> int:
        return self.__repr__().__hash__()
    
    def __eq__(self, other) -> bool:
        return self.__hash__() == other.__hash__()

def get_match_scores(event_code: str, season: int = 2024) -> dict[MatchKey, dict[str, Any]]:
    """
    Gets all score statistics from every match at the event for the given season.

    Args:
        event_code: the event code for matches to be retrieved
        season: the season the event happened in
    
    Returns a dictionary storing match statistics, or an empty dictionary if there was an error.
        Key: a MatchKey
        Value: dictionary where key = statistic (from FTC event API) and value = its value
    """
    fields = ['robot1Auto', 'robot2Auto', 'autoSampleNet', 'autoSampleLow', 'autoSampleHigh', 'autoSpecimenLow', 'autoSpecimenHigh', 'teleopSampleNet', 'teleopSampleLow', 'teleopSampleHigh', 'teleopSpecimenLow', 'teleopSpecimenHigh', 'robot1Teleop', 'robot2Teleop', 'minorFouls', 'majorFouls', 'autoSamplePoints', 'autoSpecimenPoints', 'teleopSamplePoints', 'teleopSpecimenPoints', 'teleopParkPoints', 'teleopAscentPoints', 'autoPoints', 'teleopPoints', 'endGamePoints', 'foulPointsCommitted', 'preFoulTotal', 'totalPoints']
    # SELECT * FROM scores INNER JOIN matches ON scores.season=matches.season AND scores.eventCode=matches.eventCode AND scores.matchLevel=matches.tournamentLevel AND scores.matchSeries=matches.series AND scores.matchNumber=matches.matchNumber AND INSTR(matches.station, scores.alliance) > 0;
    
    # Grab a connection from the pool
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = f"SELECT matchLevel, matchSeries, matchNumber, alliance, {', '.join(fields)} FROM scores WHERE eventCode=? AND season=?"

        cursor.execute(query, (event_code, season))

        scores = cursor.fetchall()

        return {MatchKey(event_code=event_code, match_level=score[0], match_series=score[1], match_number=score[2], alliance=score[3], season=season): {fields[i]: score[4+i] for i in range(len(fields))} for score in scores}
    except Exception as e:
        print(e)
        return {}
    finally:
        # Release the connection back to the pool
        release_connection(conn)

def get_match_teams(event_code: str, season: int = 2024) -> dict[MatchKey, dict[int, tuple[str, bool]]]:
    """
    Retrieves teams playing in each match.

    Args:
        event_code: the event code for matches to be retrieved
        season: the season the event happened in
    
    Returns a dictionary storing teams playing in each match, or an empty dictionary if there was an error.
        Key: a MatchKey
        Value: dictionary where the key is the team number and the value is a tuple (station, on_field)
    """

    # SELECT eventCode, tournamentLevel, series, matchNumber, teamNumber, station, onField FROM matches WHERE eventCode="FTCCMP1OCHO"
    # Grab a connection from the pool
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = f"SELECT eventCode, tournamentLevel, series, matchNumber, teamNumber, station, onField FROM matches WHERE eventCode=? AND season=?"

        cursor.execute(query, (event_code, season))

        matches = cursor.fetchall()

        individual_dicts = [{MatchKey(event_code, match_level, match_series, match_number, alliance=station[:-1], season=season): {team_number: (station, on_field)}}
                            for (event_code, match_level, match_series, match_number, team_number, station, on_field) in matches]
        
        return reduce(lambda current_dict, new_dict: merge_with(merge_left, current_dict, new_dict), individual_dicts)
    except:
        return {}
    finally:
        # Release the connection back to the pool
        release_connection(conn)