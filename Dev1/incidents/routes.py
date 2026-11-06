"""routes.py for the incidents endpoint logic.

Routes describe the request shape, call the service layer, and turn service
errors into HTTP status codes. They don't talk to the repository directly.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from incidents import service
from incidents.service import NotFoundError, Severity, Status, ValidationError

router = APIRouter(prefix="/incidents", tags=["incidents"])


class IncidentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    severity: Severity
    status: Status = "Open"
    tags: list[str] = []


class IncidentStatusUpdate(BaseModel):
    status: Status


@router.get("")
def get_all_incidents():
    return service.list_incidents()


@router.get("/{incident_id}")
def get_incident(incident_id: int):
    try:
        return service.get_incident(incident_id)
    except NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("", status_code=201)
def create_new_incident(payload: IncidentCreate):
    try:
        return service.create_incident(
            title=payload.title,
            description=payload.description,
            severity=payload.severity,
            status=payload.status,
            tags=payload.tags,
        )
    except ValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/{incident_id}/status")
def update_incident_status(incident_id: int, payload: IncidentStatusUpdate):
    try:
        return service.update_status(incident_id, payload.status)
    except NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
