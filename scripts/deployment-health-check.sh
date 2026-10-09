#!/bin/sh
# Wait for WatchTower's Compose healthcheck and verify the published /health endpoint.
set -u

SERVICE=watchtower
TIMEOUT_SECONDS=${WATCHTOWER_HEALTH_TIMEOUT_SECONDS:-60}
INTERVAL_SECONDS=${WATCHTOWER_HEALTH_INTERVAL_SECONDS:-2}
COMMAND_TIMEOUT_SECONDS=${WATCHTOWER_COMMAND_TIMEOUT_SECONDS:-4}

case "$TIMEOUT_SECONDS:$INTERVAL_SECONDS:$COMMAND_TIMEOUT_SECONDS" in
  *[!0-9:]*|:*|*::*) echo "Invalid health-check timeout configuration" >&2; exit 2 ;;
esac
if [ "$TIMEOUT_SECONDS" -lt 1 ] || [ "$INTERVAL_SECONDS" -lt 1 ] || [ "$COMMAND_TIMEOUT_SECONDS" -lt 1 ]; then
  echo "Health-check timeouts must be positive integers" >&2
  exit 2
fi

started_at=$(date +%s)
deadline=$((started_at + TIMEOUT_SECONDS))
container_id=
container_status="not found"
docker_health="not run"
http_status="not run"
DIAGNOSING=0
failure_step="Deployment health check"
failure_reason="WatchTower did not become ready within ${TIMEOUT_SECONDS} seconds"

run_docker() {
  command_timeout=$COMMAND_TIMEOUT_SECONDS
  if [ "$DIAGNOSING" -eq 0 ]; then
    command_now=$(date +%s)
    command_remaining=$((deadline - command_now))
    [ "$command_remaining" -gt 0 ] || return 124
    [ "$command_timeout" -gt "$command_remaining" ] && command_timeout=$command_remaining
  fi
  timeout "$command_timeout" docker "$@"
}

diagnose() {
  echo "--- docker compose ps ---"
  run_docker compose ps 2>&1 || true
  if [ -n "$container_id" ]; then
    echo "--- WatchTower container status ---"
    run_docker inspect --format 'status={{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}missing{{end}}' "$container_id" 2>&1 || true
    echo "--- Docker health details ---"
    run_docker inspect --format '{{if .State.Health}}{{json .State.Health}}{{else}}no healthcheck{{end}}' "$container_id" 2>&1 || true
    echo "--- Recent WatchTower logs (credentials redacted) ---"
    run_docker logs --tail 100 "$container_id" 2>&1 | sed -E \
      -e 's#(https?://api\.telegram\.org/bot)[^/[:space:]]+#\1[REDACTED]#g' \
      -e 's/((TOKEN|SECRET|PASSWORD|DATABASE_URL|CHAT_ID)=)[^[:space:]]+/\1[REDACTED]/Ig' || true
  fi
  if [ -n "$http_url" ]; then
    echo "--- HTTP health check ---"
    curl --verbose --max-time "$COMMAND_TIMEOUT_SECONDS" --resolve "${health_host}:${published_port}:127.0.0.1" -H "Host: $health_host" "$http_url" -o /dev/null 2>&1 || true
  fi
}

if [ "${1:-}" = "--diagnose" ]; then
  DIAGNOSING=1
  container_id=$(run_docker compose ps -q "$SERVICE" 2>/dev/null | head -n 1)
  if [ -n "$container_id" ]; then
    container_status=$(run_docker inspect --format '{{.State.Status}}' "$container_id" 2>/dev/null || printf 'unknown')
    docker_health=$(run_docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}missing{{end}}' "$container_id" 2>/dev/null || printf 'unknown')
    health_host=$(run_docker exec "$container_id" python -c "import os; print(os.environ.get('ALLOWED_HOSTS','127.0.0.1').split(',')[0].strip())" 2>/dev/null | head -n 1)
    case "$health_host" in ''|'*') health_host=127.0.0.1 ;; esac
    published_port=$(run_docker compose port "$SERVICE" 8000 2>/dev/null | tail -n 1 | sed 's/.*://')
    case "$published_port" in *[!0-9]*|'') published_port=8000 ;; esac
    http_url="http://${health_host}:${published_port}/health"
    http_status="not run"
  fi
  diagnose
  exit 0
