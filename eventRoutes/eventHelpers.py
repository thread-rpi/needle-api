from bson import ObjectId
from datetime import datetime

def convert_objectid_to_str(obj):
    """
    Recursively convert ObjectId instances to strings in a document.
    """
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid_to_str(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return obj