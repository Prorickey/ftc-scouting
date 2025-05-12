#!/usr/bin/env python3
import database
import R
from routes import create_app
from stats import epa
import time

app = create_app()

# Initialize the SQLite database
database.init()

# Initialize EPA
print("Initializing EPA, this might take a while...")
start = time.time()
epa.init()
epa.season_epa()
print(f"EPA initialized in {time.time() - start} seconds")

# Connect to Redis
if R.init() == False:
    exit(1) # Message already printed
    
app.run(port=8080, debug=True)