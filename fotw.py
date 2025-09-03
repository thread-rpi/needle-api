from flask import Flask, jsonify
from datetime import datetime, timedelta
from bson import ObjectId
import pymongo
import boto3
from botocore.exceptions import ClientError
import os

'''
This code is completely untested and should not be used in production.
This is just a proof of concept to show how we could implement a FoTW API.
'''

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

def get_week_range(weeks_ago=0):
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday() + (7 * weeks_ago))
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week.replace(hour=0, minute=0, second=0, microsecond=0), \
           end_of_week.replace(hour=23, minute=59, second=59, microsecond=999999)

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

@app.route('/api/fotw/current', methods=['GET'])
def get_current_fotw():
    return get_fotw_by_week(0)

@app.route('/api/fotw/previous', methods=['GET'])
def get_previous_fotw():
    return get_fotw_by_week(1)

@app.route('/api/fotw/week/<int:weeks_ago>', methods=['GET'])
def get_fotw_by_week(weeks_ago):
    try:
        if weeks_ago < 0:
            return jsonify({"error": "Weeks ago must be a positive integer"}), 400
        
        start_date, end_date = get_week_range(weeks_ago)
        
        query = {
            "date": {"$gte": start_date, "$lte": end_date},
            "featureGroup": {"$exists": True, "$ne": None},
            "featurePosition": {"$exists": True, "$ne": None}
        }
        
        fotw_data = list(shoot_collection.find(query).sort("featurePosition", pymongo.ASCENDING))
        
        if not fotw_data:
            return jsonify({
                "message": f"No FoTW data found for {weeks_ago} weeks ago",
                "week_range": {"start": start_date.isoformat(), "end": end_date.isoformat()}
            }), 404
        
        result = []
        for item in fotw_data:
            item_data = {
                '_id': str(item['_id']),
                'date': item['date'].isoformat() if 'date' in item else None,
                'path': item.get('path', ''),
                'featureGroup': item.get('featureGroup'),
                'featurePosition': item.get('featurePosition'),
                's3_metadata': {}
            }
            
            path_info = parse_s3_path(item.get('path', ''))
            if path_info:
                item_data['s3_metadata'] = path_info
            
            if 'path' in item and item['path']:
                original_path = item['path']
                original_url = generate_presigned_url(app.config['S3_BUCKET_NAME'], original_path)
                item_data['image_url_original'] = original_url
                
                compressed_path = item['path'].replace('/og.jpg', '/compressed.jpg')
                compressed_url = generate_presigned_url(app.config['S3_BUCKET_NAME'], compressed_path)
                if compressed_url and compressed_path != original_path:
                    item_data['image_url_compressed'] = compressed_url
            
            if 'desc' in item:
                item_data['description'] = item['desc']
            
            result.append(item_data)
        
        return jsonify({
            "weeks_ago": weeks_ago,
            "week_range": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "count": len(result),
            "data": result
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)