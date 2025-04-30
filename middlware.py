from functools import wraps

from flask import g, make_response, request

import R

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
            return make_response('missing session token', 401)
        
        # Retrieve email based on session token
        user = R.get_session(session_token)

        if not user:
            return make_response('incorrect session token', 401)
        
        # Attach the email to the context
        g.user = user
        return f(*args, **kwargs)
    return decorated_function