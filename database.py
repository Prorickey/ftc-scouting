from queue import Queue
import secrets
import sqlite3
import hashlib
import string

schema_file = "schema.sql"

# Connection pool for SQLite database connections
# I had to do this because flask is handling my requests 
# on seperate threads. This solution helps avoid using one
# connection on different threads and allows my application
# to scale better
__connection_pool = Queue(maxsize=5)
for _ in range(5):
    __connection_pool.put(sqlite3.connect("database.db", check_same_thread=False))

def get_connection():
    return __connection_pool.get()

def release_connection(connection):
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

def login(email: str, password: str) -> bool:
    """
    Login a user with the given email and password.
    """

    # Grab a connection from the pool
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT password, salt FROM users WHERE email=?", (email.lower(),))
        user = cursor.fetchone()

        if user is None:
            return False
        
        password_digest = user[0]
        password_salt = user[1]

        # Hash the password with the salt
        hashed_password = hashlib.sha256((password_salt + password).encode()).hexdigest()

        if hashed_password == password_digest:
            return True
    finally:
        # Release the connection back to the pool
        release_connection(conn)

    return False


def register(email: str, password: str, name: str) -> bool:
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
            return False

        # Generate a random salt
        salt = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))

        # Hash the password with the salt
        hashed_password = hashlib.sha256((salt + password).encode()).hexdigest()

        # Insert the new user into the database
        cursor.execute("INSERT INTO users (email, name, password, salt) VALUES (?, ?, ?, ?)", (email.lower(), name, hashed_password, salt))
        conn.commit()
    finally:
        # Release the connection back to the pool
        release_connection(conn)

    return True

def store_match_scores(event_code: str, match_data: dict, season: int = 2024) -> bool:
    """
    Saves latest match score details. If we already have old data for the match, it will be overwritten.

    Args:
        event_code: the code of the event that this match is part of
        match_data: the dictionary storing the JSON data from the FTC Event API
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
        allianceScores = match_data['alliances']
        for alliance in ["Red", "Blue"]:
            this_alliance: dict = next(filter(lambda allianceScore: allianceScore['alliance'] == alliance, allianceScores))
            # cursor.execute("SELECT * FROM scores WHERE season = ? AND eventCode = ? AND matchLevel = ? AND matchSeries = ? AND matchNumber = ? AND alliance = ?",\
            #                (season, event_code, match_data["matchLevel"], match_data["matchSeries"], match_data["matchNumber"], alliance))
            
            # do we need ` ON CONFLICT (season, eventCode, matchLevel, matchSeries, matchNumber, alliance) REPLACE` at the end?
            
            individual_alliance_keys = list(this_alliance.keys())
            for key in individual_alliance_keys:
                assert key.isalnum()
            individual_alliance_values = [this_alliance[key] for key in individual_alliance_keys]

            query = f"INSERT OR REPLACE INTO scores (season, eventCode, matchLevel, matchSeries, matchNumber, {', '.join(individual_alliance_keys)}) VALUES (?, ?, ?, ?, ?, {', '.join(['?']*len(individual_alliance_keys))})"
            print(query)

            cursor.execute(query,
                           (season, event_code, match_data["matchLevel"], match_data["matchSeries"], match_data["matchNumber"], *individual_alliance_values))

            conn.commit()
    finally:
        # Release the connection back to the pool
        release_connection(conn)
    
    return True