from datetime import datetime

import pytest
from flask import Flask, jsonify

from src.db import DatabaseConnection
from src.errors import MissingCollectorParam
from src.ingestion.collector import Collector


class _FakeCursor:
    def __init__(self, executed):
        self._executed = executed

    def execute(self, query, params):
        self._executed.append((query, params))


class _FakeCursorContext:
    def __init__(self, executed):
        self._cursor = _FakeCursor(executed)

    def __enter__(self):
        return self._cursor

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeConnection:
    def __init__(self):
        self.executed = []
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self, *args, **kwargs):
        return _FakeCursorContext(self.executed)

    def commit(self):
        self.committed = True


@pytest.fixture()
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(Collector, url_prefix="/api/v1")

    @app.errorhandler(MissingCollectorParam)
    def handle_collection_error(e):
        return (
            jsonify(
                {
                    "error": e.name,
                    "message": e.description,
                    "status_code": e.code,
                }
            ),
            e.code,
        )

    return app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_insert_session_ignores_swagger_placeholder_optional_timestamp(
    monkeypatch, client
):
    fake_conn = _FakeConnection()
    monkeypatch.setattr(
        DatabaseConnection,
        "get_connection",
        classmethod(lambda cls: fake_conn),
    )

    response = client.post(
        "/api/v1/collect/session",
        json={
            "game_id": "g1",
            "started_at": "2026-03-02T10:30:00Z",
            "ended_at": "string",
            "client_info": {"platform": "windows"},
        },
    )

    assert response.status_code == 200
    assert fake_conn.committed is True
    assert len(fake_conn.executed) == 1

    _, params = fake_conn.executed[0]
    assert isinstance(params[2], datetime)
    assert params[3] is None


def test_insert_session_rejects_invalid_required_timestamp(monkeypatch, client):
    fake_conn = _FakeConnection()
    monkeypatch.setattr(
        DatabaseConnection,
        "get_connection",
        classmethod(lambda cls: fake_conn),
    )

    response = client.post(
        "/api/v1/collect/session",
        json={
            "game_id": "g1",
            "started_at": "string",
        },
    )

    assert response.status_code == 400
    body = response.get_json()
    assert "started_at must be a valid ISO-8601 timestamp string" in body["message"]
    assert fake_conn.executed == []
