import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Unicode,
    UnicodeText,
    UniqueConstraint,
    create_engine,
    delete,
    insert,
    select,
)
from sqlalchemy.engine import Engine, URL

from .migrations import run_migrations

metadata = MetaData()
incidents = Table(
    "incidents",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("title", Unicode(500), nullable=False),
    Column("description", UnicodeText, nullable=False),
    Column("severity", Unicode(50), nullable=False),
    Column("status", Unicode(50), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)
tags = Table(
    "tags",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Unicode(255), nullable=False, unique=True),
)
incident_tags = Table(
    "incident_tags",
    metadata,
    Column("incident_id", Integer, ForeignKey("incidents.id"), nullable=False),
    Column("tag_id", Integer, ForeignKey("tags.id"), nullable=False),
    UniqueConstraint("incident_id", "tag_id"),
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
        URL.create("sqlite", database=str(data_dir / "incidents-service.db")),
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
            raise RuntimeError("Incidents database health probe could not be read.")
        connection.execute(
            delete(health_probes).where(health_probes.c.probe_id == probe_id)
        )
