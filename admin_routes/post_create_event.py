from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity
from datetime import datetime
import dateutil.parser
from bson.objectid import ObjectId
from bson.errors import InvalidId

def create_event_endpoint(events, members, admin):
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

        required_fields = ["title", "date", "location", "type", "blurb", "published"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": "Required fields are missing or malformed fields are present"}), 400

        # Type validation for required string fields
        if not isinstance(data["title"], str) or not isinstance(data["location"], str) or \
           not isinstance(data["type"], str) or not isinstance(data["blurb"], str):
            return jsonify({"error": "Required fields are missing or malformed fields are present"}), 400

        # Type validation for published (must be boolean)
        if not isinstance(data["published"], bool):
            return jsonify({"error": "Required fields are missing or malformed fields are present"}), 400

        # Validate event type enum
        if data["type"] not in ['shoot', 'internal', 'external', 'fotw']:
            return jsonify({"error": "Required fields are missing or malformed fields are present"}), 400

        # Parse and validate date
        try:
            event_date = dateutil.parser.isoparse(str(data["date"]))
        except (ValueError, TypeError):
            return jsonify({"error": "Required fields are missing or malformed fields are present"}), 400

        # Optional Fields Processing
        optional_fields_to_add = {}

        if "image_path" in data:
            image_path = data["image_path"]
            if image_path is not None and not isinstance(image_path, str):
                return jsonify({"error": "Required fields are missing or malformed fields are present"}), 400
            optional_fields_to_add["image_path"] = image_path

        # Array parsing function
        def parse_object_id_array(array_data):
            if not isinstance(array_data, list):
                raise ValueError
            parsed = []
            for item in array_data:
                try:
                    parsed.append(ObjectId(item))
                except (InvalidId, TypeError):
                    raise ValueError
            return parsed

        for array_field in ["image_ids", "photographer_ids", "creative_director_ids", "model_ids"]:
            if array_field in data:
                try:
                    optional_fields_to_add[array_field] = parse_object_id_array(data[array_field])
                except ValueError:
                    return jsonify({"error": "Required fields are missing or malformed fields are present"}), 400

        # Additional personnel parsing
        if "additional_personnel" in data:
            raw_additional = data["additional_personnel"]
            if not isinstance(raw_additional, list):
                return jsonify({"error": "Required fields are missing or malformed fields are present"}), 400

            additional_personnel = []
            for item in raw_additional:
                if not isinstance(item, dict) or "member_id" not in item or "role" not in item:
                    return jsonify({"error": "Required fields are missing or malformed fields are present"}), 400

                if not isinstance(item["role"], str):
                    return jsonify({"error": "Required fields are missing or malformed fields are present"}), 400

                try:
                    additional_personnel.append({
                        "member_id": ObjectId(item["member_id"]),
                        "role": item["role"]
                    })
                except (InvalidId, TypeError):
                    return jsonify({"error": "Required fields are missing or malformed fields are present"}), 400
            
            optional_fields_to_add["additional_personnel"] = additional_personnel

        # Automatic Fields
        now = datetime.utcnow()
        new_event = {
            "_id": ObjectId(),
            "title": data["title"],
            "date": event_date,
            "location": data["location"],
            "type": data["type"],
            "blurb": data["blurb"],
            "published": data["published"],
            "created_at": now,
            "updated_at": now,
            "created_by": user["_id"],
            "updated_by": user["_id"]
        }
        
        # Add optional fields only if they were present in the request
        new_event.update(optional_fields_to_add)

        # Database Operation
        events.insert_one(new_event)

        return jsonify({"data": {"id": str(new_event["_id"])}}), 200

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": "Something went wrong internally"}), 500
