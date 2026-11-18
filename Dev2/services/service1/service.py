import json
import logging
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .repository import get_weak_passwords

logger = logging.getLogger("password-service")

STRENGTH_LEVELS = ["Weak", "Moderate", "Strong", "Very Strong"]
SPECIAL_CHARACTERS = "!@#$%^&*()-_=+[]{}|;:'\",.<>?/`~"


def score_password(password: str) -> dict:
    score = 0
    feedback = []
    if len(password) < 8:
        feedback.append("Password is too short. Minimum length is 8 characters.")
    elif len(password) < 12:
        score += 20
        feedback.append("Password length is acceptable but could be longer.")
    else:
        score += 30

    if any(char.isupper() for char in password):
        score += 15
    else:
        feedback.append("Password should include at least one uppercase letter.")
    if any(char.islower() for char in password):
        score += 15
    else:
        feedback.append("Password should include at least one lowercase letter.")
    if any(char.isdigit() for char in password):
        score += 15
    else:
        feedback.append("Password should include at least one digit.")
    if any(char in SPECIAL_CHARACTERS for char in password):
        score += 15
    else:
        feedback.append("Password should include at least one special character.")
    if len(password) >= 16:
        score += 10

    if password.casefold() in {item.casefold() for item in get_weak_passwords()}:
        score = min(score, 30)
        feedback.append("This password appears in the weak-password list.")

    score = min(score, 100)
    if score < 40:
        strength = "Weak"
    elif score < 70:
        strength = "Moderate"
    elif score < 90:
        strength = "Strong"
    else:
        strength = "Very Strong"
    return {"score": score, "strength": strength, "feedback": feedback}


def report_weak_password(score: int, strength: str) -> dict:
    base_url = os.getenv("INCIDENTS_SERVICE_URL", "http://incidents-service:8000")
    timeout_s = float(os.getenv("INCIDENTS_TIMEOUT_S", "2"))
    if timeout_s <= 0:
        raise ValueError("INCIDENTS_TIMEOUT_S must be greater than zero.")

    payload = {
        "title": "Weak password detected",
        "description": (
            "The password checker identified a weak password. "
            f"Score: {score}/100; strength: {strength}. "
            "The password value was not transmitted."
        ),
        "severity": "High",
        "status": "Open",
        "tags": ["Password security"],
    }
    request = Request(
        f"{base_url.rstrip('/')}/incidents",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_s) as response:
            result = json.loads(response.read())
        if not isinstance(result, dict):
            raise ValueError("Incidents service returned an invalid response.")
        incident_id = result.get("id")
        if not isinstance(incident_id, int):
            raise ValueError("Incidents service returned no incident id.")
        return {"status": "created", "incident_id": incident_id}
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError):
        logger.warning(
            "Weak-password incident reporting failed; password scoring remains available.",
            exc_info=True,
        )
        return {"status": "unavailable", "incident_id": None}
