from flask import Flask, jsonify
import pymongo
import os
from get_shoot import get_shoot

# Initialize flask application
app = Flask(__name__)
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
client = pymongo.MongoClient(app.config['MONGO_URI'])

# Initialize databases
eventsDB = client['eventsDB']
shoots = eventsDB['shoot']
events = eventsDB['event']

# Routes
@app.route("/")
def root():
    return "Welcome to Needle!"


@app.route("/health")
def health_check():
    status = {"status": "healthy"}
    http_status_code = 200

    #db connection checks when added

    return jsonify(status), http_status_code


@app.route("/api/shoot/<shoot_id>", methods=["GET"])
def get_shoot_route(shoot_id):
    return get_shoot(shoots, shoot_id)


if __name__ == "__main__":
    app.run(debug=True)
