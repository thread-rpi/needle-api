from bson import ObjectId
from datetime import datetime

def serialize_mongo_doc(obj):
    """
    Recursively convert ObjectId instances to strings in a document.
    """
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: serialize_mongo_doc(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_mongo_doc(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return obj