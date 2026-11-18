import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Unicode,
    UnicodeText,
    create_engine,
    insert,
    select,
    delete,
)
from sqlalchemy.engine import Engine, URL

from .migrations import run_migrations

metadata = MetaData()
weak_passwords = Table(
    "weak_passwords",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("password", Unicode(255), nullable=False),
    Column("source", Unicode(255)),
    Column("is_active", Boolean, nullable=False, server_default="1"),
)
password_rules = Table(
    "password_rules",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Unicode(255), nullable=False),
    Column("description", UnicodeText),
    Column("min_length", Integer),
    Column("require_upper", Boolean),
    Column("require_lower", Boolean),
    Column("require_digit", Boolean),
    Column("require_symbol", Boolean),
)
health_probes = Table(
    "health_probes",
    metadata,
    Column("probe_id", String(36), primary_key=True),
    Column("checked_at", DateTime(timezone=True), nullable=False),
)


def _create_engine() -> Engine:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return create_engine(database_url, pool_pre_ping=True)

    data_dir = Path(os.getenv("DATA_DIR", "/tmp"))
    data_dir.mkdir(parents=True, exist_ok=True)
    return create_engine(
        URL.create("sqlite", database=str(data_dir / "password-service.db")),
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )


engine = _create_engine()


def init_db() -> None:
    run_migrations(engine)


def check_database_health() -> None:
    probe_id = str(uuid.uuid4())
    checked_at = datetime.now(timezone.utc)
    with engine.begin() as connection:
        connection.execute(
            insert(health_probes).values(probe_id=probe_id, checked_at=checked_at)
        )
        stored_probe = connection.execute(
            select(health_probes.c.probe_id).where(
                health_probes.c.probe_id == probe_id
            )
        ).scalar_one()
        if stored_probe != probe_id:
            raise RuntimeError("Password database health probe could not be read.")
        connection.execute(
            delete(health_probes).where(health_probes.c.probe_id == probe_id)
        )
