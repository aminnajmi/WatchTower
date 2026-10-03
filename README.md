# WatchTower

WatchTower monitors official Linux operating system releases and reports changes through its dashboard, REST API, and optional notifications.

A FastAPI service that tracks official releases for Ubuntu, AlmaLinux, Fedora, Rocky Linux, Debian, Arch Linux, and CentOS Stream. It stores release history in SQLite, serves a dashboard and REST API, and can send optional Discord or Telegram notifications.

## Production deployment on Ubuntu Server

The Compose deployment runs one Uvicorn process and therefore one in-process APScheduler. The scheduler checks at **09:00 and 23:00 UTC**. SQLite and its WAL files live in the persistent `tracker-data` Docker volume. The container runs as an unprivileged user, has a read-only root filesystem, and exposes `/health` for Docker health checks.

### 1. Install Docker Engine and Compose

Install Docker Engine and the Compose plugin using Docker's official Ubuntu instructions: <https://docs.docker.com/engine/install/ubuntu/>. Confirm both commands work:

```bash
docker --version
docker compose version
```

### 2. Get the application and configure it

```bash
git clone https://github.com/aminnajmi/WatchTower.git
cd WatchTower
cp .env.example .env
chmod 600 .env
```

Edit `.env`. Set `ALLOWED_HOSTS` to the exact hostname or server IP users will enter in their browser (comma-separated for multiple hosts; do not include a scheme or port). The example config includes `37.120.198.236`; replace it if the server address changes. Keep `HOST_BIND=127.0.0.1` when a local reverse proxy terminates HTTPS. For direct access, set `HOST_BIND=0.0.0.0`, then allow the selected `PORT` in the server firewall. Set `PORT` if the host port should differ.

Generate the JWT secret:

```bash
openssl rand -hex 32
```

Copy the output to `JWT_SECRET`. Create the administrator password hash and salt on a trusted machine with the application dependencies installed:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m app.create_admin
```

Enter the chosen administrator username and password when prompted, then copy the displayed hash and salt into `ADMIN_PASSWORD_HASH` and `ADMIN_PASSWORD_SALT`. Do not put the plain password in `.env`. Configure Telegram or Discord credentials only when needed. With Telegram enabled, both its bot token and chat ID are required.

To enable Telegram notifications, set `TELEGRAM_ENABLED=true`, `TELEGRAM_BOT_TOKEN`, and `TELEGRAM_CHAT_ID` in `.env`, then recreate the container with `docker compose up -d`. Use the dashboard's Telegram test action to verify delivery. Keep the bot token private.

The production app refuses to start if the JWT secret, admin credentials, allowed hosts, or enabled Telegram credentials are invalid. Compose defaults `DATABASE_URL` to `sqlite:////app/data/os_tracker.db`; that location is persisted in the named volume. Do not change it to a path outside `/app/data` unless you configure another persistent writable mount.

### 3. Validate and start

```bash
docker compose config --quiet
docker compose build
docker compose up -d
docker compose ps
docker compose logs --tail=100 watchtower
```

Wait for `healthy` in `docker compose ps`, then check `http://SERVER:PORT/health`, `/login`, and `/docs`. Sign in to the dashboard with the configured admin account. API clients can authenticate at `POST /api/v1/auth/token` and then use the returned bearer token.

### Reverse proxy and forwarded headers

For a reverse proxy, leave `HOST_BIND=127.0.0.1`, set `ALLOWED_HOSTS` to the public hostname, and set `FORWARDED_ALLOW_IPS` to the proxy's actual source IP as seen by the container. The default trusts only loopback. Never set it to `*` on a network where untrusted clients can reach the app directly. Configure the proxy to pass the original host and HTTPS scheme, and terminate TLS at the proxy. The app trusts forwarded scheme information only from configured proxy IPs; it ignores forwarded host values for cookie-origin checks.

