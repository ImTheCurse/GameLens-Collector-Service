import os
import uuid
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from src.errors import (
    InvalidMediaFormatError,
    MissingUploadFileError,
)
from src.util import UPLOAD_DIR, allowed_file, db, validate_data

Collector = Blueprint("collector", __name__)


@Collector.route("/collect", methods=["POST"])
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

    conn = db.get_connection()
    with conn:
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

    return jsonify({"message": "File uploaded successfully"}), 200
