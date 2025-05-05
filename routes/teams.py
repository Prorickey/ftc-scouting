from flask import Blueprint, g, jsonify, make_response, request

from R import UserTeam
from database import add_user, remove_user, store_new_team, update_team
from middlware import authenticated, team_admin
from email_validator import validate_email, EmailNotValidError

teams = Blueprint('teams', __name__)

@teams.route("/create", methods=["POST"])
@authenticated
def create_team():
    user = g.user

    body = request.get_json()
    name = body.get('name') 

    team_num = None
    try:
        team_num = int(body.get('number'))
    except Exception as err:
        return make_response(jsonify({'error': 'malformed team number; must be integer'}), 400)

    if name is None or team_num is None:
        return make_response(jsonify({'error': "missing name or team number"}), 400)

    res = store_new_team(name, team_num, user["id"])
    if res is not None:
        return make_response(jsonify({'message': 'successfully created team', 'team': res}), 200)
    else:
        return make_response(jsonify({'error': "failed to create team; team may already exist"}), 400)
    

    
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