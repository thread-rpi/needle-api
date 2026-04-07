from flask import jsonify
from bson import ObjectId
from helpers.serialize import serialize_mongo_doc, serialize_id

# members: MongoDB member collection
# id: string representing a member id
# returns member data of member corresponding to id
def get_member(members, id):
    # Check if id is a valid format
    try:
        obj_id = ObjectId(id)
    except Exception as e:
        return jsonify({"error": "Invalid member id (" + id + "): " + str(e)}), 400

    # Search for member of corresponding id
    try:
        member = members.find_one({"_id": obj_id})
    except Exception as e:
        # Something went wrong with the database query
        return jsonify({"error": "Failed to find member of id (" + id + "): " + str(e)}), 500

    # If member exists return the data, if not return an error
    if member:
        # serialize the member doc
        member = serialize_mongo_doc([member])
        # serialize the id field
        member = serialize_id(member)
        return jsonify({
            "data": member
        })
    else:
        return jsonify({"error": "Member of id (" + id + ") not found"}), 404