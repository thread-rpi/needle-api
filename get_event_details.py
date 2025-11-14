from flask import jsonify
from bson.objectid import ObjectId

def get_details(events, event_id):
    try:
        # find the event in the calendar
        event = events.find_one({"_id": ObjectId(event_id)})

        # check to see if the event exists
        if not event:
            return jsonify({
                "message": "No matching event found"
            }), 500

        # convert event id to a string
        event["_id"] = str(event["_id"])

        # convert personnel array to string objects
        for i in range(len(event["personnel"])):
            event["personnel"][i] = str(event["personnel"][i])


        return jsonify({
            "data": event
        }), 200
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to retrieve event details: {str(e)}"
        }), 500