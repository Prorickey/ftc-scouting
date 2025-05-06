import uuid
from flask import Blueprint, make_response, request, jsonify

import R
import database
from stats import opr, epa

# Create a Blueprint instance
stats = Blueprint('stats', __name__)

@stats.route("/opr/<season>/<event_code>/<statistic>", methods=["GET"])
def opr_route(season: str, event_code: str, statistic: str):
    """
    Calculates the OPR for all teams at an event.
    """
    try:
        if season != "2024":
            return make_response("2024 is the only season supported", 400)
        
        if statistic is None:
            return make_response("missing statistic to get OPR for", 400)
        
        if event_code is None:
            return make_response("missing event_code to get OPR for", 400)
        
        if statistic not in database.SCORE_FIELDS_2024:
            return make_response(f"statistic is invalid, must be one of {database.SCORE_FIELDS_2024}", 400)
        
        return jsonify(opr.calc_single_stat_opr(event_code=event_code, statistic=statistic, season=2024))
    except Exception as err:
        print(err)
        return make_response("internal server error", 500)

@stats.route("/epa/<season>/<team>", methods=["GET"])
def epa_route(season: str, team: str):
    """
    Calculates the EPA for a single team.
     
    If query string parameter time is provided, returns the EPA at that time.
    Otherwise, returns a dictionary where key = time and value = EPA at that time.
    """
    try:
        if season != "2024":
            return make_response("2024 is the only season supported", 400)
        
        if not team.isnumeric():
            return make_response("team is not numeric", 400)
        
        t = request.args.get("time", type=float)
        if t is None:
            return jsonify(epa.get_all_epas(int(team)))
        else:
            return jsonify(epa.get_epa(int(team), time=t))
    except Exception as err:
        print(err)
        return make_response("internal server error", 500)
