from dotenv import load_dotenv

load_dotenv()
from flasgger import Swagger
from flask import Flask, jsonify

from src.collector import Collector
from src.errors import FileUploadError, MissingCollectorParam
from src.util import UPLOAD_DIR, UPLOAD_SIZE

app = Flask(__name__)
swagger = Swagger(app)
app.register_blueprint(Collector, url_prefix="/api/v1")


app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
app.config["MAX_CONTENT_LENGTH"] = UPLOAD_SIZE


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
