from flask import Blueprint, g, make_response, request, render_template

import database
from middlware import authenticated

# Create a Blueprint instance
scout = Blueprint('scout', __name__, static_folder="../static", template_folder="../templates")

@scout.route("/<team>")
def scout_team_route(team: str):
    """
    Renders the scouting webpage.
    """
    return render_template("fieldview.j2", team=int(team))

@scout.route("/<team>", methods=["POST"])
@authenticated
def scout_team_post(team: str):
    """
    Receives the finished match data and stores it.
    """

    user = database.get_user_by_id(g.user["id"])
    if user['team'] is None:
        return make_response("you must be on a team to scout", 400)

    body = request.get_json()
    auto_high_sample = body['auto_high_sample']
    auto_low_sample = body['auto_low_sample']
    auto_high_specimen = body['auto_high_specimen']
    auto_low_specimen = body['auto_low_specimen']
    high_sample = body['high_sample']
    low_sample = body['low_sample']
    high_specimen = body['high_specimen']
    low_specimen = body['low_specimen']
    climb_level = body['climb_level']
    additional_points = body['additional_points']

    res = database.add_match_to_database(user['team']['id'], int(team), auto_high_sample, auto_low_sample, 
                                         auto_high_specimen, auto_low_specimen, high_sample, low_sample, 
                                         high_specimen, low_specimen, climb_level, additional_points)

    if res:
        return make_response("success", 200)
    else:
        return make_response("internal server error", 500)
        

