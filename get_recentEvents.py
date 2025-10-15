from flask import jsonify
from bson import ObjectId
from datetime import datetime, timedelta, timezone

def get_recentEvents(calander_collection):
    current = datetime.now(timezone.utc)

    try:
        # Find 3 most recent past events
        past_events = list(calander_collection.find({
            "type": "event",
            "date": {"$lte": current}
        }).sort("date", -1).limit(3))

        # Find 4 soonest upcoming events
        up_events = list(calander_collection.find({
            "type": "event", 
            "date": {"$gte": current}
        }).sort("date", 1).limit(4))

        # Convert ObjectId to string for JSON serialization
        for event in past_events + up_events:
            event['_id'] = str(event['_id'])
            # Convert date to ISO format if it's a datetime object
            if isinstance(event.get('date'), datetime):
                event['date'] = event['date'].isoformat()

        
        return jsonify({
            "success": True,
            "events": up_events + past_events  
        }), 200

    except Exception as e:
        # Fixed error response - use jsonify() not jsonify.dumps()
        error_response = {
            "success": False,
            "events": [],
            "error": "No events to show"
        }
        return jsonify(error_response), 500