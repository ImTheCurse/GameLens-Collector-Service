from dotenv import load_dotenv
from flasgger import Swagger
from flask import Flask, jsonify

# Don't remove "useless" import, decorator registration is at runtime.
import src.ingestion.capture  # noqa: F401
from src.choice.choice import Choice
from src.errors import FileUploadError, MissingCollectorParam
from src.game.game import Game
from src.ingestion.collector import Collector
from src.run.run import Run
from src.socketio_ext import init_socketio, socketio
from src.user.user import User
from src.util import UPLOAD_DIR, UPLOAD_SIZE, init_db

load_dotenv()
print("loaded environment variables.", flush=True)

app = Flask(__name__)
print("initialized flask app.", flush=True)
init_socketio(app)
print("initialized flask socket.io.", flush=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
app.config["MAX_CONTENT_LENGTH"] = UPLOAD_SIZE

with app.app_context():
    init_db()
    print("initialized db.", flush=True)
swagger = Swagger(app)
app.register_blueprint(Collector, url_prefix="/api/v1")
app.register_blueprint(Choice, url_prefix="/api/v1")
app.register_blueprint(Game, url_prefix="/api/v1")
app.register_blueprint(Run, url_prefix="/api/v1")
app.register_blueprint(User, url_prefix="/api/v1/")


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
    print("ran socket.io on app with port 8000", flush=True)
