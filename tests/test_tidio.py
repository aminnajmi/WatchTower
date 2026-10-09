import asyncio
from datetime import datetime

from app.tidio import TidioMonitor, TidioSnapshot


def test_tidio_snapshot_defaults():
    snapshot = TidioSnapshot(False, "not_configured")
    assert snapshot.connected is False
    assert snapshot.unassigned_count == 0


def test_tidio_password_encryption_round_trip():
    monitor = TidioMonitor()
    encrypted = monitor.encrypt_password("example-password")
    assert encrypted != "example-password"
    assert monitor.decrypt_password(encrypted) == "example-password"
