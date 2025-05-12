from queue import Queue
import secrets
import sqlite3
import hashlib
import string
from functools import reduce
from helper import *
import time

from R import Team, UserTeam

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

def store_new_team(name: str, number: int, created_by_id: int) -> Team:
    # Grab a connection from the pool
    conn = get_connection()
    try:
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute("SELECT * FROM teams WHERE team_number=?", (number,))
        existing_user = cursor.fetchone()

        if existing_user is not None:
            return None
        
        code = generate_code()

        # Insert the new user into the database
        cursor.execute("INSERT INTO teams (name, team_code, team_number) VALUES (?, ?, ?)", (name, code, number,))
        team_id = cursor.lastrowid

        if team_id is None: # Ideally, should never happen
            print("ERROR: Storing a new team returned no id")
            return None
        
        print(team_id, created_by_id)
        cursor.execute("UPDATE users SET team_id=?, team_role=1 WHERE rowid=?", (team_id, created_by_id,))
        conn.commit()
        return {'id': cursor.lastrowid, 'name': name, 'code': code}
    finally:
        # Release the connection back to the pool
        release_connection(conn)

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

    def __init__(self, event_code: str, match_level: str, match_series: int, match_number: int, alliance: str, season: int = 2024, start_time: float = None):
        self.event_code = event_code
        self.match_level = match_level
        self.match_series = match_series
        self.match_number = match_number
        self.alliance = alliance
        self.season = season
        self.start_time = start_time

    def __repr__(self) -> str:
        return f'MatchKey(event_code="{self.event_code}", match_level="{self.match_level}", match_series={self.match_series}, match_number={self.match_number}, alliance="{self.alliance}", season={self.season})'
    
    def __hash__(self) -> int:
        return self.__repr__().__hash__()
    
    def __eq__(self, other) -> bool:
        return self.__hash__() == other.__hash__()

SCORE_FIELDS_2024 = ['robot1Auto', 'robot2Auto', 'autoSampleNet', 'autoSampleLow', 'autoSampleHigh', 'autoSpecimenLow', 'autoSpecimenHigh', 'teleopSampleNet', 'teleopSampleLow', 'teleopSampleHigh', 'teleopSpecimenLow', 'teleopSpecimenHigh', 'robot1Teleop', 'robot2Teleop', 'minorFouls', 'majorFouls', 'autoSamplePoints', 'autoSpecimenPoints', 'teleopSamplePoints', 'teleopSpecimenPoints', 'teleopParkPoints', 'teleopAscentPoints', 'autoPoints', 'teleopPoints', 'endGamePoints', 'foulPointsCommitted', 'preFoulTotal', 'totalPoints']

def get_match_scores(event_code: str = None, season: int = 2024) -> dict[MatchKey, dict[str, Any]]:
    """
    Gets all score statistics from every match at the event for the given season.

    Args:
        event_code: the event code for matches to be retrieved
        season: the season the event happened in
    
    Returns a dictionary storing match statistics, or an empty dictionary if there was an error.
        Key: a MatchKey
        Value: dictionary where key = statistic (from FTC event API) and value = its value
    """

    # Grab a connection from the pool
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if event_code == None:
            query = f"SELECT eventCode, matchLevel, matchSeries, matchNumber, alliance, {', '.join(SCORE_FIELDS_2024)} FROM scores WHERE season=?"
            cursor.execute(query, (season,))
        else:
            query = f"SELECT eventCode, matchLevel, matchSeries, matchNumber, alliance, {', '.join(SCORE_FIELDS_2024)} FROM scores WHERE eventCode=? AND season=?"
            cursor.execute(query, (event_code, season))

        scores = cursor.fetchall()

        return {MatchKey(event_code=score[0], match_level=score[1], match_series=score[2], match_number=score[3], alliance=score[4], season=season): {SCORE_FIELDS_2024[i]: score[5+i] for i in range(len(SCORE_FIELDS_2024))} for score in scores}
    except Exception as e:
        print(e)
        return {}
    finally:
        # Release the connection back to the pool
        release_connection(conn)

def get_match_teams(event_code: str = None, season: int = 2024) -> dict[MatchKey, dict[int, tuple[str, bool]]]:
    """
    Retrieves teams playing in each match.

    Args:
        event_code: the event code for matches to be retrieved
        season: the season the event happened in
    
    Returns a dictionary storing teams playing in each match, or an empty dictionary if there was an error.
        Key: a MatchKey
        Value: dictionary where the key is the team number and the value is a tuple (station, on_field)
    """

    # Grab a connection from the pool
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if event_code == None:
            query = f"SELECT eventCode, tournamentLevel, series, matchNumber, teamNumber, station, onField, actualStartTime FROM matches WHERE season=? ORDER BY DATETIME(actualStartTime)"
            cursor.execute(query, (season,))
        else:
            query = f"SELECT eventCode, tournamentLevel, series, matchNumber, teamNumber, station, onField, actualStartTime FROM matches WHERE eventCode=? AND season=? ORDER BY DATETIME(actualStartTime)"
            cursor.execute(query, (event_code, season))

        matches = cursor.fetchall()

        # note: match start time is in local time zone :/
        individual_dicts = [{MatchKey(event_code, match_level, match_series, match_number, alliance=station[:-1], season=season, start_time=time.mktime(time.strptime(actualStartTime if "." not in actualStartTime else actualStartTime[:actualStartTime.index(".")], "%Y-%m-%dT%H:%M:%S"))): {team_number: (station, on_field)}}
                            for (event_code, match_level, match_series, match_number, team_number, station, on_field, actualStartTime) in matches]
        
        return reduce(lambda current_dict, new_dict: merge_with(merge_left, current_dict, new_dict), individual_dicts)
    except Exception as e:
        print(e)
        return {}
    finally:
        # Release the connection back to the pool
        release_connection(conn)

def get_user_team(user_id: int) -> UserTeam:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT u.team_id, t.name AS team_name, u.team_role FROM users u INNER JOIN teams t ON u.team_id = t.rowid WHERE u.rowid = ?;", (user_id,))
        team = cursor.fetchone()

        if team is None:
            return None 
        
        return {'id': team[0], 'name': team[1], 'role': team[2]}
    finally: 
        release_connection(conn)

def update_team(team: Team) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        print(team['name'])
        cursor.execute("UPDATE teams SET name=? WHERE rowid=?", (team['name'], team['id'],))
        conn.commit()

        return True 
    finally:
        release_connection(conn)

def remove_user(user_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET team_id = NULL, team_role = NULL WHERE rowid=?", (user_id, ))
        conn.commit()

        return True 
    finally:
        release_connection(conn)

def add_user(team: Team, email: str) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET team_id = ?, team_role = 0 WHERE email=?", (team['id'], email, ))
        conn.commit()

        return True 
    finally:
        release_connection(conn)     

def get_user_by_id(user_id):
    """
    Get full user information from the database by ID
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT rowid, name, email, team_id, team_role FROM users WHERE rowid=?", (user_id,))
        user_data = cursor.fetchone()
        
        if user_data is None:
            return None
            
        # Get associated team information if available
        user_team = None
        if user_data[3]:  # If team_id exists
            user_team = get_user_team(user_id)
            
        return {
            "id": user_data[0],
            "name": user_data[1],
            "email": user_data[2],
            "team": user_team
        }
    finally:
        release_connection(conn)

def get_event_codes() -> list[str]:
    """
    Returns a list of all events for which matches are stored.
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT eventCode FROM scores;")
        event_codes = cursor.fetchall()
        return list(map(lambda t: t[0], event_codes))
    
    except:
        return []
