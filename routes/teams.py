from flask import Blueprint, g, jsonify, make_response, request

from database import store_new_team
from middlware import authenticated


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