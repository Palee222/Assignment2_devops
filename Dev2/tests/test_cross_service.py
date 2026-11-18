import json
from io import BytesIO
from urllib.error import URLError

from fastapi.testclient import TestClient

from services.service1 import service as password_service
from services.service1.app import app as password_app
from services.service2.app import app as incidents_app


def test_weak_password_can_create_incident_without_sending_the_password(
    monkeypatch,
):
    monkeypatch.setattr(
        password_service, "get_weak_passwords", lambda: ["not-a-secret"]
    )
    with TestClient(incidents_app) as incidents_client:
        def send_to_incidents(request, timeout):
            payload = json.loads(request.data)
            assert timeout == 2
            assert "not-a-secret" not in request.data.decode()
            response = incidents_client.post("/incidents", json=payload)
            assert response.status_code == 200
            return BytesIO(response.content)

        monkeypatch.setattr(password_service, "urlopen", send_to_incidents)
        with TestClient(password_app) as password_client:
            response = password_client.post(
                "/password/api/check",
                json={
                    "password": "not-a-secret",
                    "report_as_incident": True,
                },
            )

        assert response.status_code == 200
        result = response.json()
        assert result["strength"] == "Weak"
        assert result["incident_report"]["status"] == "created"

        created = incidents_client.get(
            f"/incidents/{result['incident_report']['incident_id']}"
        )
        assert created.status_code == 200
        assert "not-a-secret" not in created.text


def test_incident_service_failure_does_not_fail_password_check(monkeypatch):
    def fail_to_send(request, timeout):
        raise URLError("incident service is down")

    monkeypatch.setattr(password_service, "urlopen", fail_to_send)
    with TestClient(password_app) as password_client:
        response = password_client.post(
            "/password/api/check",
            json={"password": "password", "report_as_incident": True},
        )

    assert response.status_code == 200
    result = response.json()
    assert result["strength"] == "Weak"
    assert result["incident_report"] == {
        "status": "unavailable",
        "incident_id": None,
    }


def test_request_logs_include_method_path_status_and_duration(caplog):
    caplog.set_level("INFO", logger="password-service")
    with TestClient(password_app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    request_events = [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "password-service" and record.message.startswith("{")
    ]
    assert {
        "event": "request",
        "method": "GET",
        "path": "/health",
        "status": 200,
    }.items() <= request_events[-1].items()
    assert isinstance(request_events[-1]["duration_ms"], float)
