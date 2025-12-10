from flask import jsonify
from bson import ObjectId
from datetime import datetime, timedelta, timezone

def current_fotw(fot_collection):
    """
    Get the current Fit of the Week (FOTW) based on date range (Sunday to Saturday)
    
    Args:
        fot_collection: MongoDB collection for FOTW items (fot collection in fotDB)
        
    Returns:
        JSON response with the current FOTW or error message
    """
    try:
        # Get current date in UTC
        now_utc = datetime.now(timezone.utc)
        
        # Calculate current week range (Sunday to Saturday)
        # Sunday is weekday 6, Saturday is weekday 5
        current_weekday = now_utc.weekday()  # Monday=0, Sunday=6
        
        # Calculate days to subtract to get to Sunday (start of week)
        days_to_sunday = (current_weekday + 1) % 7
        sunday = now_utc - timedelta(days=days_to_sunday)
        sunday_start = sunday.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # End of week
        saturday_end = sunday_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        print(f"Looking for FOTW between {sunday_start} and {saturday_end}")  # Debug logging
        
        # Query for FOTW items in the current week
        query = {
            "date": {
                "$gte": sunday_start.isoformat(),
                "$lte": saturday_end.isoformat()
            }
        }
        
        # Find FOTW items for current week
        fotw_items = list(fot_collection.find(query))
        
        if fotw_items:
            # Convert MongoDB objects to JSON-serializable format
            for item in fotw_items:
                item['_id'] = str(item['_id'])
                # Convert date to ISO format string if it's a datetime object
                if isinstance(item['date'], datetime):
                    item['date'] = item['date'].isoformat()
            
            # Return all found items for the current week
            return jsonify({
                "success": True,
                "current_fotw": fotw_items,
                "week_range": {
                    "start": sunday_start.isoformat(),
                    "end": saturday_end.isoformat()
                },
                "count": len(fotw_items)
            }), 200
        else:
            # Return the specified error message format
            return jsonify({
                "message": "no data/images found for the current week.",
                "date": now_utc.isoformat(),
                "week_range": {
                    "start": sunday_start,
                    "end": saturday_end
                }
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to retrieve current FOTW: {str(e)}"
        }), 500