import uuid
from flask import Blueprint, jsonify, make_response, request, render_template, redirect, url_for

import R
import database

# Create a Blueprint instance
auth = Blueprint('auth', __name__, template_folder="../templates")

@auth.route("/register", methods=["POST"])
def register():
    """
    Hosts a route to register a user via a POST request.
    """
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')

        if email is None or password is None or name is None:
            return render_template("register.j2", error="Please fill in all fields: email, password, and name")
        
        userid = database.register(email, password, name)
        if userid is not None:
            # Create the session token
            token = uuid.uuid4()
            
            R.set_session(token, userid, email)

            # Set the session cookie and redirect to homepage
            response = redirect(url_for('content.homepage'))
            response.set_cookie('session', str(token))
            return response
        else:
            return render_template("register.j2", error="Registration failed. Email may already be in use.")
    except Exception as err:
        print(err)
        return render_template("register.j2", error="An internal server error occurred")
    
@auth.route("/login", methods=["POST"])
def login():
    """
    Hosts a route to log in via a POST request.
    """
    try:
        email = request.form.get('email')
        password = request.form.get('password')

        if email is None or password is None:
            return render_template("login.j2", error="Please fill in both email and password fields")
        
        userid = database.login(email, password)
        if userid is not None:
            # Create the session token
            token = uuid.uuid4()

            # Store the session data in Redis
            R.set_session(token, userid, email)

            # Set the session cookie and redirect to homepage
            response = redirect(url_for('content.homepage'))
            response.set_cookie('session', str(token))
            return response
        else:
            return render_template("login.j2", error="Invalid email or password. Please try again.")
    except Exception as err:
        print(err)
        return render_template("login.j2", error="An internal server error occurred")

@auth.route("/logout", methods=["GET"])
def logout():
    """
    Hosts a route to log out the current user.
    """
    # Get the current session token from cookies
    session_token = request.cookies.get('session')
    
    # Create response that redirects to login page
    response = redirect(url_for('content.login_page'))
    
    # If there's a session token, delete it from Redis
    if session_token:
        try:
            # Remove session data from Redis
            R.delete_session(session_token)
        except:
            pass  # If deletion fails, just continue
    
    # Clear the session cookie
    response.set_cookie('session', '', expires=0)
    
    return response