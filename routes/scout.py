import uuid
from flask import Blueprint, make_response, request, jsonify, render_template

import R
import database

# Create a Blueprint instance
scout = Blueprint('scout', __name__, static_folder="../static", template_folder="../templates")

@scout.route("/<team>")
def scout_team_route(team: str):
    """
    Renders the scouting webpage.
    """
    return render_template("fieldview.j2", team=team)