from flask import Flask, jsonify
from bson import ObjectId
import pymongo
import os

# Set up Flask and MongoDB
app = Flask(__name__)
app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = pymongo.MongoClient(app.config['MONGO_URI'])
db = client['eventsDB']
shoots = db['shoots']

@app.route("/api/shoots/<shoot_id>", methods=["GET"])
def get_shoot(shoot_id):
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


if __name__ == '__main__':
    app.run(debug=True)