import sqlite3

from DevOPS import db


def get_weak_passwords():
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT password FROM weak_passwords")
    passwords = [row[0] for row in cur.fetchall()]
    conn.close()
    return passwords

def seed_weak_passwords():
    weak_passwords = [
        "123456", "password", "123456789", "12345678", "12345",
        "111111", "1234567", "sunshine", "qwerty", "iloveyou",
        "princess", "admin", "welcome", "666666", "abc123",
        "football", "123123", "monkey", "654321", "!@#$%^&*",
        "charlie", "aa123456", "donald", "password1", "qwerty123"
    ]
    conn = db.get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM weak_passwords LIMIT 1")
        if cur.fetchone() is not None:
            return "Weak passwords already seeded."

        cur.executemany(
            "INSERT INTO weak_passwords (password) VALUES (?)",
            [(password,) for password in weak_passwords],
        )
        conn.commit()
        return f"Inserted {len(weak_passwords)} weak passwords."
    except sqlite3.Error as error:
        conn.rollback()
        raise RuntimeError(f"Could not seed weak passwords: {error}") from error
    finally:
        conn.close()

def get_password_rules():
    rules = {
        "name": "Default password policy",
        "description": "Default rules for checking password strength.",
        "min_length": 8,
        "require_upper": True,
        "require_lower": True,
        "require_digit": True,
        "require_symbol": True,
    }
    return rules

def seed_default_rules():
    rules = get_password_rules()
    rule_id = db.insert("password_rules", rules)
    return f"Default password rules inserted successfully (id={rule_id})."


seed_deafult_rules = seed_default_rules