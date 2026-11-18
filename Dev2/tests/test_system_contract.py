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
