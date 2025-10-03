from flask import jsonify

def format_member(member):
    member_data = {
        "_id": str(member["_id"]),
        "name": member.get("name", ""),
        "role": member.get("role", ""),
        "year": member.get("year", 0),
        "blurb": member.get("blurb", "")
    }
    return member_data

def get_members(members, year_string):
    if len(year_string) != 2:
        return jsonify({"error": f"Invalid parameter {year_string}"}), 400
    
    try:
        year = int(year_string)
    except Exception as e:
        return jsonify({"error": f"Invalid parameter {year_string}"}), 400
    
    try:
        member_list = list(members.find({"year": year}))
        if len(member_list):
            return jsonify({"data": [format_member(member) for member in member_list]})
        else:
            return jsonify({"message": f"No members for year {year} found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500