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

class UserSession(TypedDict):
    id: int
    name: str
    
def set_session(token: str, id: int, email: str):
    # Store the session data in Redis
    __redis.set("session:" + str(token), str(id) + ";" + email.lower())

def get_session(token) -> UserSession:
    val = __redis.get("session:" + str(token))
    if val is None:
        return None 
    
    id, name = val.decode('utf-8').split(';')
    return {"id": int(id), "name": name}