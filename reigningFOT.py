from flask import Flask, jsonify
from datetime import datetime, timedelta
from bson import ObjectId
import pymongo
import boto3
from botocore.exceptions import ClientError
import os

app = Flask(__name__)
app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
app.config['AWS_ACCESS_KEY_ID'] = os.getenv('AWS_ACCESS_KEY_ID')
app.config['AWS_SECRET_ACCESS_KEY'] = os.getenv('AWS_SECRET_ACCESS_KEY')
app.config['S3_BUCKET_NAME'] = os.getenv('S3_BUCKET_NAME', 'your-fotw-bucket')
app.config['S3_REGION'] = os.getenv('S3_REGION', 'us-east-1')

client = pymongo.MongoClient(app.config['MONGO_URI'])
db = client['thread_site_db']
shoot_collection = db['shoot_collection']

s3_client = boto3.client(
    's3',
    aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'],
    region_name=app.config['S3_REGION']
)

def parse_s3_path(path):
    parts = path.strip('/').split('/')
    if len(parts) >= 6:
        try:
            year = int(parts[0])
            month = int(parts[1])
            day = int(parts[2])
            title = parts[3]
            index = int(parts[4])
            filename = parts[5]
            compression = 'original' if filename.lower() == 'og.jpg' else 'compressed'
            
            return {
                'year': year,
                'month': month,
                'day': day,
                'title': title,
                'index': index,
                'compression': compression,
                'filename': filename,
                'full_path': path
            }
        except (ValueError, IndexError, TypeError):
            return None
    return None

def generate_presigned_url(bucket_name, object_name, expiration=3600):
    try:
        if object_name.startswith('/'):
            object_name = object_name[1:]
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except ClientError:
        return None
    return response

def format_item(item: dict):
    item_data = {
        '_id': str(item['_id']),
        'date': item['date'].isoformat() if 'date' in item else None,
        'path': item.get('path', ''),
        'featureGroup': item.get('featureGroup'),
        'featurePosition': item.get('featurePosition'),
        's3_metadata': {}
    }

    path_info = parse_s3_path(item.get('path', ''))
    if path_info: item_data['s3_metadata'] = path_info

    if 'path' in item and item['path']:
        original_path = item['path']
        original_url = generate_presigned_url(app.config['S3_BUCKET_NAME'], original_path)
        if original_url:
            item_data['image_url_original'] = original_url
        if original_path.endswith("og.jpg"):
            compressed_path = original_path.replace("og.jpg", "compressed.jpg")
            compressed_url = generate_presigned_url(app.config['S3_BUCKET_NAME'], compressed_path)
            if compressed_url and compressed_path != original_path:
                item_data['image_url_compressed'] = compressed_url

    if 'desc' in item: item_data['description'] = item['desc']

    return item_data

@app.route('/api/fotw/reigningFOTY', methods=['GET'])
def get_reigning_fotY():
    try:
        item = shoot_collection.find_one({"yearWin": True}, sort=[("date", pymongo.DESCENDING)])
        if not item: return jsonify({"message": "No FoTY winners found"}), 404
        return jsonify({"count": 1, "data": [format_item(item)]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/fotw/reigningFOTMs', methods=['GET'])
def get_reigning_fotMs():
    try:
        fotMs_data = list(shoot_collection.find({"FOTM": True}).sort("date", pymongo.DESCENDING).limit(3))
        if not fotMs_data: return jsonify({"message": "No FoTM winners found"}), 404
        return jsonify({"count": len(fotMs_data), "data": [format_item(doc) for doc in fotMs_data]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)