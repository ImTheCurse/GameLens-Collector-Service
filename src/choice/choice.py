from flasgger import swag_from
from flask import Blueprint, jsonify, request
from psycopg.rows import dict_row
from psycopg.types.json import Json

from src.db import DatabaseConnection
from src.errors import MissingCollectorParam
from src.util import validate_data

Choice = Blueprint("choice", __name__)


@Choice.route("/collect/choice", methods=["POST"])
@swag_from("../docs/choice.yml")
def insert_choice():
    data = request.get_json() or {}
    run_id = data.get("run_id")
    choice_options = data.get("choice_options")
    selected = data.get("selected")

    validate_data(["run_id", "choice_options", "selected"], data)

    try:
        with DatabaseConnection.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO choice (
                        run_id,
                        choice_options,
                        selected
                        )
                        VALUES (%s, %s, %s)
                        RETURNING id;
                        """,
                    (run_id, Json(choice_options), selected),
                )
                choice_id = cur.fetchone()[0]
                conn.commit()

    except Exception as e:
        return jsonify(
            {"error": "Client Side Error", "message": str(e), "type": type(e).__name__}
        ), 400

    return jsonify(
        {"message": "Choice inserted successfully", "choice_id": choice_id}
    ), 200


@Choice.route("/collect/choice", methods=["GET"])
@swag_from("../docs/choice_get.yml")
def get_choice():
    run_id = request.args.get("run_id")
    if not run_id:
        raise MissingCollectorParam("run_id is required")

    try:
        with DatabaseConnection.get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                choices = cur.execute(
                    """SELECT
                        id AS choice_id,
                        run_id,
                        choice_options,
                        selected
                    FROM choice
                    WHERE run_id = %s;
                    """,
                    (run_id,),
                ).fetchall()

    except Exception as e:
        return jsonify(
            {"error": "Client Side Error", "message": str(e), "type": type(e).__name__}
        ), 400

    return jsonify({"data": choices}), 200
