import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, EVENT_JOB_MISSED
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.base import STATE_PAUSED
from apscheduler.triggers.cron import CronTrigger

from .service import check_all

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    _scheduler_log_handler = logging.StreamHandler()
    _scheduler_log_handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    logger.addHandler(_scheduler_log_handler)
logger.propagate = False

JOB_ID = "os-release-check"
SCHEDULE_LABEL = "09:00,23:00 UTC"
UTC = timezone.utc

# The scheduler is deliberately created only inside start_scheduler().  This
# guarantees that AsyncIOScheduler is bound to FastAPI/Uvicorn's live event
# loop, rather than to an event-loop object that happened to exist at import
# time.
scheduler: Optional[AsyncIOScheduler] = None

last_scheduled_run_started_at = None
last_scheduled_run_finished_at = None
last_scheduled_run_error = None
last_scheduled_run_status = None


def get_scheduler() -> Optional[AsyncIOScheduler]:
    return scheduler


async def scheduled_check():
    """Run the shared check service without taking down APScheduler."""
    global last_scheduled_run_started_at, last_scheduled_run_finished_at, last_scheduled_run_error

    last_scheduled_run_started_at = datetime.now(UTC)
    last_scheduled_run_error = None
    logger.info("SCHEDULER JOB EXECUTING")
    logger.info("Job ID: %s", JOB_ID)
    logger.info("Execution time: %s", last_scheduled_run_started_at.isoformat())

    try:
        result = await check_all()
    except Exception as exc:
        last_scheduled_run_error = type(exc).__name__
        last_scheduled_run_finished_at = datetime.now(UTC)
        logger.exception("SCHEDULER JOB FAILED")
        # Re-raise so APScheduler emits EVENT_JOB_ERROR. The cron job itself
        # remains registered and will run again at the next scheduled time.
        raise

    last_scheduled_run_finished_at = datetime.now(UTC)
    logger.info("SCHEDULER JOB COMPLETED")
    logger.info("Checked: %s", result.get("checked", 0))
    logger.info("Failed: %s", result.get("failed", 0))
    logger.info("Changed: %s", result.get("changed", 0))
    logger.info("Major releases: %s", result.get("major_releases", 0))
    return result


def _record_job_event(event):
    """Record real APScheduler lifecycle events for the tracked job."""
    global last_scheduled_run_finished_at, last_scheduled_run_error, last_scheduled_run_status

    if event.job_id != JOB_ID:
        return

    observed_at = datetime.now(UTC)
    if event.code == EVENT_JOB_EXECUTED:
        last_scheduled_run_finished_at = observed_at
        last_scheduled_run_status = "success"
        last_scheduled_run_error = None
        logger.info("SCHEDULER JOB EXECUTED")
    elif event.code == EVENT_JOB_ERROR:
        last_scheduled_run_finished_at = observed_at
        last_scheduled_run_status = "error"
        last_scheduled_run_error = type(event.exception).__name__ if event.exception else "UnknownError"
        logger.error("SCHEDULER JOB ERROR: %s", last_scheduled_run_error)
    elif event.code == EVENT_JOB_MISSED:
        last_scheduled_run_finished_at = observed_at
        last_scheduled_run_status = "missed"
        last_scheduled_run_error = "misfire"
        logger.warning("SCHEDULER JOB MISSED")


def _add_check_job(active_scheduler: AsyncIOScheduler):
    return active_scheduler.add_job(
        scheduled_check,
        CronTrigger(hour="9,23", minute=0, timezone=UTC),
        id=JOB_ID,
        replace_existing=True,
        coalesce=True,
        # Allow a temporary event-loop/process delay without losing a run.
        misfire_grace_time=900,
        max_instances=1,
    )


def start_scheduler():
    """Create and start one scheduler on FastAPI's currently running loop."""
    global scheduler

    loop = asyncio.get_running_loop()

    if scheduler is not None and scheduler.running:
        job = scheduler.get_job(JOB_ID)
        if job is None:
            job = _add_check_job(scheduler)
            logger.info("OS release check job registered")
        elif scheduler.state == STATE_PAUSED or job.next_run_time is None:
            scheduler.resume_job(JOB_ID)
            job = scheduler.get_job(JOB_ID)
            logger.info("OS release check job resumed")

        logger.info("Scheduler already running")
        logger.info("Schedule: %s", SCHEDULE_LABEL)
        logger.info("Timezone: UTC")
        logger.info("Job ID: %s", JOB_ID)
        logger.info("Next run: %s", job.next_run_time if job else None)
        return job

    # A previous TestClient/app lifecycle may have shut down the old instance.
    # Always create a fresh scheduler for a fresh application lifecycle.
    scheduler = AsyncIOScheduler(event_loop=loop, timezone=UTC)
    scheduler.add_listener(
        _record_job_event,
        EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED,
    )

    job = _add_check_job(scheduler)
    scheduler.start()

    logger.info("Scheduler started")
    logger.info("OS release check job registered")
    logger.info("Schedule: %s", SCHEDULE_LABEL)
    logger.info("Timezone: UTC")
    logger.info("Job ID: %s", JOB_ID)
    logger.info("Next run: %s", job.next_run_time)
    return job


def stop_scheduler():
    """Stop and discard the scheduler for the current application lifecycle."""
    global scheduler

    if scheduler is not None and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")

    scheduler = None
