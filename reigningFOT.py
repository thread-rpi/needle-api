from flask import jsonify
from datetime import datetime

def serialize_mongo_doc(doc):
    """Convert MongoDB ObjectId and datetime to serializable format"""
    doc['_id'] = str(doc['_id'])
    if isinstance(doc.get('date'), datetime):
        doc['date'] = doc['date'].isoformat()
    return doc


def reigning_foty(fot_collection):
    """
    Get the reigning Fit of the Year (FOTY)
    - Returns the most recent FOTY based on date
    """
    try:
        foty = fot_collection.find_one(
            {"yearWin": True},
            sort=[("date", -1)]
        )
        if foty:
            foty = serialize_mongo_doc(foty)
            return jsonify({
                "success": True,
                "reigning_foty": foty
            }), 200
        else:
            return jsonify({
                "message": "no reigning Fit of the Year found."
            }), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def reigning_fotm(fot_collection):
    """
    Get the 3 most recent Fits of the Month (FOTM)
    """
    try:
        fotm_list = list(
            fot_collection.find({"monthWin": True}).sort("date", -1).limit(3)
        )
        if fotm_list:
            fotm_list = [serialize_mongo_doc(f) for f in fotm_list]
            return jsonify({
                "success": True,
                "reigning_fotm": fotm_list,
                "count": len(fotm_list)
            }), 200
        else:
            return jsonify({"message": "no reigning Fits of the Month found."}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
