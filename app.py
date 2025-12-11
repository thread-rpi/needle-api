from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager
import pymongo
from pymongo.errors import ConnectionFailure, OperationFailure
import os
from event_routes.get_shoot import get_shoot
from member_routes.get_members import get_members
from event_routes.get_semester import get_semester
from event_routes.get_current_fotw import get_current_fotw
from event_routes.get_past_events import get_past_events
from event_routes.get_reigning_fot import get_reigning_foty, get_reigning_fotm
from admin_routes.login_handler import login_protocol
from event_routes.get_event_overview import get_event_overview

# client will error if a connection isn't made within 5 seconds of its first request
SERVER_TIMEOUT = 5000 \

# Initialize flask application
app = Flask(__name__)

# MongoDB configuration
app.config['MONGO_URI'] = os.getenv('MONGO_URI')

# Initialize mongodb databases and collections
client = pymongo.MongoClient(app.config['MONGO_URI'], serverSelectionTimeoutMS=SERVER_TIMEOUT)
eventsDB = client['eventDB']
memberDB = client['memberDB']

events = eventsDB['events']
member = memberDB['members']
admin = memberDB['admins']

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_KEY")
jwt = JWTManager(app)
 
@app.after_request
# Globally modify response headers before requests
def add_header(response):
    # Allowing resource access to URIs specified in .env
    response.headers['Access-Control-Allow-Origin'] = os.getenv('ACAO_URI') if os.getenv('ACAO_URI') else '*'
    return response

# Routes
@app.route("/")
def root():
    return "Welcome to Needle!"

@app.route("/health")
def health_check():
    res = {"data": "healthy"}
    http_status_code = 200

    # DB connection checks
    try:
       client.admin.command('ping')
    except ConnectionFailure:
       res = {"error": "MongoDB connection failed."}
       http_status_code = 500
    except OperationFailure:
        res = {"error": "MongoDB authentication failed."}
        http_status_code = 500

    return jsonify(res), http_status_code

@app.route("/login", methods=["POST"])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    return login_protocol(username, password, member, admin)

@app.route("/shoot/<shoot_id>", methods=["GET"])
def get_shoot_route(shoot_id):
    return get_shoot(shoots, shoot_id)

@app.route("/members/<year>", methods=["GET"])
def get_members_route(year):
    return get_members(member, year)

@app.route("/current-fotw", methods=["GET"])
def get_current_fotw_route():
    return get_current_fotw(fot)

@app.route("past-events", methods=["GET"])
def get_past_events_route():
    return get_past_events(events)

@app.route('/reigning-foty', methods=['GET'])
def get_reigning_foty_route():
    return get_reigning_foty(fot)

@app.route('/reigning-fotm', methods=['GET'])
def get_reigning_fotm_route():
    return get_reigning_fotm(fot)

@app.route("/event-overview", methods=["GET"])
def get_event_overview_route():
    return get_event_overview(events)

@app.route("/semester/<semester_id>", methods=["GET"])
def get_semester_route(semester_id):
    return get_semester(events, semester_id)

if __name__ == "__main__":
    app.run(debug=True)