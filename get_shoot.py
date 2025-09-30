from flask import jsonify
from bson import ObjectId

def get_shoot(shoots, shoot_id):
    try:
        obj_id = ObjectId(shoot_id)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    shoot = shoots.find_one({"_id": obj_id})

    if shoot:
        shoot_data = {
            "data": {
                "_id": str(shoot["_id"]),
                "path": shoot.get("path", ""),
                "desc": shoot.get("desc", ""),
                "personnel": shoot.get("personnel", []),
            }
        }
        return jsonify(shoot_data)
    else:
        return jsonify({"error": "Shoot not found"}), 404