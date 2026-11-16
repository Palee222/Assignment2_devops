"""service.py for the incidents business logic.

The allowed severity and status values live here, and so does the validation
that uses them. Routes translate the errors raised here into HTTP responses;
the repository stays a thin SQL layer.
"""

from typing import Literal

from incidents import repository

Severity = Literal["Low", "Medium", "High", "Critical"]
Status = Literal["Open", "In Progress", "Resolved", "Closed"]

SEVERITY_LEVELS = ["Low", "Medium", "High", "Critical"]
STATUS_LEVELS = ["Open", "In Progress", "Resolved", "Closed"]

# Kept for backwards compatibility with the original lowercase names.
severity_levels = SEVERITY_LEVELS
status_levels = STATUS_LEVELS


class ValidationError(ValueError):
    """Raised when incoming data fails a business rule."""


class NotFoundError(LookupError):
    """Raised when an incident id does not exist."""


def validate_severity(severity):
    if severity not in SEVERITY_LEVELS:
        raise ValidationError(
            f"Severity must be one of: {', '.join(SEVERITY_LEVELS)}."
        )
    return severity


def validate_status(status):
    if status not in STATUS_LEVELS:
        raise ValidationError(
            f"Status must be one of: {', '.join(STATUS_LEVELS)}."
        )
    return status


def create_incident(title, description, severity, status="Open", tags=None):
    title = title.strip()
    description = description.strip()
    if not title:
        raise ValidationError("Title cannot be empty.")
    if not description:
        raise ValidationError("Description cannot be empty.")

    validate_severity(severity)
    validate_status(status)

    incident_id = repository.create_incident(title, description, severity, status)

    if tags:
        repository.add_tags_to_incident(incident_id, tags)

    return get_incident(incident_id)


def list_incidents():
    return repository.list_incidents()


def get_incident(incident_id):
    incident = repository.get_incident_by_id(incident_id)
    if incident is None:
        raise NotFoundError(f"No incident with id {incident_id}.")
    incident["tags"] = repository.get_tags_for_incident(incident_id)
    return incident


def update_status(incident_id, status):
    validate_status(status)
    updated = repository.update_incident(incident_id, new_status=status)
    if updated is None:
        raise NotFoundError(f"No incident with id {incident_id}.")
    return get_incident(incident_id)


def add_tags(incident_id, tags):
    get_incident(incident_id)  # raises NotFoundError if the incident is gone
    repository.add_tags_to_incident(incident_id, tags)
    return repository.get_tags_for_incident(incident_id)
