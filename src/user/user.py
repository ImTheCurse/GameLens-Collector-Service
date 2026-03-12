import hashlib
import secrets

from flasgger import swag_from
from flask import Blueprint, request

from src.db import DatabaseConnection
from src.util import validate_data

User = Blueprint("user", __name__)


@User.route("/user/insert", methods=["POST"])
@swag_from("../docs/user_insert.yml")
def insert_user():
    data = request.get_json()
    validate_data(["username", "password"], data)

    salt = secrets.token_bytes(16)
    password_hash = hashlib.sha256(salt + data["password"].encode("utf-8")).hexdigest()
    stored_password = f"{salt.hex()}{password_hash}"

    try:
        with DatabaseConnection.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                       INSERT INTO users(username,user_password)
                       VALUES(%s,%s)
                       RETURNING id
                        ;
                    """,
                    (data["username"], stored_password),
                )
                user_id = cur.fetchone()[0]
                conn.commit()

    except Exception as e:
        return {
            "error": "Client Side Error",
            "message": str(e),
            "type": type(e).__name__,
        }, 400

    return {
        "message": f"user {data['username']} was inserted successfuly. ",
        "id": user_id,
    }


@User.route("/user", methods=["GET"])
@swag_from("../docs/get_user.yaml")
def get_user():
    username = request.args.get("username")
    if not username:
        return {"error": "Missing username parameter"}, 400

    try:
        with DatabaseConnection.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                       SELECT id,username FROM users WHERE username = %s
                    """,
                    (username,),
                )
                user = cur.fetchone()
                if not user:
                    return {"error": "User not found"}, 404
                return {"username": user[0]}
    except Exception as e:
        return {
            "error": "Client Side Error",
            "message": str(e),
            "type": type(e).__name__,
        }, 400
