import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HEALTH_CHECK = ROOT / "scripts" / "deployment-health-check.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "deploy.yml"


class DeploymentHealthCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.bin = Path(self.temp.name) / "bin"
        self.bin.mkdir()
        self.write_executable(
            "timeout",
            "#!/bin/sh\nshift\nexec \"$@\"\n",
        )
        self.write_executable(
            "docker",
            """#!/bin/sh
args="$*"
case "$args" in
  "compose ps -q watchtower") printf '%s\\n' "${MOCK_CONTAINER_ID-container-id}" ;;
  "compose port watchtower 8000") echo 127.0.0.1:18000 ;;
  "inspect --format {{.State.Status}} "*) echo "${MOCK_CONTAINER_STATUS:-running}" ;;
  "inspect --format {{if .State.Health}}{{.State.Health.Status}}{{else}}missing{{end}} "*)
    n=$(cat "$MOCK_HEALTH_COUNT" 2>/dev/null || echo 0); n=$((n + 1)); echo "$n" > "$MOCK_HEALTH_COUNT"
    value=$(printf '%s\\n' "${MOCK_DOCKER_HEALTH_SEQUENCE:-healthy}" | cut -d, -f"$n")
    [ -n "$value" ] || value=$(printf '%s\\n' "${MOCK_DOCKER_HEALTH_SEQUENCE:-healthy}" | awk -F, '{print $NF}')
    echo "$value" ;;
  "inspect --format "*) echo '{"Status":"healthy","Log":[]}' ;;
  "exec "*) echo localhost ;;
  "logs "*) printf '%s\\n' "${MOCK_LOG:-WatchTower diagnostic log}" ;;
  "compose ps") echo 'watchtower running' ;;
  *) echo "unexpected docker call: $args" >&2; exit 2 ;;
esac
""",
        )
        self.write_executable(
            "curl",
            """#!/bin/sh
n=$(cat "$MOCK_CURL_COUNT" 2>/dev/null || echo 0); n=$((n + 1)); echo "$n" > "$MOCK_CURL_COUNT"
case "$*" in *--verbose*) echo "$*" ;; esac
if [ "$n" -le "${MOCK_CURL_FAILURES:-0}" ]; then exit 22; fi
exit 0
""",
        )
        self.env = os.environ.copy()
        self.env.update(
            {
                "PATH": f"{self.bin}:{os.environ['PATH']}",
                "MOCK_HEALTH_COUNT": str(Path(self.temp.name) / "health-count"),
                "MOCK_CURL_COUNT": str(Path(self.temp.name) / "curl-count"),
                "WATCHTOWER_HEALTH_INTERVAL_SECONDS": "1",
                "WATCHTOWER_COMMAND_TIMEOUT_SECONDS": "2",
            }
        )

    def write_executable(self, name, content):
        path = self.bin / name
        path.write_text(content, encoding="utf-8")
        path.chmod(0o755)

    def run_check(self, **env):
        configured = self.env.copy()
        configured.update(env)
        return subprocess.run(
            ["sh", str(HEALTH_CHECK)],
            cwd=ROOT,
            env=configured,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=15,
            check=False,
        )

    def test_quick_start_reports_success_when_both_checks_are_ready(self):
        result = self.run_check(WATCHTOWER_HEALTH_TIMEOUT_SECONDS="3")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("WATCHTOWER_RESULT=success", result.stdout)
        self.assertIn("WATCHTOWER_DOCKER_HEALTH=healthy", result.stdout)
        self.assertIn("WATCHTOWER_HTTP=passed", result.stdout)

    def test_slow_container_startup_is_retried(self):
        result = self.run_check(
            WATCHTOWER_HEALTH_TIMEOUT_SECONDS="8",
            MOCK_DOCKER_HEALTH_SEQUENCE="starting,healthy",
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("WATCHTOWER_RESULT=success", result.stdout)

    def test_transient_http_failure_is_retried_until_200(self):
        result = self.run_check(
            WATCHTOWER_HEALTH_TIMEOUT_SECONDS="8", MOCK_CURL_FAILURES="1"
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("WATCHTOWER_HTTP=passed", result.stdout)
        self.assertEqual(Path(self.env["MOCK_CURL_COUNT"]).read_text().strip(), "2")

    def test_http_endpoint_that_never_returns_200_fails(self):
        result = self.run_check(
            WATCHTOWER_HEALTH_TIMEOUT_SECONDS="8", MOCK_CURL_FAILURES="10"
        )
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("WATCHTOWER_STEP=HTTP health check", result.stdout)
        self.assertIn("WATCHTOWER_HTTP=retrying", result.stdout)

    def test_missing_container_is_reported_after_wait(self):
        result = self.run_check(
            WATCHTOWER_HEALTH_TIMEOUT_SECONDS="2", MOCK_CONTAINER_ID=""
        )
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("WATCHTOWER_CONTAINER=not found", result.stdout)

    def test_never_ready_fails_after_bounded_wait_and_emits_diagnostics(self):
        result = self.run_check(
            WATCHTOWER_HEALTH_TIMEOUT_SECONDS="2",
            MOCK_DOCKER_HEALTH_SEQUENCE="starting",
        )
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("WATCHTOWER_RESULT=failure", result.stdout)
        self.assertIn("docker compose ps", result.stdout)
        self.assertIn("Docker health details", result.stdout)
        self.assertIn("Recent WatchTower logs", result.stdout)

    def test_unhealthy_container_fails_immediately(self):
        result = self.run_check(
            WATCHTOWER_HEALTH_TIMEOUT_SECONDS="10", MOCK_DOCKER_HEALTH_SEQUENCE="unhealthy"
        )
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("WATCHTOWER_STEP=Docker health check", result.stdout)
        self.assertIn("WATCHTOWER_DOCKER_HEALTH=unhealthy", result.stdout)

    def test_diagnostic_logs_redact_tokens_and_connection_strings(self):
        secret = "private-bot-token"
        result = self.run_check(
            WATCHTOWER_HEALTH_TIMEOUT_SECONDS="10",
            MOCK_DOCKER_HEALTH_SEQUENCE="unhealthy",
            MOCK_LOG=(
                f"request https://api.telegram.org/bot{secret}/sendMessage "
                "TELEGRAM_BOT_TOKEN=another-secret DATABASE_URL=postgres://user:pass@db/app"
            ),
        )
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertNotIn(secret, result.stdout)
        self.assertNotIn("another-secret", result.stdout)
        self.assertNotIn("postgres://user:pass", result.stdout)

    def test_deploy_failure_diagnostics_include_published_http_probe(self):
        configured = self.env.copy()
        result = subprocess.run(
            ["sh", str(HEALTH_CHECK), "--diagnose"],
            cwd=ROOT,
            env=configured,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=15,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("HTTP health check", result.stdout)
        self.assertIn("localhost:18000/health", result.stdout)

    def test_exited_container_fails_immediately(self):
        result = self.run_check(
            WATCHTOWER_HEALTH_TIMEOUT_SECONDS="10", MOCK_CONTAINER_STATUS="exited"
        )
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("WATCHTOWER_STEP=Container startup", result.stdout)
        self.assertIn("WATCHTOWER_CONTAINER=exited", result.stdout)


class DeploymentWorkflowSafetyTests(unittest.TestCase):
    def test_failure_notification_is_unconditional_and_does_not_mask_job_failure(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        completion = workflow.split("- name: Notify deployment completed", 1)[1]
        self.assertIn("if: ${{ always() }}", completion.split("run: |", 1)[0])
        self.assertIn("continue-on-error: true", completion.split("run: |", 1)[0])
        self.assertIn("steps.result.outputs.success != 'true'", workflow)
        self.assertIn("HTTP /health", workflow)
        self.assertIn("Docker health", workflow)

    def test_workflow_never_prints_telegram_token_or_ssh_key(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertNotRegex(workflow, r"print\([^\n]*(TELEGRAM_BOT_TOKEN|SERVER_SSH_KEY)")
        self.assertIn("except Exception:\n              print(", workflow)


if __name__ == "__main__":
    unittest.main()
