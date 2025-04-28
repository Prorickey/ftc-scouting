#!/usr/bin/env python3
from flask import Flask, Response, request
import redis
import sqlite3

app = Flask(__name__)

@app.route("/register", methods=["POST"])
def register():
    try:
        email = request.args.get("email")
        password = request.args.get("password")
    except Exception as err:
        print(err)
        return "error", 500
    
# Below route is ONLY AN EXAMPLE
@app.route("/login", methods=["GET", "POST"])
def loginPage():
    if request.method == "GET":
        # Get the session token from the request cookies - server-side token
        token = request.cookies.get('session')

        if token != None:
            user = get_token_data(token)
            if user != None:
                return redirect(f'/profile/{user}')
        
        return render_template('login.j2')
    
    fields = ['username', 'password', 'mode']
    for field in fields:
        if field not in request.form:
            return "ERROR"
        if len(str(request.form.get(field)).strip()) == 0:
            return "ERROR"
    
    if request.form.get('mode') not in ['login', 'register']:
        return render_template('login.j2', error="Malformed request")

    print(request.form.get('username'))
    print(request.form.get('password'))
    print('MODE:', str(request.form.get('mode')).upper())

    if request.form.get('mode').lower() == 'login':
        # Attempt to login the user
        if database.login(request.form.get('username'), request.form.get('password')):
            # Create the session token
            token = uuid.uuid4()

            # Store the session data in Redis
            R_Server.set(str(token), request.form.get('username').lower())

            # Set the session cookie in the response
            response = redirect('/games/minesweeper')
            response.set_cookie('session', str(token))
            return response
        else:
            # It's important that the message is generic to prevent user phishing attacks
            return render_template('login.j2', error="User doesn't exist or password is incorrect")
    elif request.form.get('mode').lower() == 'register':
        # Attempt to register the user
        if database.register(request.form.get('username'), request.form.get('password')):
            # Create the session token
            token = uuid.uuid4()

            # Store the session data in Redis
            R_Server.set(str(token), request.form.get('username').lower())

            # Set the session cookie in the response
            response = redirect('/games/minesweeper')
            response.set_cookie('session', str(token))
            return response
        else:
            return render_template('login.j2', error="Could not register user. Username may already exist.")

    return redirect('/games/minesweeper')