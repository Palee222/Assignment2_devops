from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool

from services.service1.app import app
from services.service1 import service
from services.service1 import database, migrations, repository


def test_short_password_is_weak(monkeypatch):
    monkeypatch.setattr(service, "get_weak_passwords", lambda: [])

    result = service.score_password("abc123")

    assert result["score"] < 40
    assert result["strength"] == "Weak"


def test_long_mixed_character_password_is_strong(monkeypatch):
    monkeypatch.setattr(service, "get_weak_passwords", lambda: [])

    result = service.score_password("LongPassword123!")

    assert result["score"] >= 70
    assert result["strength"] in {"Strong", "Very Strong"}


def test_weak_password_list_forces_known_weak_password_low(monkeypatch):
    monkeypatch.setattr(service, "get_weak_passwords", lambda: ["password"])

    result = service.score_password("password")

    assert result["score"] < 40
    assert result["strength"] == "Weak"
    assert any("weak-password list" in item for item in result["feedback"])


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
    import services.service1.app as app_module

    def fail_health_check():
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(app_module, "check_database_health", fail_health_check)

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["database"] == "unavailable"


def test_password_check_routes_do_not_report_when_not_requested_or_strong(monkeypatch):
    monkeypatch.setattr(service, "get_weak_passwords", lambda: [])
    from services.service1 import routes
    monkeypatch.setattr(
        routes,
        "report_weak_password",
        lambda _score, _strength: {"status": "created", "incident_id": 7},
    )

    with TestClient(app) as client:
        not_requested = client.post(
            "/password/api/check",
            json={"password": "weak", "report_as_incident": False},
        )
        weak_reported = client.post(
            "/password/api/check",
            json={"password": "weak", "report_as_incident": True},
        )
        strong = client.post(
            "/password/api/check",
            json={"password": "LongPassword123!", "report_as_incident": True},
        )

    assert not_requested.status_code == 200
    assert not_requested.headers["cache-control"] == "no-store"
    assert not_requested.json()["incident_report"]["status"] == "not_requested"
    assert weak_reported.status_code == 200
    assert weak_reported.json()["incident_report"]["status"] == "created"
    assert strong.status_code == 200
    assert strong.json()["incident_report"] == {
        "status": "not_needed",
        "incident_id": None,
    }


def test_report_weak_password_handles_http_timeout(monkeypatch):
    def timeout(_request, timeout):
        assert timeout == 2
        raise TimeoutError("timed out")

    monkeypatch.setenv("INCIDENTS_TIMEOUT_S", "2")
    monkeypatch.setattr(service, "urlopen", timeout)

    result = service.report_weak_password(30, "Weak")

    assert result == {"status": "unavailable", "incident_id": None}


def test_report_weak_password_rejects_invalid_timeout(monkeypatch):
    monkeypatch.setenv("INCIDENTS_TIMEOUT_S", "0")

    try:
        service.report_weak_password(30, "Weak")
    except ValueError as error:
        assert "greater than zero" in str(error)
    else:
        raise AssertionError("zero timeout should be rejected")


def test_password_repository_database_crud(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(repository, "engine", engine)
    migrations.run_migrations(engine)

    repository.seed_weak_passwords()
    assert "password" in repository.get_weak_passwords()

    with engine.begin() as connection:
        connection.execute(
            database.weak_passwords.update()
            .where(database.weak_passwords.c.password == "password")
            .values(is_active=False)
        )
    assert "password" not in repository.get_weak_passwords()
    engine.dispose()
