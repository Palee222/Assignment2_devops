from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from . import service

router = APIRouter(prefix="/incidents", tags=["incidents"])


class IncidentCreate(BaseModel):
    title: str = Field(max_length=500)
    description: str
    severity: str
    status: str = "Open"
    tags: list[str] = Field(default_factory=list)


class IncidentStatusUpdate(BaseModel):
    status: str


@router.get("")
def get_all_incidents():
    return service.list_incidents()


@router.get("/{incident_id}")
def get_incident(incident_id: int):
    try:
        return service.get_incident(incident_id)
    except service.NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("")
def create_new_incident(payload: IncidentCreate):
    try:
        return service.create_incident(
            title=payload.title,
            description=payload.description,
            severity=payload.severity,
            status=payload.status,
            tags=payload.tags,
        )
    except service.ValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/{incident_id}/status")
def update_incident_status(incident_id: int, payload: IncidentStatusUpdate):
    try:
        return service.update_status(incident_id, payload.status)
    except service.ValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except service.NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
