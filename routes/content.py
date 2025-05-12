from flask import Blueprint, render_template, request, g, redirect, url_for, jsonify

import R
import database

content = Blueprint('content', __name__, template_folder="../templates")

@content.route("/login")
def login_page():
    return render_template("login.j2")

@content.route("/register")
def register_page():
    return render_template("register.j2")

@content.route("/")
def homepage():
    session_token = request.cookies.get('session')

    if not session_token:
        # Redirect to login page if user is not logged in
        return redirect(url_for('content.login_page'))
    
    # Retrieve session info from Redis
    session = R.get_session(session_token)

    if not session:
        # Redirect to login page if session token is invalid
        return redirect(url_for('content.login_page'))
    
    # Get complete user information from database using session ID
    user = database.get_user_by_id(session["id"])
    
    if not user:
        # If user not found in database, clear session and redirect to login
        return redirect(url_for('content.login_page'))
    
    # Render the homepage template with the full user details
    return render_template("homepage.j2", user=user)