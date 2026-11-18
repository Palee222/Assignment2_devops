from fastapi.testclient import TestClient

from services.service1.app import app
from services.service1 import service


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
