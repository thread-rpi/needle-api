from flask import jsonify
from flask_jwt_extended import get_jwt_identity, create_access_token
from datetime import timedelta



def refresh_token(TOKEN_EXPIRATION_TIME):
    """
    Refresh endpoint to get a new access token using a valid refresh token.
    Both tokens expire after TOKEN_EXPIRATION_TIME hours.
    """
    current_user = get_jwt_identity()
    new_access_token = create_access_token(
        identity=current_user,
        expires_delta=timedelta(hours=TOKEN_EXPIRATION_TIME)
    )
    return jsonify({
        "data": {
            "access_token": new_access_token
        }
    }), 200

