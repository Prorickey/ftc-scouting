import redis
from typing import TypedDict

__redis = None 

def init() -> bool:
    global __redis 

    # Connect to Redis
    __redis = redis.StrictRedis()
    try:
        __redis.ping()
        return True
    except:
        print("REDIS: Not Running -- No Streams Available")
        return False
    
class Team(TypedDict):
    id: int 
    name: str
    code: str

class UserTeam(TypedDict):
    id: int 
    name: str
    role: int
    code: str

class UserSession(TypedDict):
    id: int
    name: str
    
def set_session(token: str, id: int, email: str):
    """
    Set a token in redis and connect it with relavent information
    """

    # Store the session data in Redis
    __redis.set("session:" + str(token), str(id) + ";" + email.lower())

def get_session(token) -> UserSession:
    """
    Get a UserSession from redis by token
    Returns the UserSession if session exists, none otherwise
    """

    val = __redis.get("session:" + str(token))
    if val is None:
        return None 
    
    id, name = val.decode('utf-8').split(';')
    return {"id": int(id), "name": name}

def delete_session(token: str) -> bool:
    """
    Delete a session from Redis by token
    Returns true if session existed and was deleted, false otherwise
    """

    key = "session:" + str(token)
    if __redis.exists(key):
        __redis.delete(key)
        return True
    
    return False