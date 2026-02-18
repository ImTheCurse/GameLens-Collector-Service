import base64
import os
import uuid
from datetime import datetime, timezone

from flasgger import swag_from
from flask import Blueprint, jsonify, request
from psycopg.rows import dict_row
from psycopg.types.json import Json
from werkzeug.utils import secure_filename

from src.db import DatabaseConnection
from src.errors import (
    InvalidMediaFormatError,
    MissingCollectorParam,
    MissingUploadFileError,
)
from src.util import UPLOAD_DIR, allowed_file, validate_data

Collector = Blueprint("collector", __name__)


@Collector.route("/collect", methods=["POST"])
@swag_from("docs/collect.yml")
def collect():
    # check if the post request has the file part
    if "file" not in request.files:
        raise MissingUploadFileError()

    file = request.files["file"]
    filename = str(file.filename)
    # If the user does not select a file, the browser submits an empty file without a filename.
    if file.filename == "":
        raise MissingUploadFileError()

    if file and allowed_file(filename):
        filename = secure_filename(filename)
        file.save(os.path.join(UPLOAD_DIR, filename))

        file.seek(0)
    else:
        raise InvalidMediaFormatError()

    data = request.form

    validate_data(["session_id", "game_id", "captured_at"], data)

    # Required fields
    capture_id = str(uuid.uuid4())
    captured_at = data.get("captured_at")
    session_id = data["session_id"]
    game_id = data["game_id"]
    received_at = datetime.now(timezone.utc)

    # Optional Fields
    run_id = data.get("run_id")
    mouse_x = data.get("mouse_x")
    mouse_y = data.get("mouse_y")
    screenshot_hash = data.get("screenshot_hash")
    image_width = data.get("image_width")
    image_height = data.get("image_height")

    try:
        with DatabaseConnection.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO raw_capture
                    (
                    capture_id,
                    image_data,
                    game_id,
                    session_id,
                    captured_at,
                    received_at,
                    run_id,
                    mouse_x,
                    mouse_y,
                    screenshot_hash,
                    image_height,
                    image_width
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
                    """,
                    (
                        capture_id,
                        file.read(),
                        game_id,
                        session_id,
                        captured_at,
                        received_at,
                        run_id,
                        mouse_x,
                        mouse_y,
                        screenshot_hash,
                        image_height,
                        image_width,
                    ),
                )
            conn.commit()
    except Exception as e:
        return jsonify(
            {"error": "Client Side Error", "message": str(e), "type": type(e).__name__}
        ), 400
    return jsonify({"message": "File uploaded successfully"}), 200


@Collector.route("/collect", methods=["GET"])
@swag_from("docs/collection_get.yml")
def get_raw_collection():
    session_id = request.args.get("session_id")
    game_id = request.args.get("game_id")

    if not game_id or not session_id:
        raise MissingCollectorParam("session_id and game_id are required")

    try:
        with DatabaseConnection.get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                res = cur.execute(
                    """SELECT
                        captured_at,
                        game_id,
                        run_id,
                        image_data,
                        image_height,
                        image_width
                    FROM raw_capture
                    WHERE game_id = %s and session_id = %s;
                    """,
                    (game_id, session_id),
                ).fetchall()
                conn.commit()
    except Exception as e:
        return jsonify(
            {"error": "Client Side Error", "message": str(e), "type": type(e).__name__}
        ), 400
    if res:
        for row in res:
            if row.get("image_data"):
                # Convert bytes to base64 string
                row["image_data"] = base64.b64encode(row["image_data"]).decode("utf-8")

    return jsonify({"data": res}), 200


@Collector.route("/collect/game", methods=["POST"])
@swag_from("docs/game.yml")
def insert_game_to_db():
    # Required fields
    data = request.json
    game_id = str(uuid.uuid4())
    name = data.get("name")
    created_at = data.get("created_at")

    if not name or not created_at:
        raise MissingCollectorParam("name and created_at are required")

    plugin_metadata = data.get("plugin_metadata")
    game_metadata = data.get("game_metadata")

    try:
        with DatabaseConnection.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO game (
                        game_id,
                        name,
                        created_at,
                        plugin_metadata,
                        game_metadata
                        )
                        VALUES (%s, %s, %s,%s,%s);""",
                    (
                        game_id,
                        name,
                        created_at,
                        Json(plugin_metadata),
                        Json(game_metadata),
                    ),
                )
                conn.commit()

    except Exception as e:
        return jsonify(
            {"error": "Client Side Error", "message": str(e), "type": type(e).__name__}
        ), 400

    return jsonify({"message": "Game inserted successfully", "game_id": game_id}), 200


@Collector.route("/collect/session", methods=["POST"])
@swag_from("docs/session.yml")
def insert_session_to_db():
    # Required fields
    data = request.json
    session_id = str(uuid.uuid4())
    game_id = data.get("game_id")
    started_at = data.get("started_at")

    if not game_id or not started_at:
        raise MissingCollectorParam("game_id and started_at are required")

    # Optional fields
    ended_at = data.get("ended_at")
    client_info = data.get("client_info")

    try:
        with DatabaseConnection.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO session(session_id,game_id,started_at,ended_at,client_info)
                    VALUES(%s,%s,%s,%s,%s);
                    """,
                    (session_id, game_id, started_at, ended_at, Json(client_info)),
                )
                conn.commit()

    except Exception as e:
        return jsonify(
            {"error": "Client Side Error", "message": str(e), "type": type(e).__name__}
        ), 400

    return jsonify(
        {"message": "Session inserted successfully", "session_id": session_id}
    ), 200
