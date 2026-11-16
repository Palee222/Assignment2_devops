import os
from pathlib import Path

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    Table,
    Unicode,
    UnicodeText,
    UniqueConstraint,
    create_engine,
    insert as sqlalchemy_insert,
    text,
)
from sqlalchemy.engine import Connection, Engine, URL
from sqlalchemy.exc import SQLAlchemyError

from db.migrations import run_migrations

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
DB_PATH = DATA_DIR / "secnote.db"

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

weak_passwords = Table(
    "weak_passwords",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("password", Unicode(255), nullable=False),
    Column("source", Unicode(255)),
    Column("is_active", Boolean, nullable=False, server_default=text("1")),
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

_TABLES = {
    "password_rules": password_rules,
}

_SERVICE_TABLES = {
    "password": (weak_passwords, password_rules),
    "incidents": (incidents, tags, incident_tags),
}


def _create_engine() -> Engine:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return create_engine(database_url, pool_pre_ping=True)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return create_engine(
        URL.create("sqlite", database=str(DB_PATH.resolve())),
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )


engine = _create_engine()


def get_connection() -> Connection:
    return engine.connect()


def insert(table_name: str, values: dict) -> int:
    table = _TABLES.get(table_name)
    if table is None:
        raise ValueError(f"Unsupported table: {table_name}")

    try:
        with engine.begin() as conn:
            result = conn.execute(sqlalchemy_insert(table).values(**values))
            record_id = result.inserted_primary_key[0]
            if record_id is None:
                raise RuntimeError(f"The {table_name} record was not inserted.")
            return record_id
    except SQLAlchemyError as error:
        raise RuntimeError(f"Could not insert into {table_name}: {error}") from error


def init_db(service: str | None = None) -> None:
    if service is None:
        run_migrations(engine, "password")
        run_migrations(engine, "incidents")
        return

    if service not in _SERVICE_TABLES:
        raise ValueError(f"Unsupported database service: {service}")
    run_migrations(engine, service)
