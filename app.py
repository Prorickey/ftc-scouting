#!/usr/bin/env python3
import database
import R
from routes import create_app
from stats import epa

app = create_app()

# Initialize the SQLite database
database.init()

# Initialize EPA
epa.init()
epa.season_epa()

# Connect to Redis
if R.init() == False:
    exit(1) # Message already printed
    
app.run(port=8080, debug=True)