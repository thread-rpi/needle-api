from flask import jsonify
from pymongo import DESCENDING

def get_recent_content(events):
    try:
        # get 20 most recent events
        events_list = events.find().sort("date", DESCENDING).limit(20)

        # convert the event ids to strings
        for i in range(len(events_list)):
            events_list[i]["_id"] = str(events_list[i]["_id"])

        # return a JSON response
        return jsonify({
            "data": events_list
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to retrieve recent events: {str(e)}"
        }), 500