Example Nginx location:

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Real-IP $remote_addr;
}
```

Restrict the server firewall to ports 22 and 80/443 for a reverse-proxy setup. For direct exposure, allow only the required host port and provide HTTPS at an external gateway; do not send administrator credentials over public plain HTTP.

### Operations

```bash
docker compose stop
docker compose start
docker compose restart
docker compose logs -f watchtower
docker compose down                 # retains tracker-data
docker compose up -d --build        # rebuild and replace the service
```

Update by reviewing the desired Git revision, pulling it, then running `docker compose build` and `docker compose up -d`. The named database volume is retained across container recreation and `docker compose down`; do not use `docker compose down -v` unless intentionally deleting stored release data.

### Database backup and restore

Make a consistent SQLite backup while the app is running using SQLite's online backup API:

```bash
docker compose exec -T watchtower python -c \
  'import sqlite3; src=sqlite3.connect("/app/data/os_tracker.db"); dst=sqlite3.connect("/tmp/os_tracker-backup.db"); src.backup(dst); dst.close(); src.close()'
docker compose cp watchtower:/tmp/os_tracker-backup.db ./os_tracker-backup.db
```

Store the resulting file off the server and protect it as application data. To restore, first put the backup at `./os_tracker-backup.db`, keep a second copy of the current database, then replace it while the service is stopped. This one-off Compose container mounts the same named volume and runs as the app user:

```bash
docker compose stop watchtower
docker compose run --rm --no-deps \
  -v "$PWD/os_tracker-backup.db:/restore/source.db:ro" \
  --entrypoint python watchtower -c \
  'import os, shutil; dst="/app/data/os_tracker.db"; shutil.copyfile("/restore/source.db", dst); os.chmod(dst, 0o600)'
docker compose up -d
```

The one-off command requires the image to be built and leaves the volume in place. Do not copy only the main database file while SQLite is actively writing; create backups with the online backup API above.

### Troubleshooting

- `unhealthy`: inspect `docker compose logs`; check that port 8000 is free and `.env` has valid production values.
- Host validation errors: add the exact request hostname to `ALLOWED_HOSTS`.
- Reverse-proxy HTTPS cookie issues: verify `FORWARDED_ALLOW_IPS` matches the proxy source IP and it sends `X-Forwarded-Proto`.
- Database permission errors: inspect the `tracker-data` volume and verify the image runs as UID/GID 10001. The named volume is initialized with the image's writable `/app/data` directory.
- Failed release checks: inspect provider errors in the dashboard and container logs; confirm outbound HTTPS access and system time synchronization.

### Deployment checklist

- [ ] Docker Engine and Compose installed
- [ ] `.env` configured with a strong JWT secret and admin password hash/salt
- [ ] Telegram configured and test message delivered, if notifications are required
- [ ] Persistent database volume configured
- [ ] Container reports healthy
- [ ] Health endpoint and dashboard work
- [ ] Scheduler status shows running, job ID, UTC schedule, and next run
- [ ] Database persistence checked after container recreation
- [ ] Backup created and restore procedure reviewed
- [ ] Firewall restricted to required ports
- [ ] HTTPS reverse proxy configured for public access

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

For local development set `APP_ENV=development`, use a local `DATABASE_URL` such as `sqlite:///./os_tracker.db`, then start:

```bash
uvicorn app.main:app --reload --no-access-log
```

Visit `http://127.0.0.1:8000/login` or `http://127.0.0.1:8000/docs`. The dashboard refreshes status from the backend every 30 seconds, and **Check now** refreshes it immediately after a manual check.

## Scheduler behavior

FastAPI's lifespan starts and stops the single APScheduler `AsyncIOScheduler`. Its UTC cron schedule is 09:00 and 23:00 daily. The in-memory scheduler does not replay a run missed while the process was down. A delayed run can start up to 15 minutes after its scheduled time; later executions are marked missed and the next cron time remains scheduled. Running multiple app replicas or Uvicorn workers would create duplicate schedulers, so production Compose deliberately uses one worker and one service replica.

## Tests

Run the suite with:

```bash
python -m unittest discover -s tests -v
```

## Release tracking and extensions

The tracker stores the release identifier returned by each provider. Debian intentionally tracks stable major releases rather than point updates. Arch is marked rolling and uses its latest official ISO release identifier. CentOS Stream tracks the latest official ISO compose identifier.

To add an OS, create a provider under `app/providers/`, implement `latest()`, and register it in `app/providers/__init__.py`.

## Authentication

Swagger and the dashboard use JWT authentication. Sign in through `POST /api/v1/auth/token`; browser login stores the JWT in an HTTP-only cookie. Protected API calls accept a bearer token. The legacy `API_KEY` remains available for server-to-server integrations.
