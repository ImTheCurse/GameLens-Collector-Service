from werkzeug.exceptions import HTTPException

from src.socketio_ext import socketio


@socketio.on_error()
def socket_error_payload(error, default_status=400):
    """
    Normalize exceptions into a socket-friendly error payload.
    """
    if isinstance(error, HTTPException):
        return {
            "error": error.name,
            "message": error.description,
            "type": type(error).__name__,
            "status": error.code,
        }

    return {
        "error": "Client Error",
        "message": str(error),
        "type": type(error).__name__,
        "status": default_status,
    }
