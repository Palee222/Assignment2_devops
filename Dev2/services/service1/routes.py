from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.templating import Jinja2Templates

from password.repository import get_password_rules
from password.service import score_password


router = APIRouter(prefix="/password", tags=["password"])
templates = Jinja2Templates(
	directory=str(Path(__file__).resolve().parents[1] / "src" / "templates")
)


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
