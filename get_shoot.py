from flask import jsonify
from bson import ObjectId

# shoots: MongoDB shoot collection
# shoot_id: string representing a shoot id
# returns shoot data of shoot corresponding to choot_id
def get_shoot(shoots, shoot_id):
    # Check if shoot_id is a valid format
    try:
        obj_id = ObjectId(shoot_id)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    # Search for shoot of corresponding id
    shoot = shoots.find_one({"_id": obj_id})

    # If shoot exists return the data, if not return an error
    if shoot:
        shoot_data = {
            "data": {
                "_id": str(shoot["_id"]),
                "path": shoot.get("path", ""),
                "desc": shoot.get("desc", ""),
                "personnel": shoot.get("personnel", []),
                "img_count": shoot.get("img_count", 0)
            }
        }
        return jsonify(shoot_data)
    else:
        return jsonify({"error": "Shoot not found"}), 404