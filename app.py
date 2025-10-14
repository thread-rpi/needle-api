from flask import Flask, jsonify
import pymongo
from pymongo.errors import ConnectionFailure, OperationFailure
import os
import boto3
from get_event_details import get_details

SERVER_TIMEOUT = 5000 # client will error if a connection isn't made within 5 seconds of its first request

# Initialize flask application
app = Flask(__name__)

# MongoDB Configuration
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
client = pymongo.MongoClient(app.config['MONGO_URI'], serverSelectionTimeoutMS=SERVER_TIMEOUT)

# Initialize databases
eventsDB = client['eventsDB']
shoots = eventsDB['shoot']
events = eventsDB['event']
calendar = eventsDB['calendar']

fotDB = client['fotDB']
fot = fotDB['fot']

memberDB = client['memberDB']
member = memberDB['member']

# set up access to the s3 bucket
app.config["AWS_ACCESS_KEY_ID"] = os.getenv("AWS_ACCESS_KEY_ID")
app.config["AWS_SECRET_ACCESS_KEY"] = os.getenv("AWS_SECRET_ACCESS_KEY")
app.config["S3_REGION"] = os.getenv("S3_REGION")
app.config["S3_BUCKET_NAME"] = os.getenv("S3_BUCKET_NAME")
s3_client = boto3.client(
    's3',
    aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'],
    region_name=app.config['S3_REGION']
)


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

@app.route("/api/events/<event_id>", methods=["GET"])
def get_event_details(event_id):
    return get_details(calendar, events, shoots, event_id, s3_client, app.config["S3_BUCKET_NAME"])


if __name__ == "__main__":
    app.run(debug=True)