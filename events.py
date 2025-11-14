from flask import Flask, jsonify
import pymongo
import os
from dotenv import load_dotenv, dotenv_values 

app = Flask(__name__)
load_dotenv()

app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
app.config['AWS_ACCESS_KEY_ID'] = os.getenv('AWS_ACCESS_KEY_ID')
app.config['AWS_SECRET_ACCESS_KEY'] = os.getenv('AWS_SECRET_ACCESS_KEY')
app.config['S3_BUCKET_NAME'] = os.getenv('S3_BUCKET_NAME', 'your-fotw-bucket')
app.config['S3_REGION'] = os.getenv('S3_REGION', 'us-east-2')

client = pymongo.MongoClient(app.config['MONGO_URI'])
print(client)
