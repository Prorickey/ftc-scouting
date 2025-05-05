from functools import wraps

from flask import g, jsonify, make_response, request

import R
from database import get_user_team

# Here is an example of how to use the authentication
# middleware for anyone who needs it :)
# @app.route("/info", methods=["GET"])
# @authenticated
# def test():
#     print("I'm authenticated", g.email)
#     return 'yay', 200

def authenticated(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_token = request.cookies.get('session')

        if not session_token:
            return make_response(jsonify({'error': 'missing session token'}), 401)
        
        # Retrieve email based on session token
        user = R.get_session(session_token)

        if not user:
            return make_response(jsonify({'error': 'incorrect session token'}), 401)
        
        # Attach the email to the context
        g.user = user
        return f(*args, **kwargs)
    return decorated_function

def team_admin(f):
    @wraps(f)
    @authenticated
    def decorated_function(*args, **kwargs):
        user: R.UserSession = g.user
        team: R.UserTeam = get_user_team(user['id'])

        if team is None:
            return make_response(jsonify({'error': "not a member of a team"}))

        if team['role'] != 1: # Check if they are an admin here
            return make_response(jsonify({'error': 'insufficient permissions'}, 403))
        
        # Attach the email to the context
        g.team = team
        return f(*args, **kwargs)
    return decorated_function