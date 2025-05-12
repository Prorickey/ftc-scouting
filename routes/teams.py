from flask import Blueprint, g, jsonify, make_response, request, render_template, redirect, url_for, flash

from R import UserTeam
from database import add_user, remove_user, store_new_team, update_team, get_team_by_code, add_user_to_team
from middlware import authenticated, team_admin
from email_validator import validate_email, EmailNotValidError

teams = Blueprint('teams', __name__)

@teams.route("/create", methods=["POST"])
@authenticated
def create_team():
    user = g.user

    name = request.form.get('name') 

    team_num = None
    try:
        team_num = int(request.form.get('number'))
    except Exception as err:
        return render_template("create_team.j2", error='Team number must be an integer')

    if name is None or team_num is None:
        return render_template("create_team.j2", error="Please fill in both name and team number fields")

    res = store_new_team(name, team_num, user["id"])
    if res is not None:
        return redirect(url_for('content.homepage'))
    else:
        return render_template("create_team.j2", error="Failed to create team; team may already exist")
    
@teams.route("/leave", methods=["GET"])
@authenticated
def leave_team():
    user = g.user
    
    remove_user(user['id'])
    
    # Redirect to the homepage
    return redirect(url_for('content.homepage'))

@teams.route("/update", methods=["POST"])
@team_admin
def edit_team():
    team: UserTeam = g.team

    body = request.get_json()

    name = body.get("name")
    if name is not None:
        team['name'] = name 

    if update_team(team):
        return make_response(jsonify({'message': 'sucessfully updated team'}), 200)
    else:
        return make_response(jsonify({'error': 'failed to update team'}))
    
@teams.route("/members/<user_id>", methods=["DELETE"])
@team_admin
def remove_member(user_id: str):
    uid = None 
    try:
        uid = int(user_id)
    except:
        return make_response(jsonify({"error": "user id is not an integer"}))
    
    if remove_user(uid):
        return make_response(jsonify({"message": "sucessfully removed the user"}))
    else:
        return make_response(jsonify({'error': 'failed to remove the user'}))
        
@teams.route("/members", methods=["PUT"])
@team_admin
def add_member():
    team: UserTeam = g.team 

    body = request.get_json()

    email = body.get("email")
    if email is None:
        return make_response(jsonify({"error": "body missing email"}))
    
    try:
        validate_email(email)
    except EmailNotValidError:
        return make_response(jsonify({"error": "invalid email"}))
    
    if add_user(team, email):
        return make_response(jsonify({"message": "sucessfully added the user"}))
    else:
        return make_response(jsonify({'error': 'failed to add the user'}))

@teams.route("/join", methods=["POST"])
@authenticated
def join_team():
    """Route for joining a team using a team code"""
    user = g.user
    
    # First check if user is already in a team
    from database import get_user_team
    current_team = get_user_team(user['id'])
    if current_team:
        # User is already in a team, redirect to homepage
        return redirect(url_for('content.homepage'))
    
    # Get the team code from the form
    team_code = request.form.get('code')
    if not team_code:
        return redirect(url_for('content.homepage'))
    
    # Look up the team by code
    team = get_team_by_code(team_code)
    if not team:
        return redirect(url_for('content.homepage'))
    
    # Try to add the user to the team
    if add_user_to_team(team['id'], user['id']):
        # Success - redirect to homepage
        return redirect(url_for('content.homepage'))
    else:
        # Failed - user might already be in a team
        return redirect(url_for('content.homepage'))

@teams.route("/members/<user_id>/promote", methods=["POST"])
@team_admin
def promote_member(user_id: str):
    """Promote a team member to admin"""
    uid = None 
    try:
        uid = int(user_id)
    except:
        return make_response(jsonify({"error": "user id is not an integer"}))
    
    from database import promote_user_to_admin
    if promote_user_to_admin(uid, g.user['id']):
        return make_response(jsonify({"message": "successfully promoted the user"}))
    else:
        return make_response(jsonify({"error": "failed to promote the user"}), 400)