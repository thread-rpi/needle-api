from flask import jsonify
from pymongo import DESCENDING

def get_recent_content(calendar, events, shoots):
    try:
        # get 20 most recent events
        events_list = calendar.find().sort("date", DESCENDING).limit(20)

        combined_documents = []

        # create an array of the documents of each event from the relevant database
        document_count = 0
        for event in events_list:
            if (event["type"] == "event" or event["type"] == "external"):
                document = events.find_one({"_id": event["_id"]})
            elif (event["type"] == "shoot"):
                document = shoots.find_one({"_id": event["_id"]})
            else:
                print("event type not recognized") # debugging print statement
                continue

            # convert ObjectIDs to strings
            event["_id"] = str(event["_id"])
            document["_id"] = str(document["_id"])

            # create the union and push it into an array
            combined = {**event, **document}
            combined_documents.append(combined)

            document += 1

        if (len(combined_documents) != document_count):
            return jsonify({
                "success": False,
                "message": "number of events found is not correct, more events found from calendar then found in collections"
            })

        return jsonify({
            "data": combined_documents
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to retrieve recent events: {str(e)}"
        }), 500