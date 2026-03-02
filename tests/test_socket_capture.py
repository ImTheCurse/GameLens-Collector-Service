import pytest
from flask import Flask

from src.ingestion import capture
from src.socketio_ext import init_socketio, socketio


@pytest.fixture()
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    init_socketio(app)
    return app


@pytest.fixture()
def client(app):
    return socketio.test_client(app)


def test_capture_event_success(monkeypatch, client):
    def fake_collect_capture(data, image_bytes):
        return {"message": "ok"}, 200

    monkeypatch.setattr(capture, "collect_capture", fake_collect_capture)

    # 1. Capture the return value of emit by setting callback=True
    response = client.emit(
        "capture_event",
        {
            "session_id": "s1",
            "game_id": "g1",
            "captured_at": "2025-01-01T00:00:00Z",
            "image_data": b"fake-bytes",
        },
        callback=True,  # This tells the client to wait for the return value
    )

    # 2. Assert against the 'response' variable directly
    assert response is not None
    assert response["status"] == "ok"


def test_capture_event_missing_image_data_emits_error(client):
    # Capture return value from the exception/ValueError path
    response = client.emit(
        "capture_event",
        {
            "session_id": "s1",
            "game_id": "g1",
            "captured_at": "2025-01-01T00:00:00Z",
        },
        callback=True,
    )

    assert response is not None
    assert response["status"] == "error" or response["status"] == 400
    assert "image_data is required" in response["message"]


def test_capture_event_collect_capture_error(monkeypatch, client):
    def fake_collect_capture(data, image_bytes):
        return {"error": "Client Side Error", "message": "bad data"}, 400

    monkeypatch.setattr(capture, "collect_capture", fake_collect_capture)

    response = client.emit(
        "capture_event",
        {
            "session_id": "s1",
            "game_id": "g1",
            "captured_at": "2025-01-01T00:00:00Z",
            "image_data": b"fake-bytes",
        },
        callback=True,
    )

    assert response is not None
    assert response["status"] == "error"
    assert response["error"] == "Client Side Error"
