#!/usr/bin/env python3
import uuid
from flask import Flask, Response, make_response, redirect, request
import database
import redis

app = Flask(__name__)

# Initialize the SQLite database
database.init()

# Connect to Redis
R = redis.StrictRedis()
try:
    R.ping()
except:
    print("REDIS: Not Running -- No Streams Available")
    R = None

@app.route("/register", methods=["POST"])
def register():
    try:
        body = request.get_json()
        email = body.get('email')
        password = body.get('password')
        name = body.get('name')

        if email is None or password is None or name is None:
            return make_response("missing email, password, or name", 400)
        
        if database.register(email, password, name):
            # Create the session token
            token = uuid.uuid4()

            # Store the session data in Redis
            R.set("session:" + str(token), email.lower())

            # Set the session cookie in the response
            response = make_response("success", 200)
            response.set_cookie('session', str(token))
            return response
        else:
            return make_response("failed to create user", 400)
    except Exception as err:
        print(err)
        return make_response("internal server error", 500)
    
@app.route("/login", methods=["POST"])
def login():
    try:
        body = request.get_json()
        email = body.get('email')
        password = body.get('password')

        if email is None or password is None:
            return make_response("missing email or password", 400)
        
        if database.login(email, password):
            # Create the session token
            token = uuid.uuid4()

            # Store the session data in Redis
            R.set("session:" + str(token), email.lower())

            # Set the session cookie in the response
            response = make_response("success", 200)
            response.set_cookie('session', str(token))
            return response
        else:
            return make_response("failed to login. password or email may be incorrect", 400)
    except Exception as err:
        print(err)
        return make_response("internal server error", 500)
    
app.run(port=8080, debug=True)