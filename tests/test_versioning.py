import unittest
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.providers.base import Release
from app.models import Base, OSRelease, ReleaseEvent
from app.versioning import ReleaseState, compare_releases, parse_version


class CompareReleasesTests(unittest.TestCase):
    def test_requested_release_comparisons(self):
        cases = [
            ("Ubuntu same release", ReleaseState("26.04.1", "26"), ReleaseState("26.04.1", "26"), (False, False, None)),
            ("Ubuntu point release", ReleaseState("26.04.1", "26"), ReleaseState("26.04.2", "26"), (True, False, "new_minor_release")),
            ("Ubuntu major release", ReleaseState("26.04.1", "26"), ReleaseState("28.04", "28"), (True, True, "new_major_release")),
            ("AlmaLinux minor release", ReleaseState("10.2", "10"), ReleaseState("10.3", "10"), (True, False, "new_minor_release")),
            ("AlmaLinux major release", ReleaseState("10.2", "10"), ReleaseState("11", "11"), (True, True, "new_major_release")),
            ("Rocky Linux major release", ReleaseState("10.2", "10"), ReleaseState("11", "11"), (True, True, "new_major_release")),
            ("Debian major release", ReleaseState("13", "13"), ReleaseState("14", "14"), (True, True, "new_major_release")),
            ("Fedora major release", ReleaseState("44", "44"), ReleaseState("45", "45"), (True, True, "new_major_release")),
            ("CentOS Stream major release", ReleaseState("10-20260930.0", "10"), ReleaseState("11-2027xxxx.x", "11"), (True, True, "new_major_release")),
            ("Arch rolling release", ReleaseState("2026.09.01", "rolling", True), ReleaseState("2026.10.01", "rolling", True), (True, False, "new_rolling_release")),
            ("First run baseline", None, ReleaseState("26.04.1", "26"), (False, False, None)),
        ]
        for label, previous, current, expected in cases:
            with self.subTest(label=label):
                result = compare_releases(previous, current)
                self.assertEqual((result.changed, result.major_release, result.event_type), expected)


class ParseVersionTests(unittest.TestCase):
    def test_current_release_classification(self):
        cases = [
            ("ubuntu", "26.04", "26", "major", False),
            ("ubuntu", "26.04.1", "26", "minor", False),
            ("ubuntu", "28.04", "28", "major", False),
            ("almalinux", "10.2", "10", "minor", False),
            ("almalinux", "11", "11", "major", False),
            ("rockylinux", "10.2", "10", "minor", False),
            ("rockylinux", "11", "11", "major", False),
            ("debian", "13", "13", "major", False),
            ("fedora", "44", "44", "major", False),
            ("centos", "10-20260930.0", "10", "major", False),
            ("archlinux", "2026.10.01", "rolling", "rolling", True),
        ]
        for slug, version, major, release_type, rolling in cases:
            with self.subTest(slug=slug, version=version):
                release = Release(slug, slug, version, None, "https://example.invalid", is_rolling=rolling)
                parsed = parse_version(release)
                self.assertEqual((parsed.major_version, parsed.release_type), (major, release_type))


class CheckServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_baseline_and_duplicate_major_events(self):
        from app import service

        with tempfile.TemporaryDirectory() as directory:
            engine = create_engine(f"sqlite:///{Path(directory) / 'test.db'}")
            Base.metadata.create_all(engine)
            test_sessions = sessionmaker(bind=engine, autoflush=False, autocommit=False)
            versions = ["26.04.1", "28.04", "26.04.1", "28.04"]

            class FakeProvider:
                async def latest(self):
                    version = versions.pop(0)
                    return Release("ubuntu", "Ubuntu", version, None, "https://example.invalid")

            with patch.object(service, "SessionLocal", test_sessions), \
                 patch.object(service, "PROVIDERS", {"ubuntu": FakeProvider()}), \
                 patch.object(service, "notify", new=lambda message: _done()):
                baseline = await service.check_all()
                self.assertEqual(baseline["results"][0]["event_type"], None)
                self.assertFalse(baseline["results"][0]["changed"])

                await service.check_all()
                await service.check_all()
                await service.check_all()

            with test_sessions() as db:
                events = db.scalars(select(ReleaseEvent)).all()
                self.assertEqual(len(events), 2)
                self.assertEqual(sum(
                    event.previous_major_version == "26" and event.new_major_version == "28"
                    for event in events
                ), 1)
            engine.dispose()

    async def test_provider_failures_are_included_in_results(self):
        from app import service

        with tempfile.TemporaryDirectory() as directory:
            engine = create_engine(f"sqlite:///{Path(directory) / 'errors.db'}")
            Base.metadata.create_all(engine)
            test_sessions = sessionmaker(bind=engine, autoflush=False, autocommit=False)
            previous_check = datetime(2025, 1, 1)
            with test_sessions() as db:
                db.add(OSRelease(
                    slug="ubuntu", name="Ubuntu", version="26.04", major_version="26",
                    source_url="https://example.invalid", checked_at=previous_check,
                    first_seen_at=previous_check, updated_at=previous_check,
                ))
                db.commit()

            class FailingProvider:
                async def latest(self):
                    raise RuntimeError("provider unavailable")

            class WorkingProvider:
                def __init__(self, slug):
                    self.slug = slug

                async def latest(self):
                    return Release(self.slug, self.slug, "13", None, "https://example.invalid")

            providers = {"ubuntu": FailingProvider()}
            providers.update({f"working-{number}": WorkingProvider(f"working-{number}") for number in range(6)})
            with patch.object(service, "SessionLocal", test_sessions), \
                 patch.object(service, "PROVIDERS", providers):
                result = await service.check_all()

            self.assertEqual((result["checked"], result["failed"]), (6, 1))
            self.assertEqual(result["errors"], [{"slug": "ubuntu", "error": "provider unavailable"}])
            self.assertIsNotNone(result["finished_at"])
            self.assertEqual(service.last_check_finished_at, result["finished_at"])
            with test_sessions() as db:
                ubuntu = db.scalar(select(OSRelease).where(OSRelease.slug == "ubuntu"))
                self.assertEqual(ubuntu.checked_at, previous_check)
            engine.dispose()


async def _done():
    return None


if __name__ == "__main__":
    unittest.main()
