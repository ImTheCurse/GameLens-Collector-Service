import base64
import os
import uuid
from datetime import datetime, timezone

from flasgger import swag_from
from flask import Blueprint, jsonify, request
from psycopg.rows import dict_row
from werkzeug.utils import secure_filename

from src.db import DatabaseConnection
from src.errors import (
    InvalidMediaFormatError,
    MissingCollectorParam,
    MissingUploadFileError,
)
from src.util import UPLOAD_DIR, allowed_file, validate_data


def _parse_timestamp(value, field_name, required=True):
    """Parse ISO-8601 timestamp strings into datetime objects for DB inserts."""
    if value is None:
        if required:
            raise MissingCollectorParam(f"{field_name} is required")
        return None

    if isinstance(value, datetime):
        return value

    if not isinstance(value, str):
        raise MissingCollectorParam(
            f"{field_name} must be a valid ISO-8601 timestamp string"
        )

    raw_value = value.strip()
    if not raw_value:
        if required:
            raise MissingCollectorParam(f"{field_name} is required")
        return None

    # Swagger placeholders should not be treated as real timestamps.
    if raw_value.lower() in {"string", "null", "none"}:
        if required:
            raise MissingCollectorParam(
                f"{field_name} must be a valid ISO-8601 timestamp string"
            )
        return None

    normalized_value = (
        f"{raw_value[:-1]}+00:00" if raw_value.endswith("Z") else raw_value
    )

    try:
        return datetime.fromisoformat(normalized_value)
    except ValueError as exc:
        raise MissingCollectorParam(
            f"{field_name} must be a valid ISO-8601 timestamp string"
        ) from exc


def collect_capture(data, image_bytes):
    validate_data(["session_id", "game_id", "captured_at", "capture_index"], data)

    # Required fields
    capture_id = str(uuid.uuid4())
    captured_at = _parse_timestamp(data.get("captured_at"), "captured_at")
    session_id = data["session_id"]
    game_id = data["game_id"]
    capture_index = data["capture_index"]
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
                    image_width,
                    capture_index
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
                    """,
                    (
                        capture_id,
                        image_bytes,
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
                        capture_index,
                    ),
                )
            conn.commit()
    except Exception as e:
        return {
            "error": "Client Side Error",
            "message": str(e),
            "type": type(e).__name__,
        }, 400

    return {"message": "File uploaded successfully"}, 200


Collector = Blueprint("collector", __name__)


@Collector.route("/collect", methods=["POST"])
@swag_from("../docs/collect.yml")
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

    payload, status = collect_capture(data, file.read())
    return jsonify(payload), status


@Collector.route("/collect", methods=["GET"])
@swag_from("../docs/collection_get.yml")
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
