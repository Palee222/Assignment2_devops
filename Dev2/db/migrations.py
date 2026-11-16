import hashlib
import logging
import re
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from sqlalchemy import (
    Column,
    DateTime,
    MetaData,
    String,
    Table,
    insert,
    select,
    text,
)
from sqlalchemy.engine import Connection, Engine

logger = logging.getLogger(__name__)

_MIGRATIONS_ROOT = Path(__file__).resolve().parents[1] / "src"
_SERVICES = {"password", "incidents"}
_MIGRATION_NAME = re.compile(r"(?P<number>\d{3})_[a-z0-9_]+\.sql")

_migration_metadata = MetaData()
schema_migrations = Table(
    "schema_migrations",
    _migration_metadata,
    Column("service", String(32), primary_key=True),
    Column("version", String(255), primary_key=True),
    Column("checksum", String(64), nullable=False),
    Column("applied_at", DateTime(timezone=True), nullable=False),
)


def _migration_files(service: str, dialect: str) -> list[Path]:
    if service not in _SERVICES:
        raise ValueError(f"Unsupported database service: {service}")
    if dialect not in {"sqlite", "mssql"}:
        raise RuntimeError(f"Unsupported migration database dialect: {dialect}")

    directory = _MIGRATIONS_ROOT / service / "migrations" / dialect
    files = sorted(directory.glob("*.sql"))
    if not files:
        raise RuntimeError(f"No {dialect} migrations found for {service}.")

    numbers = []
    for path in files:
        match = _MIGRATION_NAME.fullmatch(path.name)
        if match is None:
            raise RuntimeError(f"Invalid migration filename: {path.name}")
        numbers.append(int(match.group("number")))

    if numbers != list(range(1, len(numbers) + 1)):
        raise RuntimeError(f"{service} migrations must be numbered consecutively.")
    return files


def _execute_migration(connection, path: Path, dialect: str) -> None:
    sql = path.read_text(encoding="utf-8")
    if dialect == "mssql":
        connection.exec_driver_sql(sql)
        return

    for statement in sql.split(";"):
        statement = statement.strip()
        if statement:
            connection.exec_driver_sql(statement)


@contextmanager
def _migration_transaction(engine: Engine, service: str) -> Iterator[Connection]:
    with engine.connect() as connection:
        if engine.dialect.name == "sqlite":
            connection.exec_driver_sql("BEGIN IMMEDIATE")
            try:
                yield connection
            except BaseException:
                connection.rollback()
                raise
            else:
                connection.commit()
            return

        with connection.begin():
            lock_result = connection.execute(
                text(
                    "DECLARE @lock_result int; "
                    "EXEC @lock_result = sys.sp_getapplock "
                    "@Resource = :resource, "
                    "@LockMode = 'Exclusive', "
                    "@LockOwner = 'Transaction', "
                    "@LockTimeout = 60000; "
                    "SELECT @lock_result;"
                ),
                {"resource": f"schema-migrations:{service}"},
            ).scalar_one()
            if lock_result < 0:
                raise RuntimeError(
                    f"Could not acquire the {service} migration lock "
                    f"(SQL Server returned {lock_result})."
                )
            yield connection


def run_migrations(engine: Engine, service: str) -> None:
    files = _migration_files(service, engine.dialect.name)
    with _migration_transaction(engine, service) as connection:
        _migration_metadata.create_all(connection, tables=[schema_migrations])
    available_versions = {path.name for path in files}

    with engine.connect() as connection:
        applied_checksums = dict(
            connection.execute(
                select(
                    schema_migrations.c.version,
                    schema_migrations.c.checksum,
                ).where(
                    schema_migrations.c.service == service,
                )
            ).all()
        )

    unknown_versions = set(applied_checksums) - available_versions
    if unknown_versions:
        versions = ", ".join(sorted(unknown_versions))
        raise RuntimeError(
            f"Database has {service} migrations absent from this release: {versions}."
        )

    for path in files:
        checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        stored_checksum = applied_checksums.get(path.name)
        if stored_checksum is not None:
            if stored_checksum != checksum:
                raise RuntimeError(
                    f"Applied migration {path.name} was modified; "
                    "create a new migration instead."
                )
            continue

        with _migration_transaction(engine, service) as connection:
            already_applied = connection.execute(
                select(schema_migrations.c.checksum).where(
                    schema_migrations.c.service == service,
                    schema_migrations.c.version == path.name,
                )
            ).scalar_one_or_none()
            if already_applied is not None:
                if already_applied != checksum:
                    raise RuntimeError(
                        f"Applied migration {path.name} was modified; "
                        "create a new migration instead."
                    )
                applied_checksums[path.name] = already_applied
                continue

            _execute_migration(connection, path, engine.dialect.name)
            connection.execute(
                insert(schema_migrations).values(
                    service=service,
                    version=path.name,
                    checksum=checksum,
                    applied_at=datetime.now(timezone.utc),
                )
            )
        applied_checksums[path.name] = checksum
        logger.info("Applied %s migration %s", service, path.name)
