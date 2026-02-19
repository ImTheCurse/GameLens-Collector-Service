from src.ingestion.collector import collect_capture
from src.ingestion.error import socket_error_payload
from src.socketio_ext import socketio


@socketio.on("capture_event")
def handle_capture(json):
    try:
        if not json:
            raise ValueError("Missing payload")

        image_bytes = json.get("image_data")
        if not image_bytes:
            raise ValueError("image_data is required")

        payload, status = collect_capture(json, image_bytes=image_bytes)
        if status >= 400:
            socketio.emit("error", {"status": status, **payload})
            return

        response_payload = {
            "status": "ok",
            "message": "recieved and stored raw capture.",
        }
        socketio.emit("response", response_payload)
    except Exception as e:
        socketio.emit("error", socket_error_payload(e))


@socketio.on("hello_world")
def handle_hello_world(json):
    print(f"[socket] hello_world received: {json}", flush=True)
    response_payload = {"status": "ok", "message": f"got message: {json.get('msg')}"}
    socketio.emit("response", response_payload)
