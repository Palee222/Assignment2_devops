from pathlib import Path

from fastapi import APIRouter, Form, Request, Response
from pydantic import BaseModel, Field
from fastapi.templating import Jinja2Templates

from password.repository import get_password_rules
from password.service import score_password


router = APIRouter(prefix="/password", tags=["password"])
templates = Jinja2Templates(
	directory=str(Path(__file__).resolve().parents[1] / "templates")
)


class PasswordCheckRequest(BaseModel):
    password: str = Field(min_length=1)


@router.get("/api/health")
def password_api_health():
    return {"status": "ok"}


@router.post("/api/check")
def check_password_api(payload: PasswordCheckRequest, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return score_password(payload.password)


@router.get("/check")
def password_check_form(request: Request):
	return templates.TemplateResponse(
		request=request,
		name="password/check.html",
		context={"result": None},
	)


@router.post("/check")
def check_password(request: Request, password: str = Form(...)):
	result = score_password(password)

	return templates.TemplateResponse(
		request=request,
		name="password/check.html",
		context={"result": result},
	)


@router.get("/rules")
def password_rules(request: Request):
	return templates.TemplateResponse(
		request=request,
		name="password/rules.html",
		context={"rules": get_password_rules()},
	)
