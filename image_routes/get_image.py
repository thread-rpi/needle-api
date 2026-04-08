from flask import jsonify
from bson import ObjectId
from helpers.serialize import serialize_mongo_doc, serialize_id

# images: MongoDB image collection
# id: string representing a image id
# returns image data of image corresponding to id
def get_image(images, id):
    # Check if id is a valid format
    try:
        obj_id = ObjectId(id)
    except Exception as e:
        return jsonify({"error": "Invalid image id (" + id + "): " + str(e)}), 400

    # Search for image of corresponding id
    try:
        image = images.find_one({"_id": obj_id})
    except Exception as e:
        # Something went wrong with the database query
        return jsonify({"error": "Failed to find image of id (" + id + "): " + str(e)}), 500

    # If image exists return the data, if not return an error
    if image:
        # serialize the image doc
        image = serialize_mongo_doc(image)
        # serialize the id field
        image = serialize_id(image)
        return jsonify({
            "data": image
        })
    else:
        return jsonify({"error": "Image of id (" + id + ") not found"}), 404