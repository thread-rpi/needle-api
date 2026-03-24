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

        required_fields = ["title", "date", "location", "type"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": "Required fields are missing or malformed fields are present"}), 400

        if not isinstance(data["title"], str) or not isinstance(data["location"], str) or not isinstance(data["type"], str):
            return jsonify({"error": "Required fields are missing or malformed fields are present"}), 400

        if data["type"] not in ['shoot', 'internal', 'external', 'fotw']:
            return jsonify({"error": "Required fields are missing or malformed fields are present"}), 400

        try:
            event_date = dateutil.parser.isoparse(str(data["date"]))
        except (ValueError, TypeError):
            return jsonify({"error": "Required fields are missing or malformed fields are present"}), 400

        # Optional Fields Mapping
        s3_path = data.get("s3_path", "")
        if not isinstance(s3_path, str): s3_path = ""
        
        blurb = data.get("blurb", "")
        if not isinstance(blurb, str): blurb = ""
        
        published = data.get("published", False)
        if not isinstance(published, bool): published = False

        # Array parsing function
        def parse_object_id_array(array_data):
            if not isinstance(array_data, list):
                return []
            parsed = []
            for item in array_data:
                try:
                    parsed.append(ObjectId(item))
                except (InvalidId, TypeError):
                    raise ValueError
            return parsed

        try:
            image_ids = parse_object_id_array(data.get("image_ids", []))
            photographer_ids = parse_object_id_array(data.get("photographer_ids", []))
            creative_director_ids = parse_object_id_array(data.get("creative_director_ids", []))
            model_ids = parse_object_id_array(data.get("model_ids", []))
        except ValueError:
            return jsonify({"error": "Required fields are missing or malformed fields are present"}), 400

        # Additional personnel parsing
        additional_personnel = []
        if "additional_personnel" in data:
            raw_additional = data["additional_personnel"]
            if not isinstance(raw_additional, list):
                return jsonify({"error": "Required fields are missing or malformed fields are present"}), 400

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

        # Automatic Fields
        now = datetime.utcnow()
        new_event = {
            "_id": ObjectId(),
            "title": data["title"],
            "date": event_date,
            "location": data["location"],
            "type": data["type"],
            "s3_path": s3_path,
            "blurb": blurb,
            "image_ids": image_ids,
            "published": published,
            "photographer_ids": photographer_ids,
            "creative_director_ids": creative_director_ids,
            "model_ids": model_ids,
            "created_at": now,
            "updated_at": now,
            "created_by": user["_id"],
            "updated_by": user["_id"]
        }
        
        if additional_personnel or "additional_personnel" in data:
            new_event["additional_personnel"] = additional_personnel

        # Database Operation
        events.insert_one(new_event)
        
        return jsonify({"data": {"id": str(new_event["_id"])}}), 200

    except Exception as e:
        return jsonify({"error": "Something went wrong internally"}), 500
