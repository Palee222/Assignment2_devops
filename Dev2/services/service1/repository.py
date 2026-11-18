from sqlalchemy import insert, select
from sqlalchemy.exc import SQLAlchemyError

from .database import engine, password_rules, weak_passwords


def get_weak_passwords() -> list[str]:
    with engine.connect() as connection:
        rows = connection.execute(
            select(weak_passwords.c.password).where(weak_passwords.c.is_active.is_(True))
        )
        return [row.password for row in rows]


def seed_weak_passwords() -> None:
    passwords = [
        "123456", "password", "123456789", "12345678", "12345",
        "111111", "1234567", "sunshine", "qwerty", "iloveyou",
        "princess", "admin", "welcome", "666666", "abc123",
        "football", "123123", "monkey", "654321", "!@#$%^&*",
        "charlie", "aa123456", "donald", "password1", "qwerty123",
    ]
    try:
        with engine.begin() as connection:
            if connection.execute(select(weak_passwords.c.id).limit(1)).first():
                return
            connection.execute(
                insert(weak_passwords),
                [{"password": password} for password in passwords],
            )
    except SQLAlchemyError as error:
        raise RuntimeError(f"Could not seed weak passwords: {error}") from error


def get_password_rules() -> dict:
    return {
        "name": "Default password policy",
        "description": "Default rules for checking password strength.",
        "min_length": 8,
        "require_upper": True,
        "require_lower": True,
        "require_digit": True,
        "require_symbol": True,
    }


def seed_default_rules() -> None:
    with engine.begin() as connection:
        if connection.execute(select(password_rules.c.id).limit(1)).first():
            return
        connection.execute(insert(password_rules).values(**get_password_rules()))
