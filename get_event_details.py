from flask import jsonify
from bson.objectid import ObjectId

def get_details(calendar, events, shoots, event_id, s3_client, bucket_name):
    try:
        # find the event in the calendar
        event = calendar.find_one({"_id": ObjectId(event_id)})

        # find which collection has the event details
        if (event):
            if (event["type"] == "event" or event["type"] == "external"):
                collection = events
            elif (event["type"]) == "shoot":
                collection = shoots
            else:
                return jsonify({
                    "message": "Event type not recognized"
                }), 500
        else:
            return jsonify({
                "message": "No matching event found"
            }), 500
        
        # get the event details from the collection
        event = collection.find_one({"_id": ObjectId(event_id)})

        # remove the first chunk from the path variable in event, AWS doesn't need it
        substring_val = 0
        if ("s3://thread-s3-dev/" in event["path"]):
            substring_val = len("s3://thread-s3-dev/")
        path = event["path"][substring_val:]

        # ensure correct formatting
        if(path[-1] != "/"):
            path += "/"

        # get the number of images in the filepath
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=path, Delimiter="/")
        if ("KeyCount" in response.keys()):
            img_count = response["KeyCount"]
        else:
            return jsonify({
                "message": "s3 returned unexpected results"
            }), 500
        
        event["num_img"] = img_count
        event["_id"] = str(event["_id"])

        return jsonify({
            "data": event
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to retrieve event details: {str(e)}"
        }), 500