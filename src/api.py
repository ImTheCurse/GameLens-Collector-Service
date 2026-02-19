import os

from dotenv import load_dotenv
from flasgger import Swagger
from flask import Flask, jsonify

# Don't remove "useless" import, decorator registration is at runtime.
import src.ingestion.capture  # noqa: F401
from src.errors import FileUploadError, MissingCollectorParam
from src.ingestion.collector import Collector
from src.socketio_ext import init_socketio, socketio
from src.util import UPLOAD_DIR, UPLOAD_SIZE, init_db

load_dotenv()

app = Flask(__name__)
app.config["REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379/0")
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
app.config["MAX_CONTENT_LENGTH"] = UPLOAD_SIZE

init_socketio(app)
init_db()
swagger = Swagger(app)
app.register_blueprint(Collector, url_prefix="/api/v1")


@app.errorhandler(MissingCollectorParam)
@app.errorhandler(FileUploadError)
def handle_collection_error(e):
    """
    handles error exceptions, and returns to the user a json response with the error metadata.
    """
    return jsonify(
        {
            "error": e.name,  # e.g., "Payload Too Large"
            "message": e.description,  # The custom description defined above
            "status_code": e.code,  # The code defined in the class (413, 415, etc.)
        }
    ), e.code


if __name__ == "__main__":
    socketio.run(app, port=8000)
