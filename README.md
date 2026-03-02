# GameLens-Collector-Service

GameLens Collector Service is a Flask-based ingestion API and Socket.IO server used to receive game capture data and store it in Postgres. It supports HTTP uploads and realtime ingestion via Socket.IO, and can run behind Traefik with sticky sessions for WebSocket stability.

## What’s in this repo
- **HTTP API** for ingesting captures and metadata
- **Socket.IO** endpoint for realtime capture events
- **Postgres** storage via `psycopg`
- **Docker + Compose** for local and containerized runs

## Requirements
- Python **3.13+** (local)
- Docker + Docker Compose (recommended for local/dev)

> [!IMPORTANT] 
> **Environment Variables:** You must configure the following in your `.env` file: `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB`. 
> 
> For your database connection (`PGSQL_CONN`), the host depends on how you are running the API:
> * **Running via Docker:** `postgresql://<POSTGRES_USER>:<POSTGRES_PASSWORD>@db:5432/<POSTGRES_DB>`
> * **Running locally (Host machine):** `postgresql://<POSTGRES_USER>:<POSTGRES_PASSWORD>@localhost:5432/<POSTGRES_DB>`
## Local development (uv)
```bash
uv sync
uv run gunicorn --worker-class eventlet --workers 1 --bind 0.0.0.0:8000 src.api:app
```

> Tip: use **1 worker** for local Socket.IO testing to avoid session issues without a reverse proxy.

## Docker / Compose
This repo includes a `Dockerfile` and `docker-compose.yaml` with Traefik + Redis.

```bash
docker compose up --build 
```

Migrate the DB using the following command, after the startup of all docker containers:
```bash
docker exec -i postgres_db psql -U your_username -d your_database_name < db/GameLens-Schema.sql
```

## Tests
Run the socket unit tests:

```bash
uv run pytest
```

## Notes
- For multi-worker setups, add Redis + traefik
