import pytest

from incidents.service import (
	SEVERITY_LEVELS,
	STATUS_LEVELS,
	NotFoundError,
	ValidationError,
	add_tags,
	create_incident,
	get_incident,
	list_incidents,
	update_status,
	validate_severity,
	validate_status,
)
from incidents import service


def test_valid_status_transitions_are_accepted():
	for status in STATUS_LEVELS:
		assert validate_status(status) == status


def test_invalid_status_transition_raises_error():
	with pytest.raises(ValidationError):
		validate_status("Cancelled")


def test_valid_severities_are_accepted():
	for severity in SEVERITY_LEVELS:
		assert validate_severity(severity) == severity


def test_invalid_severity_raises_error():
	with pytest.raises(ValidationError):
		validate_severity("Urgent")


def test_create_incident_strips_fields_and_returns_incident(monkeypatch):
	created = {}

	def fake_create(title, description, severity, status):
		created.update(title=title, description=description, severity=severity, status=status)
		return 1

	monkeypatch.setattr(service.repository, "create_incident", fake_create)
	monkeypatch.setattr(service.repository, "add_tags_to_incident", lambda incident_id, tags: None)
	monkeypatch.setattr(service.repository, "get_incident_by_id", lambda incident_id: {"id": incident_id})
	monkeypatch.setattr(service.repository, "get_tags_for_incident", lambda incident_id: ["api"], raising=False)

	result = create_incident("  API down  ", "  Service unavailable  ", "High", tags=["api"])

	assert created == {
		"title": "API down",
		"description": "Service unavailable",
		"severity": "High",
		"status": "Open",
	}
	assert result == {"id": 1, "tags": ["api"]}


@pytest.mark.parametrize("title, description", [("", "details"), ("title", "")])
def test_create_incident_rejects_empty_fields(title, description):
	with pytest.raises(ValidationError):
		create_incident(title, description, "Low")


def test_list_incidents_delegates_to_repository(monkeypatch):
	incidents = [{"id": 1}]
	monkeypatch.setattr(service.repository, "list_incidents", lambda: incidents)

	assert list_incidents() == incidents


def test_get_incident_adds_tags(monkeypatch):
	monkeypatch.setattr(service.repository, "get_incident_by_id", lambda incident_id: {"id": incident_id})
	monkeypatch.setattr(service.repository, "get_tags_for_incident", lambda incident_id: ["database"], raising=False)

	assert get_incident(2) == {"id": 2, "tags": ["database"]}


def test_get_missing_incident_raises_error(monkeypatch):
	monkeypatch.setattr(service.repository, "get_incident_by_id", lambda incident_id: None)

	with pytest.raises(NotFoundError):
		get_incident(99)


def test_update_status_returns_updated_incident(monkeypatch):
	monkeypatch.setattr(service.repository, "update_incident", lambda incident_id, new_status: {"id": incident_id})
	monkeypatch.setattr(service.repository, "get_incident_by_id", lambda incident_id: {"id": incident_id})
	monkeypatch.setattr(service.repository, "get_tags_for_incident", lambda incident_id: [], raising=False)

	assert update_status(3, "Resolved") == {"id": 3, "tags": []}


def test_update_missing_incident_raises_error(monkeypatch):
	monkeypatch.setattr(service.repository, "update_incident", lambda incident_id, new_status: None)

	with pytest.raises(NotFoundError):
		update_status(99, "Closed")


def test_add_tags_returns_repository_tags(monkeypatch):
	monkeypatch.setattr(service.repository, "get_incident_by_id", lambda incident_id: {"id": incident_id})
	monkeypatch.setattr(service.repository, "get_tags_for_incident", lambda incident_id: ["urgent"], raising=False)
	monkeypatch.setattr(service.repository, "add_tags_to_incident", lambda incident_id, tags: None)

	assert add_tags(4, ["urgent"]) == ["urgent"]
