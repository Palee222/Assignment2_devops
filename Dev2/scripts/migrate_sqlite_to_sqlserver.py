import argparse
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import Boolean, DateTime, func, insert, select
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.sql.schema import Table

SERVICE_TABLES = {
    "password": ("weak_passwords", "password_rules"),
    "incidents": ("incidents", "tags", "incident_tags"),
}
BATCH_SIZE = 500
DEFAULT_SOURCE = Path(__file__).resolve().parents[1] / "data" / "secnote.db"


def _connect_source(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _validate_source_schema(
    source: sqlite3.Connection,
    target_tables: dict[str, Table],
    table_names: tuple[str, ...],
) -> None:
    source_table_names = {
        row[0]
        for row in source.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name NOT LIKE 'sqlite_%'"
        )
    }

    for table_name in table_names:
        if table_name not in source_table_names:
            raise RuntimeError(f"Source database is missing table {table_name!r}.")

        source_columns = {
            row[1]
            for row in source.execute(f'PRAGMA table_info("{table_name}")')
        }
        target_columns = {column.name for column in target_tables[table_name].columns}
        if not source_columns.issubset(target_columns):
            raise RuntimeError(
                f"Source table {table_name!r} has columns absent from the target."
            )
        missing_columns = target_columns - source_columns
        missing_required_columns = {
            column.name
            for column in target_tables[table_name].columns
            if column.name in missing_columns
            and column.server_default is None
            and column.default is None
        }
        if missing_required_columns:
            raise RuntimeError(
                f"Source table {table_name!r} is missing required columns: "
                f"{', '.join(sorted(missing_required_columns))}."
            )


def _source_counts(
    source: sqlite3.Connection, table_names: tuple[str, ...]
) -> dict[str, int]:
    return {
        table_name: source.execute(
            f'SELECT COUNT(*) FROM "{table_name}"'
        ).fetchone()[0]
        for table_name in table_names
    }


def _convert_value(column, value):
    if value is None:
        return None
    if isinstance(column.type, DateTime) and isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
    if isinstance(column.type, Boolean):
        return bool(value)
    return value


def _source_batches(
    source: sqlite3.Connection, table: Table, batch_size: int = BATCH_SIZE
):
    cursor = source.execute(f'SELECT * FROM "{table.name}"')
    while rows := cursor.fetchmany(batch_size):
        yield [
            {
                column.name: _convert_value(column, row[column.name])
                for column in table.columns
                if column.name in row.keys()
            }
            for row in rows
        ]


def _ensure_target_empty(
    connection: Connection,
    tables: dict[str, Table],
    table_names: tuple[str, ...],
) -> None:
    nonempty_tables = [
        name
        for name in table_names
        if connection.scalar(
            select(func.count()).select_from(tables[name])
        )
    ]
    if nonempty_tables:
        raise RuntimeError(
            "Target database must be empty before migration; "
            f"these tables already contain rows: {', '.join(nonempty_tables)}."
        )


def _copy_table(
    source: sqlite3.Connection,
    target: Connection,
    table: Table,
    target_dialect: str,
    source_count: int,
) -> int:
    if source_count == 0:
        return 0

    identity_insert = target_dialect == "mssql" and "id" in table.c
    quoted_table_name = target.dialect.identifier_preparer.quote(table.name)
    if identity_insert:
        target.exec_driver_sql(f"SET IDENTITY_INSERT {quoted_table_name} ON")

    copied = 0
    try:
        for batch in _source_batches(source, table):
            target.execute(insert(table), batch)
            copied += len(batch)
    finally:
        if identity_insert:
            target.exec_driver_sql(f"SET IDENTITY_INSERT {quoted_table_name} OFF")

    if copied != source_count:
        raise RuntimeError(
            f"Copied {copied} of {source_count} rows from {table.name}."
        )
    return copied


def migrate(
    source_path: Path,
    engine: Engine,
    tables: dict[str, Table],
    service: str,
) -> None:
    if engine.dialect.name != "mssql":
        raise RuntimeError("DATABASE_URL must point to a SQL Server database.")

    table_names = SERVICE_TABLES[service]
    with closing(_connect_source(source_path)) as source:
        _validate_source_schema(source, tables, table_names)
        source_counts = _source_counts(source, table_names)

        with engine.begin() as target:
            _ensure_target_empty(target, tables, table_names)
            for table_name in table_names:
                _copy_table(
                    source,
                    target,
                    tables[table_name],
                    engine.dialect.name,
                    source_counts[table_name],
                )

            target_counts = {
                table_name: target.scalar(
                    select(func.count()).select_from(tables[table_name])
                )
                for table_name in table_names
            }
            if target_counts != source_counts:
                raise RuntimeError("Post-migration row counts do not match the source.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Copy one service's SQLite tables into its empty SQL Server database."
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--service", choices=tuple(SERVICE_TABLES), required=True)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write to the SQL Server database configured by DATABASE_URL",
    )
    args = parser.parse_args()

    if not args.source.is_file():
        raise SystemExit(f"Source database not found: {args.source}")

    if not args.apply:
        with closing(_connect_source(args.source)) as source:
            source_table_names = {
                row[0]
                for row in source.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table' "
                    "AND name NOT LIKE 'sqlite_%'"
                )
            }
            table_names = SERVICE_TABLES[args.service]
            missing_tables = set(table_names) - source_table_names
            if missing_tables:
                raise SystemExit(
                    "Source database is missing tables: "
                    + ", ".join(sorted(missing_tables))
                )
            counts = _source_counts(source, table_names)
        for table_name in table_names:
            print(f"{table_name}: {counts[table_name]} rows")
        print("Dry run only. Add --apply to copy into the configured SQL Server database.")
        return

    from db import db

    tables = {table.name: table for table in db.metadata.sorted_tables}
    db.init_db(args.service)
    migrate(args.source, db.engine, tables, args.service)
    print("SQLite data migration completed and row counts were verified.")


if __name__ == "__main__":
    main()
