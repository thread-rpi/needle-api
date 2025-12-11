from flask import jsonify
from bson import ObjectId
from event_routes.event_helpers import serialize_mongo_doc

# events: MongoDB event collection
# event_id: string representing a event id
# returns event data of event corresponding to event_id
def get_event(events, event_id):
    # Check if event_id is a valid format
    try:
        obj_id = ObjectId(event_id)
    except Exception as e:
        return jsonify({"error": "Invalid event id(" + event_id + "): " + str(e)}), 400

    # Search for event of corresponding id
    try:
        event = events.find_one({"_id": obj_id})
    except Exception as e:
        # Something went wrong with the database query
        return jsonify({"error": "Failed to find event of id(" + event_id + "): " + str(e)}), 500

    # If event exists return the data, if not return an error
    if event:
        event = serialize_mongo_doc([event])
        return jsonify({
            "data": event
        })
    else:
        return jsonify({"error": "Event of id(" + event_id + ") not found"}), 404