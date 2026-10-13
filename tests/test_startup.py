import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import main, models, service
from app.auth import create_access_token
from app.config import settings
from app import scheduler as scheduler_module


class ApplicationStartupTests(unittest.TestCase):
    def test_real_startup_scheduler_health_docs_and_status(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "startup.db"
            engine = create_engine(f"sqlite:///{database_path}", connect_args={"check_same_thread": False})
            sessions = sessionmaker(bind=engine, autoflush=False, autocommit=False)
            with patch.object(models, "engine", engine), \
                 patch.object(models.settings, "database_url", f"sqlite:///{database_path}"), \
                 patch.object(main, "SessionLocal", sessions), \
                 patch.object(service, "SessionLocal", sessions), \
                 TestClient(main.app) as client:
                self.assertEqual(client.get("/health").json(), {"status": "ok"})
                self.assertEqual(client.get("/docs").status_code, 200)
                token = create_access_token(settings.admin_username)
                status_response = client.get("/api/v1/status", headers={"Authorization": f"Bearer {token}"})
                self.assertEqual(status_response.status_code, 200)
                payload = status_response.json()
                self.assertTrue(payload["scheduler"]["running"])
                self.assertEqual(payload["tracked_os"], 7)
                job = scheduler_module.get_scheduler().get_job("os-release-check")
                self.assertIsNotNone(job)
                self.assertIs(job.func, scheduler_module.scheduled_check)
                self.assertEqual(str(job.trigger), "cron[hour='9,23', minute='0']")
                self.assertEqual(str(job.trigger.timezone), "UTC")
                self.assertGreater(job.next_run_time, datetime.now(timezone.utc))
                self.assertEqual(payload["scheduler"]["job_id"], "os-release-check")
                self.assertEqual(payload["scheduler"]["schedule"], "09:00,23:00 UTC")
                self.assertEqual(payload["scheduler"]["timezone"], "UTC")
                self.assertEqual(payload["scheduler"]["trigger"], "cron")
                self.assertTrue(payload["scheduler"]["job_exists"])
                self.assertEqual(payload["scheduler"]["job_state"], "scheduled")
                self.assertEqual(
                    datetime.fromisoformat(payload["scheduler"]["next_check"]),
                    job.next_run_time,
                )

                next_run = job.next_run_time
                main.start_scheduler()
                self.assertEqual(len(scheduler_module.get_scheduler().get_jobs()), 1)
                self.assertEqual(scheduler_module.get_scheduler().get_job("os-release-check").next_run_time, next_run)

                scheduler_module.get_scheduler().pause_job("os-release-check")
                paused_status = client.get("/api/v1/status", headers={"Authorization": f"Bearer {token}"}).json()
                self.assertEqual(paused_status["scheduler"]["job_state"], "paused")
                self.assertFalse(paused_status["scheduler"]["running"])
                self.assertTrue(paused_status["scheduler"]["apscheduler_running"])
                self.assertIsNone(paused_status["scheduler"]["next_check"])
                main.start_scheduler()
                self.assertIsNotNone(scheduler_module.get_scheduler().get_job("os-release-check").next_run_time)

                scheduler_module.get_scheduler().remove_job("os-release-check")
                missing_status = client.get("/api/v1/status", headers={"Authorization": f"Bearer {token}"}).json()
                self.assertEqual(missing_status["scheduler"]["job_state"], "missing")
                self.assertFalse(missing_status["scheduler"]["job_exists"])
                self.assertFalse(missing_status["scheduler"]["running"])
                main.start_scheduler()
                self.assertEqual(len(scheduler_module.get_scheduler().get_jobs()), 1)
            self.assertIsNone(scheduler_module.get_scheduler())
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
