from fastapi import APIRouter, Response
from pydantic import BaseModel, Field

from .service import report_weak_password, score_password

router = APIRouter(prefix="/password", tags=["password"])


class PasswordCheckRequest(BaseModel):
    password: str = Field(min_length=1)
    report_as_incident: bool = False


@router.get("/api/health", tags=["health"])
def password_api_health():
    return {"status": "ok"}


@router.post("/api/check")
def check_password_api(payload: PasswordCheckRequest, response: Response):
    response.headers["Cache-Control"] = "no-store"
    result = score_password(payload.password)
    if not payload.report_as_incident:
        result["incident_report"] = {"status": "not_requested", "incident_id": None}
    elif result["strength"] != "Weak":
        result["incident_report"] = {"status": "not_needed", "incident_id": None}
    else:
        result["incident_report"] = report_weak_password(
            result["score"], result["strength"]
        )
    return result
