#!/usr/bin/env python3
import database
import R
from routes import create_app
from stats import epa
import time
import threading

app = create_app()

# Initialize the SQLite database
database.init()

# Initialize EPA in background
def __init_epa():
    epa.init()
    epa.season_epa()

threading.Thread(target=__init_epa).start()

# Connect to Redis
if R.init() == False:
    exit(1) # Message already printed
    
app.run(port=8080, debug=True)