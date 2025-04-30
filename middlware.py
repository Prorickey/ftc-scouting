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
        email = R.get_session(session_token)

        if not email:
            return make_response('incorrect session token', 401)
        
        # Attach the email to the context
        g.email = email
        return f(*args, **kwargs)
    return decorated_function