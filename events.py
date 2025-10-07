from flask import Flask
import pymongo
from bson import json_util
from bson.objectid import ObjectId
import os
import boto3
from dotenv import load_dotenv 

app = Flask(__name__)
load_dotenv()

# initialize environment variables
app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
app.config['AWS_ACCESS_KEY_ID'] = os.getenv('AWS_ACCESS_KEY_ID')
app.config['AWS_SECRET_ACCESS_KEY'] = os.getenv('AWS_SECRET_ACCESS_KEY')
app.config['S3_BUCKET_NAME'] = os.getenv('S3_BUCKET_NAME', 'event-image-bucket')
app.config['S3_REGION'] = os.getenv('S3_REGION', 'us-east-1')

# set up access to the Mongo Database
client = pymongo.MongoClient(app.config['MONGO_URI'], server_api=pymongo.server_api.ServerApi('1'))

# define our mongo variables
db = client['eventsDB']
events = db['event']
shoots = db['shoot']
calendar = db['calendar']

# set up access to the s3 bucket
s3_client = boto3.client(
    's3',
    aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'],
    region_name=app.config['S3_REGION']
)

# find which database the given event is in by querying calendar
def query_calendar(event_id):
    event = calendar.find_one({"_id": ObjectId(event_id)})
    if (event):
        if (event["type"] == "event" or event["type"] == "external"):
            return "event"
        elif (event["type" == "shoot"]):
            return "shoot"
        return "Event type not recognized"
    return "Event not found"

def get_image_path(event_path):
    # ensure correct event_date format
    if (event_path[-1] != "/"):
        event_path += "/"

    # get the number of images in the filepath
    response = s3_client.list_objects_v2(Bucket=app.config["S3_BUCKET_NAME"], Prefix=event_path, Delimiter= "/")
    img_count = response["KeyCount"]

    return img_count

"""this returns a JSON response in the form of:
{
    "data" : {
        "name"      : "ObjectID",
        "path"      : "event_path",
        "desc"      : "description",
        "num_img"   : "num"
    }
}"""
def format_JSON_response(event_id, event_db):
    # find image given the id
    if (event_db == "event"):
        event = events.find_one({"_id": ObjectId(event_id)})
    elif (event_db == "shoot"):
        event = events.find_one({"_id": ObjectId(event_id)})

    # get image count variable, add it to event data
    substring_val = 0
    if ("s3://thread-s3-dev/" in event["path"]):
        substring_val = len("s3://thread-s3-dev/")  # remove the first chunk, AWS doesn't need it
    path = event["path"][substring_val:]
    count = get_image_path(path)
    event["num_img"] = count

    # convert ObjectId to string for easier jsonify
    event["_id"] = str(event["_id"])

    # set up the dictionary as "data" : {event info} 
    jdict = {"data" : event}

    # convert to json
    return json_util.dumps(jdict)

def main(event_id):
    database = query_calendar(event_id)
    return format_JSON_response(event_id, database)