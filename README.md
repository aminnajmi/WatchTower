# OS Release Tracker

A small FastAPI service that tracks new releases for:

- Ubuntu
- AlmaLinux
- Fedora
- Rocky Linux
- Debian
- Arch Linux
- CentOS Stream

It polls official project release sources, stores the last seen version in SQLite, exposes a REST API, and sends optional Discord/Telegram notifications when a tracked version changes.

## 1. Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/login` for the dashboard or `http://127.0.0.1:8000/docs` for Swagger.

## Web dashboard

The FastAPI app serves the Jinja2 dashboard from the same process and database as the REST API. Sign in at `/login` with the configured admin username and password. The page exchanges the existing JWT for a short-lived HTTP-only browser cookie; API clients can continue using bearer tokens.

The dashboard, operating system details, release history, event filters, scheduler status, and read-only notification settings use the existing backend data. **Check now** runs the provider check on demand. The dashboard refreshes status with read-only API requests every 30 seconds.

## Scheduler

The application uses one APScheduler `AsyncIOScheduler` owned by FastAPI's startup and shutdown lifecycle. The `os-release-check` cron job runs at **09:00 UTC** and **23:00 UTC** every day. Its job store is in memory: if the process is down at a scheduled time, that past run is not replayed when the application starts. While the process is running, APScheduler allows a delayed run for up to 60 seconds; after that it records a missed execution and waits for the next cron time.

## Tests

Run the existing and dashboard test suite with:

```bash
python -m unittest discover -s tests -v
```

## 2. Test

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/v1/providers
curl http://127.0.0.1:8000/api/v1/os
curl -X POST http://127.0.0.1:8000/api/v1/check -H 'X-API-Key: change-me'
```

## 3. Docker

```bash
cp .env.example .env
# edit .env
mkdir -p data
docker compose up -d --build
```

## Notification setup

Set either:

```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

or:

```env
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=-100123456789
```

## Adding another OS

Create a provider under `app/providers/`, implement `latest()`, and register it in `app/providers/__init__.py`.

## Release semantics

The tracker stores the exact release identifier returned by each provider. Debian's provider intentionally tracks the stable major release rather than point releases because Debian explicitly distinguishes point updates from a new Debian release. Arch is marked rolling and uses the latest official ISO release identifier. CentOS tracks the latest CentOS Stream ISO compose identifier.

## Production notes

- Use PostgreSQL instead of SQLite when running multiple replicas.
- Put the service behind HTTPS/reverse proxy.
- Change `API_KEY`.
- Keep notification secrets in environment variables.
- Add retries/backoff and structured logging before large-scale deployment.

## Authentication

Swagger/user authentication uses JWT bearer tokens. Log in once at `POST /api/v1/auth/token`, then click **Authorize** in Swagger and paste the returned `access_token`. Protected requests will automatically send `Authorization: Bearer <token>`.

Create the admin password hash with:

```bash
python -m app.create_admin
```

Generate a JWT secret with:

```bash
openssl rand -hex 32
```

The legacy `API_KEY` remains available for server-to-server integrations; normal users do not need to enter it for every request.
