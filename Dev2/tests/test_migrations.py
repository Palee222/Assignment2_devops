from sqlalchemy import create_engine, select, text

from db import db
from db.migrations import run_migrations, schema_migrations


def test_password_migration_preserves_existing_rows_and_runs_once():
    engine = create_engine("sqlite:///:memory:")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE weak_passwords ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "password VARCHAR(255) NOT NULL, "
                    "source VARCHAR(255))"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO weak_passwords (password, source) "
                    "VALUES (:password, :source)"
                ),
                {"password": "legacy-password", "source": "test"},
            )

        run_migrations(engine, "password")
        run_migrations(engine, "password")
        run_migrations(engine, "incidents")
        run_migrations(engine, "incidents")

        with engine.connect() as connection:
            password = connection.exec_driver_sql(
                "SELECT password, source, is_active FROM weak_passwords"
            ).one()
            password_versions = connection.execute(
                select(schema_migrations.c.version).where(
                    schema_migrations.c.service == "password"
                )
            ).scalars().all()
            incident_versions = connection.execute(
                select(schema_migrations.c.version).where(
                    schema_migrations.c.service == "incidents"
                )
            ).scalars().all()

        assert tuple(password) == ("legacy-password", "test", 1)
        assert password_versions == [
            "001_init.sql",
            "002_add_weak_password_active.sql",
        ]
        assert incident_versions == ["001_init.sql"]
    finally:
        engine.dispose()


def test_init_db_runs_migrations_for_both_services(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    monkeypatch.setattr(db, "engine", engine)
    try:
        db.init_db()

        with engine.connect() as connection:
            services = set(
                connection.execute(
                    select(schema_migrations.c.service)
                ).scalars()
            )

        assert services == {"password", "incidents"}
    finally:
        engine.dispose()
