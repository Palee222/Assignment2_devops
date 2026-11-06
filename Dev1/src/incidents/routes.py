#service.py for the business logic
#AI used here for code generation and suggestions
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from incidents.repository import (
    create_incident,
    list_incidents,
    get_incident_by_id,
    update_incident,
)

router = APIRouter(prefix="/incidents", tags=["incidents"])


class IncidentCreate(BaseModel):
    title: str
    description: str
    severity: str
    status: str = "Open"


class IncidentStatusUpdate(BaseModel):
    status: str


@router.get("")
def get_all_incidents():
    return list_incidents()


@router.get("/{incident_id}")
def get_incident(incident_id: int):
    incident = get_incident_by_id(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("")
def create_new_incident(payload: IncidentCreate):
    incident_id = create_incident(
        title=payload.title,
        description=payload.description,
        severity=payload.severity,
        status=payload.status,
    )
    return {
        "id": incident_id,
        "message": "Incident created successfully",
    }


@router.post("/{incident_id}/status")
def update_incident_status(incident_id: int, payload: IncidentStatusUpdate):
    updated = update_incident(incident_id, new_status=payload.status)
    if updated is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return updated