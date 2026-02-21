# GameLens-Collector-Service

GameLens Collector Service is a Flask-based ingestion API and Socket.IO server used to receive game capture data and store it in Postgres. It supports HTTP uploads and realtime ingestion via Socket.IO, and can run behind Traefik with sticky sessions for WebSocket stability.

## What’s in this repo
- **HTTP API** for ingesting captures and metadata
- **Socket.IO** endpoint for realtime capture events
- **Postgres** storage via `psycopg`
- **Redis** for Socket.IO multi-worker message queue
- **Docker + Compose** for local and containerized runs

## Requirements
- Python **3.13+** (local)
- Docker + Docker Compose (recommended for local/dev)

## Local development (uv)
```bash
uv sync
uv run gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker --workers 1 --bind 0.0.0.0:8000 src.api:app
```

> Tip: use **1 worker** for local Socket.IO testing to avoid session issues without a reverse proxy.

## Docker / Compose
This repo includes a `Dockerfile` and `docker-compose.yaml` with Traefik + Redis.

```bash
docker compose up --build --scale collector=3
```
> Note: you can change the number of collector services(here its 3) to allow more container to handle traffic.
- Direct container port: `http://localhost:8000`
- Traefik dashboard: `http://localhost:8080`

for both cases, add an environment variable called `PGSQL_CONN` with the connection string in order to connect to the DB.
## Tests
Run the socket unit tests:

```bash
uv run pytest
```

## Notes
- Socket.IO is set up for gevent + gevent-websocket.
- For multi-worker setups, keep Redis + traefik enabled
