from datetime import datetime
from pathlib import Path
from sqlalchemy import DateTime, Integer, String, Text, Boolean, ForeignKey, UniqueConstraint, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from .config import settings


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    # Encoded PBKDF2 record: algorithm$iterations$salt_hex$digest_hex.
    password_hash: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(20), default="user", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class OSRelease(Base):
    __tablename__ = "os_releases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    version: Mapped[str] = mapped_column(String(50))
    major_version: Mapped[str] = mapped_column(String(30), default="")
    release_date: Mapped[str | None] = mapped_column(String(30), nullable=True)
    source_url: Mapped[str] = mapped_column(Text)
    release_type: Mapped[str] = mapped_column(String(30), default="stable")
    is_rolling: Mapped[bool] = mapped_column(Boolean, default=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ReleaseHistory(Base):
    __tablename__ = "release_history"
    __table_args__ = (UniqueConstraint("os_id", "version", name="uq_release_history_os_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    os_id: Mapped[int] = mapped_column(ForeignKey("os_releases.id", ondelete="CASCADE"), index=True)
    version: Mapped[str] = mapped_column(String(50))
    major_version: Mapped[str] = mapped_column(String(30))
    release_type: Mapped[str] = mapped_column(String(30))
    release_date: Mapped[str | None] = mapped_column(String(30), nullable=True)
    source_url: Mapped[str] = mapped_column(Text)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class ReleaseEvent(Base):
    __tablename__ = "release_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    os_id: Mapped[int] = mapped_column(ForeignKey("os_releases.id", ondelete="CASCADE"), index=True)
    previous_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    new_version: Mapped[str] = mapped_column(String(50))
    previous_major_version: Mapped[str | None] = mapped_column(String(30), nullable=True)
    new_major_version: Mapped[str] = mapped_column(String(30))
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    notification_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    notification_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


def ensure_sqlite_directory(database_url: str) -> None:
    url = make_url(database_url)
    if url.get_backend_name() != "sqlite" or not url.database or url.database == ":memory:":
        return
    Path(url.database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False, "timeout": 30} if settings.database_url.startswith("sqlite") else {},
)

if engine.dialect.name == "sqlite":
    @event.listens_for(engine, "connect")
    def _configure_sqlite_connection(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    ensure_sqlite_directory(settings.database_url)
    Base.metadata.create_all(engine)
    # Preserve the existing environment-configured administrator as the
    # one-time bootstrap account. Subsequent credentials live in the users table.
    if settings.admin_password_hash and settings.admin_password_salt:
        try:
            salt = bytes.fromhex(settings.admin_password_salt)
            digest = bytes.fromhex(settings.admin_password_hash)
        except ValueError:
            salt = digest = b""
        if salt and digest:
            encoded = f"pbkdf2_sha256$310000${salt.hex()}${digest.hex()}"
            with sessionmaker(bind=engine, autoflush=False, autocommit=False).begin() as db:
                admin = db.query(User).filter(User.username == settings.admin_username).one_or_none()
                if admin is None:
                    db.add(User(
                        username=settings.admin_username,
                        password_hash=encoded,
                        role="admin",
                        is_active=True,
                    ))
    # Lightweight migration for the existing SQLite database shipped with v1.x.
    if settings.database_url.startswith("sqlite"):
        with engine.begin() as conn:
            columns = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(os_releases)").fetchall()}
            migrations = {
                "major_version": "ALTER TABLE os_releases ADD COLUMN major_version VARCHAR(30) DEFAULT ''",
                "first_seen_at": "ALTER TABLE os_releases ADD COLUMN first_seen_at DATETIME",
                "updated_at": "ALTER TABLE os_releases ADD COLUMN updated_at DATETIME",
            }
            for name, sql in migrations.items():
                if name not in columns:
                    conn.exec_driver_sql(sql)
            conn.exec_driver_sql(
                "UPDATE os_releases SET first_seen_at = COALESCE(first_seen_at, checked_at), "
                "updated_at = COALESCE(updated_at, checked_at), major_version = COALESCE(NULLIF(major_version, ''), 'unknown')"
            )
