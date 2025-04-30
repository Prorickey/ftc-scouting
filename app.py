#!/usr/bin/env python3
import database
import R
from routes import create_app

app = create_app()

# Initialize the SQLite database
database.init()

# Connect to Redis
if R.init() == False:
    exit(1) # Message already printed
    
app.run(port=8080, debug=True)