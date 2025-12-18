from flask import jsonify
from datetime import datetime, timezone
from pymongo import DESCENDING
from event_routes.event_helpers import serialize_mongo_doc

def get_past_events(events):
    current = datetime.now(timezone.utc)
    try:
        # get 20 most recent events
        events_list = list(events.find({
            "date": {"$lte": current}
        }).sort("date", DESCENDING).limit(20))
    
    except Exception as e:
      return jsonify({
          "error": f"Failed to retrieve past events: {str(e)}"
      }), 500

    # serialize the events
    events_list = serialize_mongo_doc(events_list)

    # return a JSON response
    return jsonify({
        "data": {
          "past_events": events_list
        }
    }), 200

   