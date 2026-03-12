from flasgger import swag_from
from flask import Blueprint, jsonify, request
from psycopg.rows import dict_row

from src.db import DatabaseConnection
from src.errors import MissingCollectorParam
from src.util import validate_data

Game = Blueprint("game", __name__)


@Game.route("/collect/game", methods=["POST"])
@swag_from("../docs/game.yml")
def insert_game_to_db():
    data = request.get_json() or {}
    game_name = data.get("game_name")
    user_id = data.get("user_id")
    game_version = data.get("game_version")

    validate_data(["game_name", "user_id", "game_version"], data)

    try:
        with DatabaseConnection.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO user_game (
                        user_id,
                        game_name,
                        game_version,
                        version_date
                        )
                        VALUES (%s, %s, %s, NOW())
                        RETURNING id;
                        """,
                    (user_id, game_name, game_version),
                )
                game_id = cur.fetchone()[0]
                conn.commit()

    except Exception as e:
        return jsonify(
            {"error": "Client Side Error", "message": str(e), "type": type(e).__name__}
        ), 400

    return jsonify({"message": "Game inserted successfully", "game_id": game_id}), 200


@Game.route("/collect/game", methods=["GET"])
@swag_from("../docs/game_get.yml")
def get_game():
    game_id = request.args.get("game_id")
    if not game_id:
        raise MissingCollectorParam("game_id is required")

    try:
        with DatabaseConnection.get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                game = cur.execute(
                    """SELECT
                        id AS game_id,
                        user_id,
                        game_name,
                        game_version,
                        version_date
                    FROM user_game
                    WHERE id = %s;
                    """,
                    (game_id,),
                ).fetchall()

    except Exception as e:
        return jsonify(
            {"error": "Client Side Error", "message": str(e), "type": type(e).__name__}
        ), 400

    if not game:
        return jsonify({"error": "Game not found"}), 404

    return jsonify(game), 200
