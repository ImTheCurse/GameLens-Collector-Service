from flask_socketio import SocketIO

socketio = SocketIO()


def init_socketio(app):
    socketio.init_app(
        app,
        cors_allowed_origins="*",
        logger=True,
        engineio_logger=True,
    )