fi

http_url=
health_host=
while :; do
  now=$(date +%s)
  if [ "$now" -ge "$deadline" ]; then
    break
  fi

  container_id=$(run_docker compose ps -q "$SERVICE" 2>/dev/null | head -n 1)
  if [ -n "$container_id" ]; then
    container_status=$(run_docker inspect --format '{{.State.Status}}' "$container_id" 2>/dev/null || printf 'unknown')
    case "$container_status" in
      exited|dead|removing)
        failure_step="Container startup"
        failure_reason="WatchTower container entered terminal state: $container_status"
        break
        ;;
      running)
        docker_health=$(run_docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}missing{{end}}' "$container_id" 2>/dev/null || printf 'unknown')
        case "$docker_health" in
          unhealthy)
            failure_step="Docker health check"
            failure_reason="WatchTower Docker health check reported unhealthy"
            break
            ;;
          healthy)
            health_host=$(run_docker exec "$container_id" python -c "import os; print(os.environ.get('ALLOWED_HOSTS','127.0.0.1').split(',')[0].strip())" 2>/dev/null | head -n 1)
            case "$health_host" in ''|'*') health_host=127.0.0.1 ;; esac
            published_port=$(run_docker compose port "$SERVICE" 8000 2>/dev/null | tail -n 1 | sed 's/.*://')
            case "$published_port" in *[!0-9]*|'') published_port=8000 ;; esac
            http_url="http://${health_host}:${published_port}/health"
            curl_timeout=$COMMAND_TIMEOUT_SECONDS
            now=$(date +%s)
            remaining=$((deadline - now))
            [ "$remaining" -gt 0 ] || break
            [ "$curl_timeout" -gt "$remaining" ] && curl_timeout=$remaining
            if curl --silent --show-error --fail --max-time "$curl_timeout" --resolve "${health_host}:${published_port}:127.0.0.1" -H "Host: $health_host" "$http_url" -o /dev/null 2>/dev/null; then
              http_status=passed
              printf 'WATCHTOWER_RESULT=success\nWATCHTOWER_STEP=none\nWATCHTOWER_ERROR=none\nWATCHTOWER_IMAGE=built\nWATCHTOWER_CONTAINER=running\nWATCHTOWER_DOCKER_HEALTH=healthy\nWATCHTOWER_HTTP=passed\n'
              exit 0
            fi
            http_status=retrying
            failure_step="HTTP health check"
            failure_reason="Published /health endpoint has not returned HTTP 200 yet"
            ;;
          starting|missing|unknown)
            docker_health=${docker_health:-unknown}
            ;;
          *)
            docker_health=unknown
            ;;
        esac
        ;;
      created|restarting|paused|unknown)
        ;;
      *)
        ;;
    esac
  fi

  now=$(date +%s)
  [ "$now" -ge "$deadline" ] && break
  remaining=$((deadline - now))
  delay=$INTERVAL_SECONDS
  [ "$delay" -gt "$remaining" ] && delay=$remaining
  sleep "$delay"
done

DIAGNOSING=1
diagnose
printf 'WATCHTOWER_RESULT=failure\nWATCHTOWER_STEP=%s\nWATCHTOWER_ERROR=%s\nWATCHTOWER_IMAGE=built\nWATCHTOWER_CONTAINER=%s\nWATCHTOWER_DOCKER_HEALTH=%s\nWATCHTOWER_HTTP=%s\n' \
  "$failure_step" "$failure_reason" "$container_status" "$docker_health" "$http_status"
exit 1
