from flask import Blueprint, g, make_response, request

from database import store_new_team
from middlware import authenticated


teams = Blueprint('teams', __name__)

@teams.route("/create", methods=["POST"])
@authenticated
def create_team():
    user = g.user

    body = request.get_json()
    name = body.get('name') 

    team_num = -1
    try:
        team_num = int(body.get('number'))
    except Exception as err:
        return make_response("malformed team number; must be integer", 400)

    if name is None or team_num is None:
        return make_response("missing name or team number", 400)

    res = store_new_team(name, team_num, user["id"])
    if res:
        return make_response("successfully created team", 200)
    else:
        return make_response("failed to create team", 400)