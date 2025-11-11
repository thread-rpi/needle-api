from flask import jsonify
from flask_jwt_extended import create_access_token

def login_protocol(username, password, members, admin):
    # check that username and password successfully received from the request
    if username == None or password == None:
        return jsonify({"error": "Username or Password not found in request."}), 500
    
    # find all users with matching usernames (should only be one, but we'll verify)
    user = list(members.find({"email": username}))

    # check that only one matching user exists 
    if len(user) == 1:
        # get the user and extract their ID
        user = user[0]
        id = user["_id"]

        # find the passwored associated with the id
        password_check = admin.find_one({"_id": id})
        if password_check: 
            # if given password doesn't match the database, return error
            if password != password_check["password"]:
                return jsonify({"error": "Credentials could not be authenticated."}), 401
            # otherwise create an access token and return it in a JSON response
            else:
                return jsonify({"data": {"token": create_access_token(identity = username)}}), 200
        # if no such user exists in admin, return error
        else:
            return jsonify({"error": "Member is not authorized to access this page."}), 403
    # if more than one user exists, return error
    else:
        return jsonify({"error": "Credentials could not be authenticated."}), 401
    