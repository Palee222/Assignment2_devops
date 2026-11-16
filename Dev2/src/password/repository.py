from sqlalchemy import insert, select
from sqlalchemy.exc import SQLAlchemyError

from db import db


def get_weak_passwords():
    with db.get_connection() as conn:
        rows = conn.execute(select(db.weak_passwords.c.password))
        return [row.password for row in rows]


def seed_weak_passwords():
    weak_passwords = [
        "123456", "password", "123456789", "12345678", "12345",
        "111111", "1234567", "sunshine", "qwerty", "iloveyou",
        "princess", "admin", "welcome", "666666", "abc123",
        "football", "123123", "monkey", "654321", "!@#$%^&*",
        "charlie", "aa123456", "donald", "password1", "qwerty123"
    ]
    try:
        with db.get_connection() as conn, conn.begin():
            existing_password = conn.execute(
                select(db.weak_passwords.c.id).limit(1)
            ).first()
            if existing_password is not None:
                return "Weak passwords already seeded."

            conn.execute(
                insert(db.weak_passwords),
                [{"password": password} for password in weak_passwords],
            )
        return f"Inserted {len(weak_passwords)} weak passwords."
    except SQLAlchemyError as error:
        raise RuntimeError(f"Could not seed weak passwords: {error}") from error


def get_password_rules():
    return {
        "name": "Default password policy",
        "description": "Default rules for checking password strength.",
        "min_length": 8,
        "require_upper": True,
        "require_lower": True,
        "require_digit": True,
        "require_symbol": True,
    }


def seed_default_rules():
    rules = get_password_rules()
    rule_id = db.insert("password_rules", rules)
    return f"Default password rules inserted successfully (id={rule_id})."


seed_deafult_rules = seed_default_rules
