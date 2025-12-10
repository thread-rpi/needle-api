from flask import jsonify
from datetime import datetime, timedelta, timezone
from event_routes.event_helpers import serialize_mongo_doc

def get_recent_events(events_collection):
  '''
  An endpoint that provides high level data on the recently past and upcoming Thread events.

  Arguements: 
      events_collection: MongoDB Collection for all Thread events (events collection in EventsDB)

  Returns:
      JSON response with the 3 most recently past events amnd the 4 soonest upcoming events 
  '''
  current = datetime.now(timezone.utc)
  # Find 3 most recent past events
  try:
    past_events = list(events_collection.find({
      "date": {"$lte": current}
    }).sort("date", -1).limit(3))
  except Exception as e:
    return jsonify({
      "error": f"Failed to retrieve past events: {str(e)}"
    }), 500

  # Find 4 soonest upcoming events
  try:
    up_events = list(events_collection.find({
      "date": {"$gte": current}
    }).sort("date", 1).limit(4))
  except Exception as e:
    return jsonify({
      "error": f"Failed to retrieve upcoming events: {str(e)}"
    }), 500

  # convert ObjectId to string for JSON serialization
  past_events = serialize_mongo_doc(past_events)
  up_events = serialize_mongo_doc(up_events)

  return jsonify({
    "data": {
      "upcoming": up_events,
      "past": past_events
    }
  }), 200
