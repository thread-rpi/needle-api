from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity
from bson.objectid import ObjectId
from bson.errors import InvalidId

def delete_event_endpoint(events, members, admin):
    try:
        # Authentication and Authorization
        current_user_email = get_jwt_identity()
        if not current_user_email:
            return jsonify({"error": "Unauthenticated or unauthorized request"}), 403

        user = members.find_one({"email": current_user_email})
        if not user:
            return jsonify({"error": "Unauthenticated or unauthorized request"}), 403

        admin_user = admin.find_one({"_id": user["_id"]})
        if not admin_user:
            return jsonify({"error": "Unauthenticated or unauthorized request"}), 403

        # Request Validation
        data = request.json
        if not data:
            return jsonify({"error": "Required fields are missing or malformed fields are present"}), 400

        if "_id" not in data:
            return jsonify({"error": "Required fields are missing or malformed fields are present"}), 400

        try:
            event_id = ObjectId(data["_id"])
        except (InvalidId, TypeError):
            return jsonify({"error": "Required fields are missing or malformed fields are present"}), 400

        # Database Operation
        result = events.delete_one({"_id": event_id})

        if result.deleted_count == 0:
            return jsonify({"error": "Event not found"}), 404

        return jsonify({"data": {"id": str(event_id)}}), 200

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": "Something went wrong internally"}), 500
