from flask import jsonify
from flask_jwt_extended import create_access_token

def login_protocol(username, password, members, admin):
    user = members.find({"email": username})
    if not user:
        return jsonify({"error": "Credentials could not be authenticated."}), 401

    id = user["_id"]
    password_check = admin.find({"_id": id})
    if not password_check:
        return jsonify({"error": "Member is not authorized to access this page."}), 403
    
    if password != password_check["password"]:
        return jsonify({"error": "Credentials could not be authenticated."}), 401
    else:
        return jsonify({"data": {"token": create_access_token(identity = username)}}), 200
    