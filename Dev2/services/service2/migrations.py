import hashlib
import logging
import re
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from sqlalchemy import Column, DateTime, MetaData, String, Table, insert, select, text
from sqlalchemy.engine import Connection, Engine

MIGRATION_DIR = Path(__file__).resolve().parent / "migrations"
MIGRATION_NAME = re.compile(r"(?P<number>\d{3})_[a-z0-9_]+\.sql")
logger = logging.getLogger("incidents-service")

metadata = MetaData()
schema_migrations = Table(
    "schema_migrations",
    metadata,
    Column("service", String(32), primary_key=True),
    Column("version", String(255), primary_key=True),
    Column("checksum", String(64), nullable=False),
    Column("applied_at", DateTime(timezone=True), nullable=False),
)


def _migration_files(dialect: str) -> list[Path]:
    if dialect not in {"sqlite", "mssql"}:
        raise RuntimeError(f"Unsupported migration database dialect: {dialect}")
    files = sorted((MIGRATION_DIR / dialect).glob("*.sql"))
    numbers = []
    for path in files:
        match = MIGRATION_NAME.fullmatch(path.name)
        if match is None:
            raise RuntimeError(f"Invalid migration filename: {path.name}")
        numbers.append(int(match.group("number")))
    if not files or numbers != list(range(1, len(numbers) + 1)):
        raise RuntimeError("Incidents migrations must be numbered consecutively.")
    return files


def _execute_migration(connection: Connection, path: Path, dialect: str) -> None:
    sql = path.read_text(encoding="utf-8")
    if dialect == "mssql":
        connection.exec_driver_sql(sql)
    else:
        for statement in sql.split(";"):
            if statement.strip():
                connection.exec_driver_sql(statement)


@contextmanager
def _migration_transaction(engine: Engine) -> Iterator[Connection]:
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
                {"resource": "schema-migrations:incidents"},
            ).scalar_one()
            if lock_result < 0:
                raise RuntimeError(
                    "Could not acquire the incidents migration lock "
                    f"(SQL Server returned {lock_result})."
                )
            yield connection


def run_migrations(engine: Engine) -> None:
    files = _migration_files(engine.dialect.name)
    with _migration_transaction(engine) as connection:
        metadata.create_all(connection, tables=[schema_migrations])
        applied = dict(
            connection.execute(
                select(schema_migrations.c.version, schema_migrations.c.checksum).where(
                    schema_migrations.c.service == "incidents"
                )
            ).all()
        )

    available = {path.name for path in files}
    unknown = set(applied) - available
    if unknown:
        raise RuntimeError(
            "Incidents database has migrations absent from this release: "
            + ", ".join(sorted(unknown))
        )

    for path in files:
        checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        with _migration_transaction(engine) as connection:
            stored_checksum = connection.execute(
                select(schema_migrations.c.checksum).where(
                    schema_migrations.c.service == "incidents",
                    schema_migrations.c.version == path.name,
                )
            ).scalar_one_or_none()
            if stored_checksum is not None:
                if stored_checksum != checksum:
                    raise RuntimeError(
                        f"Applied migration {path.name} was modified; "
                        "create a new migration instead."
                    )
                continue
            _execute_migration(connection, path, engine.dialect.name)
            connection.execute(
                insert(schema_migrations).values(
                    service="incidents",
                    version=path.name,
                    checksum=checksum,
                    applied_at=datetime.now(timezone.utc),
                )
            )
        logger.info("Applied incidents migration %s", path.name)
