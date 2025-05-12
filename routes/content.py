from flask import Blueprint, render_template, request, g, redirect, url_for, jsonify, send_file

import R
import database

content = Blueprint('content', __name__, template_folder="../templates", static_folder="../static")

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
        # Open page as anon user
        return render_template("homepage.j2", user={'name': 'Anonymous User'}, anon=True)
    
    # Retrieve session info from Redis
    session = R.get_session(session_token)

    if not session:
        # Open page as anon user
        return render_template("homepage.j2", user={'name': 'Anonymous User'}, anon=True)
    
    # Get complete user information from database using session ID
    user = database.get_user_by_id(session["id"])
    
    if not user:
        # Open page as anon user
        return render_template("homepage.j2", user={'name': 'Anonymous User'}, anon=True)
    
    members = []
    if user['team']:
        members = database.get_team_members(user['id'])
    
    # Render the homepage template with the full user details
    return render_template("homepage.j2", user=user, team=user['team'], members=members)

@content.route("/opr")
def opr():
    event_codes = database.get_event_codes()
    return render_template("opr.j2", events=event_codes, fields=database.SCORE_FIELDS_2024)

@content.route("/epa")
def epa():
    return render_template("epa.j2")

@content.route("/explore_teams")
def explore_teams():
    return render_template("explore_teams.j2")

@content.route("/createteam")
def create_team_page():
    session_token = request.cookies.get('session')
    if not session_token:
        return redirect(url_for('content.login_page'))
    
    session = R.get_session(session_token)
    if not session:
        return redirect(url_for('content.login_page'))
    
    return render_template("create_team.j2")
