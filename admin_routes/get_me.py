from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from event_routes.event_helpers import serialize_mongo_doc

def get_me(members):
    try:
        current_user_email = get_jwt_identity()
        
        if not current_user_email:
            return jsonify({"error": "No user identity found in token."}), 500
        
        # Find user in members collection by email (JWT identity is the email)
        user = members.find_one({"email": current_user_email})
        
        if not user:
            return jsonify({"error": "User not found."}), 500
        
        # Serialize the MongoDB document (convert ObjectIds, datetimes, etc.)
        user = serialize_mongo_doc(user)
        
        return jsonify({
          "data": {
            "id": user['_id'],
            "email": user['email'],
            "name": user['name'],
            "role": user['role'],
          }
        }), 200
    
    except Exception as e:
        return jsonify({
            "error": f"Failed to retrieve user information: {str(e)}"
        }), 500