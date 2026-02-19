from flask_socketio import SocketIO

socketio = SocketIO()


def init_socketio(app):
    socketio.init_app(
        app, message_queue=app.config.get("REDIS_URL"), cors_allowed_origins="*"
    )
