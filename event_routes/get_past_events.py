from flask import jsonify
from datetime import datetime, timezone
from pymongo import DESCENDING
from event_routes.event_helpers import serialize_mongo_doc

def get_past_events(events):
    current = datetime.now(timezone.utc)
    current_iso = current.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    try:
        # return only necessary fields
        projection = {"_id": 1, "title": 1, "date": 1, "location": 1, "type": 1, "cover_image_path": 1}
        # filter for past, non-fotw, published only events
        events_list = list(events.find({
            "$or": [
                {"date": {"$lte": current}},
                {"date": {"$lte": current_iso}}
            ],
            "type": {"$ne": "fotw"},
            "published": True
        }, projection).sort("date", DESCENDING).limit(20))
    
    except Exception as e:
      return jsonify({
          "error": f"Failed to retrieve past events: {str(e)}"
      }), 500

    # serialize the events
    events_list = serialize_mongo_doc(events_list)
    # expose _id as id for response clarity
    for event in events_list:
        event["id"] = event.pop("_id")

    # return a JSON response
    return jsonify({
        "data": {
          "past_events": events_list
        }
    }), 200

   