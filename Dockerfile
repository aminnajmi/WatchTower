FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt \
    && python -m playwright install --with-deps chromium \
    && chmod -R 755 /ms-playwright \
    && rm -rf /root/.cache/pip

COPY app ./app
COPY static ./static
COPY templates ./templates

# Fail the image build if the UI files needed by the browser were omitted
# from the build context or copied to an unexpected path.
RUN test -s /app/static/js/app.js \
    && test -s /app/static/css/app.css \
    && test -s /app/static/watchtower.svg \
    && test -s /app/templates/login.html \
    && test -s /app/templates/base.html

# The default UID/GID is stable so bind-mounted SQLite storage can be owned
# by this account on the host. Override at build time when required.
ARG APP_UID=10001
ARG APP_GID=10001

RUN groupadd --gid "${APP_GID}" watchtower \
    && useradd --uid "${APP_UID}" \
        --gid watchtower \
        --create-home \
        --home-dir /home/watchtower \
        --shell /usr/sbin/nologin \
        watchtower \
    && mkdir -p /app/data \
    && chown -R watchtower:watchtower /app /home/watchtower

USER watchtower:watchtower

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,urllib.request; host=os.environ.get('ALLOWED_HOSTS','127.0.0.1').split(',')[0].strip(); paths=('/health','/static/css/app.css','/static/js/app.js','/static/watchtower.svg'); [urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8000'+path,headers={'Host':host}),timeout=3).read() for path in paths]" || exit 1

# Keep one process: each Uvicorn worker would create its own APScheduler.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 --no-access-log --proxy-headers --forwarded-allow-ips \"${FORWARDED_ALLOW_IPS:-127.0.0.1}\""]