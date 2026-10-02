from datetime import datetime, timezone
import logging
from sqlalchemy import select
from .models import SessionLocal, OSRelease, ReleaseHistory, ReleaseEvent
from .providers import PROVIDERS
from .config import settings
from .notifications import notify
from .notifications.telegram import send as send_telegram
from .versioning import ReleaseState, compare_releases, parse_version

logger = logging.getLogger(__name__)
PROVIDER_NAMES = {
    "ubuntu": "Ubuntu", "almalinux": "AlmaLinux", "fedora": "Fedora",
    "rockylinux": "Rocky Linux", "debian": "Debian", "archlinux": "Arch Linux",
    "centos": "CentOS Stream",
}

last_check_started_at = None
last_check_finished_at = None
last_check_result = None


async def check_all():
    global last_check_started_at, last_check_finished_at, last_check_result
    last_check_started_at = datetime.now(timezone.utc)
    results = []
    errors = []
    notification_errors = []
    changed_count = 0
    major_count = 0
    successful_os_ids = []
    db = SessionLocal()

    try:
        for slug, provider in PROVIDERS.items():
            try:
                release = await provider.latest()
                parsed = parse_version(release)
                now = datetime.now(timezone.utc).replace(tzinfo=None)
                current = db.scalar(select(OSRelease).where(OSRelease.slug == slug))
                old_version = current.version if current is not None else None
                old_major_version = current.major_version if current is not None else None
                comparison = compare_releases(
                    ReleaseState(current.version, current.major_version, current.is_rolling) if current else None,
                    ReleaseState(release.version, parsed.major_version, release.is_rolling),
                )
                is_changed = comparison.changed
                is_major_release = comparison.major_release

                if current is None:
                    current = OSRelease(
                        slug=release.slug,
                        name=release.name,
                        version=release.version,
                        major_version=parsed.major_version,
                        release_date=release.release_date,
                        source_url=release.source_url,
                        release_type=parsed.release_type,
                        is_rolling=release.is_rolling,
                        first_seen_at=now,
                        checked_at=now,
                        updated_at=now,
                    )
                    db.add(current)
                    db.flush()
                    history_exists = False
                    # Initial baseline is recorded but never notified.
                else:
                    history_exists = db.scalar(
                        select(ReleaseHistory.id).where(
                            ReleaseHistory.os_id == current.id,
                            ReleaseHistory.version == release.version,
                        )
                    ) is not None
                    current.name = release.name
                    current.version = release.version
                    current.major_version = parsed.major_version
                    current.release_date = release.release_date
                    current.source_url = release.source_url
                    current.release_type = parsed.release_type
                    current.is_rolling = release.is_rolling
                    current.checked_at = now
                    current.updated_at = now

                if not history_exists:
                    db.add(ReleaseHistory(
                        os_id=current.id,
                        version=release.version,
                        major_version=parsed.major_version,
                        release_type=parsed.release_type,
                        release_date=release.release_date,
                        source_url=release.source_url,
                        detected_at=now,
                    ))

                event = None
                if is_major_release:
                    existing_event = db.scalar(select(ReleaseEvent.id).where(
                        ReleaseEvent.os_id == current.id,
                        ReleaseEvent.previous_major_version == old_major_version,
                        ReleaseEvent.new_major_version == parsed.major_version,
                        ReleaseEvent.event_type == "new_major_release",
                    ))
                    if existing_event is None:
                        event = ReleaseEvent(
                            os_id=current.id,
                            previous_version=old_version,
                            new_version=release.version,
                            previous_major_version=old_major_version,
                            new_major_version=parsed.major_version,
                            event_type="new_major_release",
                            detected_at=now,
                        )
                        db.add(event)
                        db.flush()
                        major_count += 1

                if is_changed:
                    changed_count += 1

                results.append({
                    "slug": release.slug,
                    "name": release.name,
                    "version": release.version,
                    "major_version": parsed.major_version,
                    "release_type": parsed.release_type,
                    "changed": is_changed,
                    "major_release": is_major_release,
                    "event_type": comparison.event_type,
                    "last_checked": now.replace(tzinfo=timezone.utc),
                })
                successful_os_ids.append(current.id)
            except Exception as exc:
                errors.append({"slug": slug, "error": str(exc)})
                logger.warning("Provider error: %s", PROVIDER_NAMES.get(slug, slug))

        provider_check_finished_at = datetime.now(timezone.utc)
        checked_at = provider_check_finished_at.replace(tzinfo=None)
        for os_id in successful_os_ids:
            os_row = db.get(OSRelease, os_id)
            if os_row:
                os_row.checked_at = checked_at
        for result in results:
            result["last_checked"] = provider_check_finished_at
        db.commit()

        events = db.scalars(
            select(ReleaseEvent).where(
                ReleaseEvent.event_type == "new_major_release",
                ReleaseEvent.notification_sent.is_(False),
            ).order_by(ReleaseEvent.id)
        ).all()

        for event in events:
            os_row = db.get(OSRelease, event.os_id)
            if not os_row or os_row.is_rolling or event.event_type != "new_major_release":
                continue
            message = (
                "🚨 New Major OS Release\n\n"
                f"OS: {os_row.name}\n"
                f"Previous Version: {event.previous_version or 'unknown'}\n"
                f"New Version: {event.new_version}\n"
                f"Major Version: {event.new_major_version}\n\n"
                "The OS Release Tracker detected a new major release."
            )
            try:
                delivery = await notify(message)
                # Retain compatibility with integrations/tests that implement the
                # older notify() contract and return None on success.
                sent, delivery_error = delivery if isinstance(delivery, tuple) else (True, None)
                if sent:
                    event.notification_sent = True
                    event.notification_sent_at = datetime.now(timezone.utc).replace(tzinfo=None)
                    db.commit()
                    logger.info("Major release notification sent for %s %s", os_row.name, event.new_version)
                else:
                    safe_error = delivery_error or "notification delivery failed"
                    notification_errors.append({"slug": os_row.slug, "error": safe_error})
                    logger.warning("Notification failed for %s %s: %s", os_row.name, event.new_version, safe_error)
            except Exception as exc:
                safe_error = f"notification delivery failed ({type(exc).__name__})"
                notification_errors.append({"slug": os_row.slug, "error": safe_error})
                logger.warning("Notification failed for %s %s: %s", os_row.name, event.new_version, safe_error)

    finally:
        db.close()

    last_check_finished_at = datetime.now(timezone.utc)
    summary = {
        "checked": len(results),
        "failed": len(errors),
        "changed": changed_count,
        "major_releases": major_count,
        "results": results,
        "errors": errors,
        "notification_errors": notification_errors,
        "finished_at": last_check_finished_at,
    }
    last_check_result = summary

    # Send one Telegram completion summary per check. Major release events use
    # the existing notification path above and remain separate messages.
    completion = (
        "✅ Check Completed\n\n"
        f"{summary['checked']}/{len(PROVIDERS)} providers healthy\n\n"
        "The OS Release Tracker completed the provider check."
    )
    if errors:
        completion = (
            "⚠️ Check Completed\n\n"
            f"{summary['checked']}/{len(PROVIDERS)} providers healthy\n\n"
            "Provider errors:\n"
            + "\n".join(
                f"- {PROVIDER_NAMES.get(item['slug'], item['slug'])}: provider unavailable"
                for item in errors
            )
        )
    if settings.telegram_enabled:
        try:
            await send_telegram(completion)
        except Exception as exc:
            # Notification transport failures must not turn a completed provider
            # check into a failed check. Exception details can contain credentials.
            logger.warning("Telegram check summary failed (%s)", type(exc).__name__)
    return summary
