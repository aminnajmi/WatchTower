import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app import main, scheduler as scheduler_module, service
from app.auth import create_access_token
from app.config import settings
from app.models import Base, OSRelease
from app.providers.base import Release


class FakeProvider:
    def __init__(self, release=None, error=None):
        self.release = release
        self.error = error
        self.calls = 0

    async def latest(self):
        self.calls += 1
        if self.error:
            raise RuntimeError(self.error)
        return self.release


class SchedulerExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.engine = create_engine(
            f"sqlite:///{Path(self.temp_dir.name) / 'scheduler.db'}",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        self.old_checked_at = datetime(2020, 1, 1)
        self.releases = {
            "ubuntu": Release("ubuntu", "Ubuntu", "26.04.1", None, "https://example.invalid"),
            "almalinux": Release("almalinux", "AlmaLinux", "10.2", None, "https://example.invalid"),
            "fedora": Release("fedora", "Fedora", "44", None, "https://example.invalid"),
            "rockylinux": Release("rockylinux", "Rocky Linux", "10.2", None, "https://example.invalid"),
            "debian": Release("debian", "Debian", "13", None, "https://example.invalid"),
            "archlinux": Release("archlinux", "Arch Linux", "2026.10.01", None, "https://example.invalid", "rolling", True),
            "centos": Release("centos", "CentOS Stream", "10-20260930.0", None, "https://example.invalid"),
        }
        with self.sessions() as db:
            for release in self.releases.values():
                major = "rolling" if release.is_rolling else release.version.split(".", 1)[0].split("-", 1)[0]
                db.add(OSRelease(
                    slug=release.slug,
                    name=release.name,
                    version=release.version,
                    major_version=major,
                    source_url=release.source_url,
                    release_type="rolling" if release.is_rolling else "major",
                    is_rolling=release.is_rolling,
                    first_seen_at=self.old_checked_at,
                    checked_at=self.old_checked_at,
                    updated_at=self.old_checked_at,
                ))
            db.commit()

        service.last_check_started_at = None
        service.last_check_finished_at = None
        service.last_check_result = None
        scheduler_module.last_scheduled_run_started_at = None
        scheduler_module.last_scheduled_run_finished_at = None
        scheduler_module.last_scheduled_run_error = None
        scheduler_module.last_scheduled_run_status = None

    def tearDown(self):
        active_scheduler = scheduler_module.get_scheduler()
        if active_scheduler is not None and active_scheduler.running:
            scheduler_module.stop_scheduler()
        self.engine.dispose()
        self.temp_dir.cleanup()

    def _wait_until(self, predicate, timeout=3):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(0.01)
        self.fail("Timed out waiting for scheduled job execution")

    def _run_with_scheduler(self, providers, check_all_override=None):
        check_mock = patch.object(scheduler_module, "check_all", check_all_override) if check_all_override else None
        with patch.object(main, "init_db"), \
             patch.object(main, "SessionLocal", self.sessions), \
             patch.object(service, "SessionLocal", self.sessions), \
             patch.object(service, "PROVIDERS", providers), \
             patch.object(service, "notify", new=AsyncMock(return_value=(True, None))), \
             patch.object(service, "send_telegram", new=AsyncMock()), \
             TestClient(main.app) as client:
            if check_mock:
                check_mock.start()
            try:
                job = scheduler_module.get_scheduler().get_job(scheduler_module.JOB_ID)
                self.assertIsNotNone(job)
                self.assertIs(job.func, scheduler_module.scheduled_check)
                self.assertEqual(str(job.trigger), "cron[hour='9,23', minute='0']")
                self.assertEqual(str(job.trigger.timezone), "UTC")
                self.assertIsNotNone(job.next_run_time)
                scheduler_module.get_scheduler().modify_job(
                    scheduler_module.JOB_ID,
                    next_run_time=datetime.now(timezone.utc) + timedelta(milliseconds=50),
                )
                token = create_access_token(settings.admin_username)
                headers = {"Authorization": f"Bearer {token}"}
                yield client, headers, job
            finally:
                if check_mock:
                    check_mock.stop()

    def test_scheduled_job_runs_shared_service_and_updates_state(self):
        providers = {slug: FakeProvider(release) for slug, release in self.releases.items()}
        for client, headers, job in self._run_with_scheduler(providers):
            prior_next_run = job.next_run_time
            with self.assertLogs("app.scheduler", level="INFO") as captured:
                self._wait_until(lambda: scheduler_module.last_scheduled_run_finished_at is not None)
            log_output = "\n".join(captured.output)
            self.assertIn("SCHEDULER JOB EXECUTING", log_output)
            self.assertIn("SCHEDULER JOB COMPLETED", log_output)
            self.assertIn("Checked: 7", log_output)

            result = service.last_check_result
            self.assertEqual((result["checked"], result["failed"]), (7, 0))
            self.assertEqual(scheduler_module.last_scheduled_run_error, None)
            self.assertEqual(scheduler_module.last_scheduled_run_status, "success")
            self.assertTrue(scheduler_module.get_scheduler().running)
            self.assertIsNotNone(scheduler_module.get_scheduler().get_job(scheduler_module.JOB_ID))
            self.assertIsNotNone(scheduler_module.get_scheduler().get_job(scheduler_module.JOB_ID).next_run_time)
            self.assertGreaterEqual(sum(provider.calls for provider in providers.values()), 7)

            token = create_access_token(settings.admin_username)
            status_response = client.get("/api/v1/status", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(status_response.status_code, 200)
            scheduler_data = status_response.json()["scheduler"]
            self.assertEqual(scheduler_data["job_state"], "scheduled")
            self.assertEqual(scheduler_data["job_id"], scheduler_module.JOB_ID)
            self.assertEqual(scheduler_data["trigger"], "cron")
            self.assertEqual(scheduler_data["last_execution_status"], "success")
            self.assertEqual(
                datetime.fromisoformat(scheduler_data["last_check"]),
                result["finished_at"],
            )
            current_job = scheduler_module.get_scheduler().get_job(scheduler_module.JOB_ID)
            self.assertNotEqual(current_job.next_run_time, prior_next_run)
            self.assertEqual(
                datetime.fromisoformat(scheduler_data["next_check"]),
                current_job.next_run_time,
            )
            self.assertEqual(scheduler_data["next_run"], scheduler_data["next_check"])
            os_api_rows = client.get("/api/v1/os", headers={"Authorization": f"Bearer {token}"}).json()
            self.assertEqual(len(os_api_rows), 7)
            self.assertTrue(all(row["last_checked"] for row in os_api_rows))

            with self.sessions() as db:
                checked_rows = db.scalars(select(OSRelease)).all()
            self.assertEqual(len(checked_rows), 7)
            self.assertTrue(all(row.checked_at > self.old_checked_at for row in checked_rows))
            self.assertEqual(len({row.checked_at for row in checked_rows}), 1)

    def test_provider_failure_does_not_stop_scheduler(self):
        providers = {slug: FakeProvider(release) for slug, release in self.releases.items()}
        providers["ubuntu"] = FakeProvider(error="mock provider failure")
        for _client, _headers, _job in self._run_with_scheduler(providers):
            self._wait_until(lambda: scheduler_module.last_scheduled_run_finished_at is not None)
            self.assertEqual(service.last_check_result["failed"], 1)
            self.assertTrue(scheduler_module.get_scheduler().running)
            self.assertIsNotNone(scheduler_module.get_scheduler().get_job(scheduler_module.JOB_ID))
            with self.sessions() as db:
                ubuntu = db.scalar(select(OSRelease).where(OSRelease.slug == "ubuntu"))
                fedora = db.scalar(select(OSRelease).where(OSRelease.slug == "fedora"))
            self.assertEqual(ubuntu.checked_at, self.old_checked_at)
            self.assertGreater(fedora.checked_at, self.old_checked_at)

    def test_unexpected_job_exception_is_logged_and_scheduler_keeps_running(self):
        failing_check = AsyncMock(side_effect=RuntimeError("unexpected test failure"))
        providers = {slug: FakeProvider(release) for slug, release in self.releases.items()}
        for _client, _headers, _job in self._run_with_scheduler(providers, failing_check):
            with self.assertLogs("app.scheduler", level="ERROR") as captured:
                self._wait_until(lambda: scheduler_module.last_scheduled_run_status == "error")
            self.assertEqual(scheduler_module.last_scheduled_run_error, "RuntimeError")
            self.assertIn("SCHEDULER JOB FAILED", "\n".join(captured.output))
            self.assertGreaterEqual(failing_check.await_count, 1)
            self.assertEqual(scheduler_module.last_scheduled_run_status, "error")
            self.assertTrue(scheduler_module.get_scheduler().running)
            self.assertIsNotNone(scheduler_module.get_scheduler().get_job(scheduler_module.JOB_ID))

    def test_cron_next_runs_are_0900_and_2300_utc(self):
        from apscheduler.triggers.cron import CronTrigger
        trigger = CronTrigger(hour="9,23", minute=0, timezone=timezone.utc)
        morning = trigger.get_next_fire_time(None, datetime(2026, 10, 2, 8, 59, tzinfo=timezone.utc))
        evening = trigger.get_next_fire_time(None, datetime(2026, 10, 2, 10, 0, tzinfo=timezone.utc))
        next_day = trigger.get_next_fire_time(None, datetime(2026, 10, 2, 23, 1, tzinfo=timezone.utc))
        self.assertEqual((morning.hour, morning.minute), (9, 0))
        self.assertEqual((evening.hour, evening.minute), (23, 0))
        self.assertEqual((next_day.day, next_day.hour, next_day.minute), (3, 9, 0))

    def test_missed_execution_is_observable(self):
        event = SimpleNamespace(code=scheduler_module.EVENT_JOB_MISSED, job_id=scheduler_module.JOB_ID)
        with self.assertLogs("app.scheduler", level="WARNING") as captured:
            scheduler_module._record_job_event(event)
        self.assertEqual(scheduler_module.last_scheduled_run_status, "missed")
        self.assertEqual(scheduler_module.last_scheduled_run_error, "misfire")
        self.assertIn("SCHEDULER JOB MISSED", "\n".join(captured.output))


if __name__ == "__main__":
    unittest.main()
