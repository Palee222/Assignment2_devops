import json
from pathlib import Path

import yaml
from jsonschema import validate

ROOT = Path(__file__).resolve().parents[1]


def test_system_configuration_matches_its_schema():
    configuration = yaml.safe_load((ROOT / "system.yaml").read_text())
    schema = json.loads((ROOT / "system.schema.json").read_text())

    validate(configuration, schema)


def test_each_service_openapi_document_names_a_health_route():
    for service in ("service1", "service2"):
        specification = yaml.safe_load(
            (ROOT / "services" / service / "openapi.yaml").read_text()
        )

        assert specification["openapi"] == "3.1.0"
        assert "/health" in specification["paths"]


def test_compose_uses_local_sql_server_not_azure_sql():
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text())

    sqlserver = compose["services"]["sqlserver"]
    assert sqlserver["image"].startswith("mcr.microsoft.com/mssql/server:")
    assert "127.0.0.1:1433:1433" in sqlserver["ports"]

    for service_name in ("password-service", "incidents-service"):
        database_url = compose["services"][service_name]["environment"]["DATABASE_URL"]
        assert "@sqlserver:1433/" in database_url
        assert "ODBC+Driver+18+for+SQL+Server" in database_url
        assert "azure" not in database_url.lower()
