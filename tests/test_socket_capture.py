import pytest
from flask import Flask

from src.ingestion import capture
from src.socketio_ext import init_socketio, socketio


@pytest.fixture()
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["REDIS_URL"] = None
    init_socketio(app)
    return app


@pytest.fixture()
def client(app):
    return socketio.test_client(app)


def _get_event(received, name):
    for event in received:
        if event.get("name") == name:
            return event
    return None


def test_capture_event_success(monkeypatch, client):
    def fake_collect_capture(data, image_bytes):
        assert data["session_id"] == "s1"
        assert data["game_id"] == "g1"
        assert data["captured_at"] == "2025-01-01T00:00:00Z"
        assert image_bytes == b"fake-bytes"
        return {"message": "ok"}, 200

    # Patching the collect_capture in runtime function to avoid
    # inserting data into the DB.
    monkeypatch.setattr(capture, "collect_capture", fake_collect_capture)

    client.emit(
        "capture_event",
        {
            "session_id": "s1",
            "game_id": "g1",
            "captured_at": "2025-01-01T00:00:00Z",
            "image_data": b"fake-bytes",
        },
    )

    received = client.get_received()
    response_event = _get_event(received, "response")
    assert response_event is not None
    assert response_event["args"][0]["status"] == "ok"


def test_capture_event_missing_image_data_emits_error(client):
    client.emit(
        "capture_event",
        {
            "session_id": "s1",
            "game_id": "g1",
            "captured_at": "2025-01-01T00:00:00Z",
        },
    )

    received = client.get_received()
    error_event = _get_event(received, "error")
    assert error_event is not None
    payload = error_event["args"][0]
    assert payload["status"] == 400
    assert "image_data is required" in payload["message"]


def test_capture_event_collect_capture_error(monkeypatch, client):
    def fake_collect_capture(data, image_bytes):
        return {"error": "Client Side Error", "message": "bad data"}, 400

    monkeypatch.setattr(capture, "collect_capture", fake_collect_capture)

    client.emit(
        "capture_event",
        {
            "session_id": "s1",
            "game_id": "g1",
            "captured_at": "2025-01-01T00:00:00Z",
            "image_data": b"fake-bytes",
        },
    )

    received = client.get_received()
    error_event = _get_event(received, "error")
    assert error_event is not None
    payload = error_event["args"][0]
    assert payload["status"] == 400
    assert payload["error"] == "Client Side Error"
