import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from services.service2 import service
from services.service2.app import app
from services.service2 import database, migrations, repository


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


def test_incident_service_list_get_and_status(monkeypatch):
    incidents = [
        {"id": 1, "title": "First", "description": "Details", "severity": "Low", "status": "Open"}
    ]
    monkeypatch.setattr(repository, "list_incidents", lambda: incidents)
    monkeypatch.setattr(repository, "get_tags_for_incident", lambda incident_id: ["api"])
    monkeypatch.setattr(
        repository,
        "get_incident_by_id",
        lambda incident_id: dict(incidents[0]) if incident_id == 1 else None,
    )
    def update_status(incident_id, new_status):
        incidents[0]["status"] = new_status
        return incidents[0]

    monkeypatch.setattr(repository, "update_incident_status", update_status)

    assert service.list_incidents() == [dict(incidents[0], tags=["api"])]
    assert service.get_incident(1)["tags"] == ["api"]
    assert service.update_status(1, "Resolved")["status"] == "Resolved"
    with pytest.raises(service.NotFoundError):
        service.get_incident(999)


def test_incident_routes_validate_and_not_found():
    with TestClient(app) as client:
        invalid = client.post(
            "/incidents",
            json={
                "title": "",
                "description": "Details",
                "severity": "High",
            },
        )
        missing = client.get("/incidents/999999")
        bad_status = client.post(
            "/incidents/999999/status",
            json={"status": "Cancelled"},
        )

    assert invalid.status_code == 422
    assert missing.status_code == 404
    assert bad_status.status_code == 422


def test_incident_repository_database_crud(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(repository, "engine", engine)
    migrations.run_migrations(engine)

    incident_id = repository.create_incident("Database outage", "API unavailable", "High", "Open")
    repository.add_tags_to_incident(incident_id, ["api", "api", "", "production"])

    incident = repository.get_incident_by_id(incident_id)
    assert incident["title"] == "Database outage"
    assert repository.get_tags_for_incident(incident_id) == ["api", "production"]
    assert repository.update_incident_status(incident_id, "Resolved")["status"] == "Resolved"
    assert repository.update_incident_status(999999, "Closed") is None
    assert len(repository.list_incidents()) == 1
    engine.dispose()
