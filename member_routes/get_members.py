from flask import jsonify
from datetime import datetime, timezone

# member: a member document
# Parses memeber data into a dictionary
def format_member(member):
    member_data = {
        "_id": str(member["_id"]),
        "name": member.get("name", ""),
        "role": member.get("role", ""),
        "year": member.get("year", 0),
        "blurb": member.get("blurb", "")
    }
    return member_data

# members: MongoDb member collection
# year_string: String representing a school year of form [yy]
# returns all member data for the given year
def get_members(members, year_string):
    # Check if string is correct length
    if len(year_string) != 2:
        return jsonify({"error": f"Invalid parameter {year_string}, string not of length 2"}), 400
    
    # Check if string can be converted to an int
    try:
        year = int(year_string)
    except Exception as e:
        return jsonify({"error": f"Invalid parameter {year_string}, string is not an integer"}), 400
    
    # Check if the given year is inbetween 25 (2025) and the current school year
    current_year = datetime.now(timezone.utc).year - 2000
    current_month = datetime.now(timezone.utc).month
    if current_month <= 5:
        current_year -= 1
    if not(year >= 25 and year <= current_year):
        return jsonify({"error": f"Invalid parameter {year_string}, year out of valid range"}), 400

    # Return the data of all members of a given year
    try:
        member_list = list(members.find({"year": year}))
        if len(member_list):
            return jsonify({"data": [format_member(member) for member in member_list]})
        else:
            return jsonify({"message": f"No members for year {year} found"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500