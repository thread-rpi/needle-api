from flask import Flask, jsonify
import pymongo
from pymongo.errors import ConnectionFailure, OperationFailure
import os
from get_shoot import get_shoot
from get_semester import get_semester

SERVER_TIMEOUT = 5000 # client will error if a connection isn't made within 5 seconds of its first request

# Initialize flask application
app = Flask(__name__)
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
client = pymongo.MongoClient(app.config['MONGO_URI'], serverSelectionTimeoutMS=SERVER_TIMEOUT)

# Initialize databases
eventsDB = client['eventsDB']
shoots = eventsDB['shoot']
events = eventsDB['event']
calendar = eventsDB['calendar']

# Routes
@app.route("/")
def root():
    return "Welcome to Needle!"


@app.route("/health")
def health_check():
    status = {"status": "healthy"}
    http_status_code = 200

    # DB connection checks
    try:
       client.admin.command('ping')
    except ConnectionFailure:
       status = {"status": "unhealthy", "error": "MongoDB connection failed."}
       http_status_code = 500
    except OperationFailure:
        status = {"status": "unhealthy", "error": "MongoDB authentication failed."}
        http_status_code = 500

    return jsonify(status), http_status_code


@app.route("/api/shoot/<shoot_id>", methods=["GET"])
def get_shoot_route(shoot_id):
    return get_shoot(shoots, shoot_id)

@app.route("/api/events/<semester_id>", methods=["GET"])
def get_semester_route(semester_id):
    return get_semester(calendar, semester_id)


if __name__ == "__main__":
    app.run(debug=True)
