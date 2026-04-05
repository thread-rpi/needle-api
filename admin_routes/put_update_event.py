from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity
from datetime import datetime
import dateutil.parser
from bson.objectid import ObjectId
from bson.errors import InvalidId

def update_event_endpoint(events, members, admin):
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

        updatable_fields = [
            "title", "date", "location", "type", "blurb", "image_path", "published",
            "image_ids", "photographer_ids", "creative_director_ids", "model_ids",
            "additional_personnel"
        ]

        fields_to_update = {}

        # check if at least one updatable field is present
        has_updatable = any(field in data for field in updatable_fields)
        if not has_updatable:
            return jsonify({"error": "Required fields are missing or malformed fields are present"}), 400

        # Validate string fields
        string_fields = ["title", "location", "type", "blurb", "image_path"]
        for field in string_fields:
            if field in data:
                if data[field] is not None and not isinstance(data[field], str):
                    return jsonify({"error": "Required fields are missing or malformed fields are present"}), 400
                fields_to_update[field] = data[field]
        
        # specific string matching for type
        if "type" in fields_to_update and fields_to_update["type"] not in ['shoot', 'internal', 'external', 'fotw']:
            return jsonify({"error": "Required fields are missing or malformed fields are present"}), 400

        # Validate boolean field
        if "published" in data:
            if not isinstance(data["published"], bool):
                return jsonify({"error": "Required fields are missing or malformed fields are present"}), 400
            fields_to_update["published"] = data["published"]

        # Validate date
        if "date" in data:
            try:
                fields_to_update["date"] = dateutil.parser.isoparse(str(data["date"]))
            except (ValueError, TypeError):
                return jsonify({"error": "Required fields are missing or malformed fields are present"}), 400

        # Validate arrays
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
                    fields_to_update[array_field] = parse_object_id_array(data[array_field])
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
            
            fields_to_update["additional_personnel"] = additional_personnel

        # Automatic Fields
        fields_to_update["updated_at"] = datetime.utcnow()
        fields_to_update["updated_by"] = user["_id"]

        # Database Operation
        result = events.update_one(
            {"_id": event_id},
            {"$set": fields_to_update}
        )

        if result.matched_count == 0:
            return jsonify({"error": "Event not found"}), 404

        return jsonify({"data": {"id": str(event_id)}}), 200

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": "Something went wrong internally"}), 500
