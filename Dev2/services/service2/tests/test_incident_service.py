import pytest
from fastapi.testclient import TestClient

from services.service2 import service
from services.service2.app import app


def test_valid_statuses_and_severities_are_accepted():
    for status in service.STATUS_LEVELS:
        assert service.validate_status(status) == status
    for severity in service.SEVERITY_LEVELS:
        assert service.validate_severity(severity) == severity


def test_invalid_status_and_severity_are_rejected():
    with pytest.raises(service.ValidationError):
        service.validate_status("Cancelled")
    with pytest.raises(service.ValidationError):
        service.validate_severity("Urgent")


def test_create_incident_strips_fields_and_attaches_tags(monkeypatch):
    created = {}
    monkeypatch.setattr(
        service.repository,
        "create_incident",
        lambda title, description, severity, status: (
            created.update(
                title=title, description=description, severity=severity, status=status
            )
            or 1
        ),
    )
    monkeypatch.setattr(
        service.repository, "add_tags_to_incident", lambda incident_id, tags: None
    )
    monkeypatch.setattr(
        service.repository,
        "get_incident_by_id",
        lambda incident_id: {"id": incident_id},
    )
    monkeypatch.setattr(
        service.repository, "get_tags_for_incident", lambda incident_id: ["api"]
    )

    result = service.create_incident(
        "  API down  ", "  Service unavailable  ", "High", tags=["api"]
    )

    assert created == {
        "title": "API down",
        "description": "Service unavailable",
        "severity": "High",
        "status": "Open",
    }
    assert result == {"id": 1, "tags": ["api"]}


@pytest.mark.parametrize(("title", "description"), [("", "details"), ("title", "")])
def test_create_incident_rejects_empty_fields(title, description):
    with pytest.raises(service.ValidationError):
        service.create_incident(title, description, "Low")


def test_health_returns_database_and_git_sha(monkeypatch):
    monkeypatch.setenv("GIT_SHA", "test-sha")

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "ok",
        "git_sha": "test-sha",
    }


def test_health_returns_503_when_database_probe_fails(monkeypatch):
    import services.service2.app as app_module

    def fail_health_check():
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(app_module, "check_database_health", fail_health_check)

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["database"] == "unavailable"
