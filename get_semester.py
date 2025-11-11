from flask import jsonify
from datetime import datetime, timezone

def get_semester(events, semester_id):
    # map semesters to the corresponding months
    semester_map = {
        "S": (1, 4),
        "A": (5, 8),
        "F": (9, 12)
    }

    # record the how many days are in the last month of each semester
    last_month_days = {
        4: 30,
        8: 31,
        12: 31
    }

    # check that the semester id is valid (S, A, or F)
    if semester_id[0] in semester_map.keys():
        semester = semester_id[0]
    else:
        # otherwise use the current semester
        month = datetime.now(timezone.utc).month
        semester = ""
        for sem, months in semester_map.items():
            if months[0] <= month <= months[1]:
                semester = sem
                break

    try: 
        # make sure that the year is valid, otherwise take current year
        if int(semester_id[1:]) >= 25:  # first year of the club, all data will be in or after 2025
            year = int(semester_id[1:]) + 2000
        else:
            year = datetime.now(timezone.utc).year
            

        # create a range of dates for the semester
        start_date = datetime(year, semester_map[semester][0], 1)
        end_date = datetime(year, semester_map[semester][1], last_month_days[semester_map[semester][1]])

        # create a query 
        query = {
            "date" : {
                "$gte": start_date,
                "$lte": end_date
            }
        }

        # look for all events in the query
        events = list(events.find(query))

        if events:
            # if events found, clean up data and jsonify
            for event in events:
                event['_id'] = str(event['_id']) # cast id to string
                
                # cast all personnel ids to strings
                for i in range(len(event['personnel'])):
                    event['personnel'][i] = str(event['personnel'][i])

                # format date
                if isinstance(event['date'], datetime):
                    event['date'] = event['date'].isoformat()

            return jsonify({
                "data" : events
            }), 200
        else:
            # otherwise, jsonfiy a message saying no events
            return jsonify({
                "message": "no events found"
            }), 500

    except Exception as e:
        # error handling in case this break
        return jsonify({
            "success": False,
            "error": f"Failed to retrieve semester data: {str(e)}"
        }), 500