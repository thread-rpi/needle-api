from flask import Flask, jsonify
import certifi
import pymongo
import os
import json
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv, dotenv_values 

app = Flask(__name__)
load_dotenv()

app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
app.config['AWS_ACCESS_KEY_ID'] = os.getenv('AWS_ACCESS_KEY_ID')
app.config['AWS_SECRET_ACCESS_KEY'] = os.getenv('AWS_SECRET_ACCESS_KEY')
app.config['S3_BUCKET_NAME'] = os.getenv('S3_BUCKET_NAME', 'event-image-bucket')
app.config['S3_REGION'] = os.getenv('S3_REGION', 'us-east-1')

client = pymongo.MongoClient(app.config['MONGO_URI'], tls=True, tlsCAFile=certifi.where())
# print(client.server_info())

db = client['eventsDB']
events = db['event']
shoots = db['shoot']
calendar = db['calendar']

s3_client = boto3.client(
    's3',
    aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'],
    region_name=app.config['S3_REGION']
)

# can't get to the server yet so simulating a dummy response
def format_JSON_response(event):
    d = {}
    for key in event.keys():
        d[key] = event[key]
    # Query S3 bucket to get images, count the number of images and get the file path
    num_imgs = 0                        # dummy value
    file_path = "example/file/path"     # dummy value
    d["num_imgs"] = num_imgs
    d["img_path"] = file_path

    data = {
        data: d
    }

    return json.dumps(data)

# Format:
# {
#     "data" : [
#         {"name" : "ObjectID('68cb5143de01bc3e473c0667')", "path" : "s3://thread-s3-dev/2025/10/25/coolEvent", "desc" : "Placeholder description for coolEvent", "num_imgs" : "10", "img_path" : "example/folder/here"}
#     ]
# }