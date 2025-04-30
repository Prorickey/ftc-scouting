import redis


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
    
def set_session(token, email):
    # Store the session data in Redis
    __redis.set("session:" + str(token), email.lower())

def get_session(token):
    __redis.get("session" + str(token))