import uuid
from flask import Blueprint, make_response, request

import R
import database

# Create a Blueprint instance
auth = Blueprint('auth', __name__)

@auth.route("/register", methods=["POST"])
def register():
    try:
        body = request.get_json()
        email = body.get('email')
        password = body.get('password')
        name = body.get('name')

        if email is None or password is None or name is None:
            return make_response("missing email, password, or name", 400)
        
        userid = database.register(email, password, name)
        if userid is not None:
            # Create the session token
            token = uuid.uuid4()
            
            R.set_session(token, userid, email)

            # Set the session cookie in the response
            response = make_response("success", 200)
            response.set_cookie('session', str(token))
            return response
        else:
            return make_response("failed to create user", 400)
    except Exception as err:
        print(err)
        return make_response("internal server error", 500)
    
@auth.route("/login", methods=["POST"])
def login():
    try:
        body = request.get_json()
        email = body.get('email')
        password = body.get('password')

        if email is None or password is None:
            return make_response("missing email or password", 400)
        
        userid = database.login(email, password)
        if userid is not None:
            # Create the session token
            token = uuid.uuid4()

            # Store the session data in Redis
            R.set_session(token, userid, email)

            # Set the session cookie in the response
            response = make_response("success", 200)
            response.set_cookie('session', str(token))
            return response
        else:
            return make_response("failed to login. password or email may be incorrect", 400)
    except Exception as err:
        print(err)
        return make_response("internal server error", 500)