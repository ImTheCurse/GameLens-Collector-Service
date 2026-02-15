import os
from typing import List

from src.db import DatabaseConnection
from src.errors import MissingCollectorParam

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
UPLOAD_SIZE = 25 * 1000 * 1000  # 25 MB
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Creates the folder if it doesn't exist

conn_str = os.environ.get("PGSQL_CONN")
if not conn_str:
    raise ValueError("PGSQL_CONN environment variable is not set")

db = DatabaseConnection(conn_str)


def allowed_file(filename: str):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_data(required_keys: List[str], req_data):
    """
    Ensures all required keys exist in the request JSON.
    Uses Python sets for efficient comparison.
    """
    data = req_data or {}

    # Convert both to sets to use set math
    required_set = set(required_keys)
    provided_set = set(data.keys())

    # The '-' operator finds items in 'required' that are missing from 'provided'
    missing = required_set - provided_set

    if missing:
        raise MissingCollectorParam(
            f"Missing parameter(s): {', '.join(sorted(missing))}"
        )
