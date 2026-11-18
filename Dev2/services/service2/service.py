from . import repository

Severity = str
Status = str
SEVERITY_LEVELS = ["Low", "Medium", "High", "Critical"]
STATUS_LEVELS = ["Open", "In Progress", "Resolved", "Closed"]


class ValidationError(ValueError):
    pass


class NotFoundError(LookupError):
    pass


def validate_severity(severity: str) -> Severity:
    if severity not in SEVERITY_LEVELS:
        raise ValidationError(f"Severity must be one of: {', '.join(SEVERITY_LEVELS)}.")
    return severity


def validate_status(status: str) -> Status:
    if status not in STATUS_LEVELS:
        raise ValidationError(f"Status must be one of: {', '.join(STATUS_LEVELS)}.")
    return status


def create_incident(
    title: str,
    description: str,
    severity: str,
    status: str = "Open",
    tags: list[str] | None = None,
) -> dict:
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


def list_incidents() -> list[dict]:
    result = repository.list_incidents()
    for incident in result:
        incident["tags"] = repository.get_tags_for_incident(incident["id"])
    return result


def get_incident(incident_id: int) -> dict:
    incident = repository.get_incident_by_id(incident_id)
    if incident is None:
        raise NotFoundError(f"No incident with id {incident_id}.")
    incident["tags"] = repository.get_tags_for_incident(incident_id)
    return incident


def update_status(incident_id: int, status: str) -> dict:
    validate_status(status)
    updated = repository.update_incident_status(incident_id, new_status=status)
    if updated is None:
        raise NotFoundError(f"No incident with id {incident_id}.")
    return get_incident(incident_id)
