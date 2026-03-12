from flasgger import swag_from
from flask import Blueprint, jsonify, request
from psycopg.rows import dict_row

from src.db import DatabaseConnection
from src.errors import MissingCollectorParam
from src.util import validate_data

Run = Blueprint("run", __name__)


@Run.route("/collect/run", methods=["POST"])
@swag_from("../docs/run.yml")
def insert_run_to_db():
    data = request.get_json() or {}
    game_id = data.get("game_id")
    duration = data.get("duration")

    validate_data(["game_id", "duration"], data)

    try:
        with DatabaseConnection.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO run(
                        game_id,
                        duration
                    )
                    VALUES(%s,%s)
                    RETURNING id;
                    """,
                    (
                        game_id,
                        duration,
                    ),
                )
                run_id = cur.fetchone()[0]
                conn.commit()

    except Exception as e:
        return jsonify(
            {"error": "Client Side Error", "message": str(e), "type": type(e).__name__}
        ), 400

    return jsonify({"message": "Run inserted successfully", "run_id": run_id}), 200


@Run.route("/collect/run", methods=["GET"])
@swag_from("../docs/run_get.yml")
def get_run():
    run_id = request.args.get("run_id")
    if not run_id:
        raise MissingCollectorParam("run_id is required")

    try:
        with DatabaseConnection.get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                run = cur.execute(
                    """SELECT
                        id AS run_id,
                        game_id,
                        duration
                    FROM run
                    WHERE id = %s;
                    """,
                    (run_id,),
                ).fetchone()

    except Exception as e:
        return jsonify(
            {"error": "Client Side Error", "message": str(e), "type": type(e).__name__}
        ), 400

    if not run:
        return jsonify({"error": "Run not found"}), 404

    return jsonify(run), 200
