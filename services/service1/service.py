#routes.py for endpoint logic


strength_levels = ["Weak", "Moderate", "Strong", "Very Strong"]

def score_password(password: str) -> dict:
    """
    Score the strength of a password on a 0-100 scale.
    strength is determined by length, character variety, and complexity.
    Args:
        password (str): The password to be scored.

    Returns:
        dict: A dictionary containing the password score, strength level, and feedback.
    """
    score = 0
    feedback = []
    special_characters = "!@#$%^&*()-_=+[]{}|;:'\",.<>?/`~"

    # Length scoring: 0 to 30
    if len(password) < 8:
        feedback.append("Password is too short. Minimum length is 8 characters.")
    elif len(password) < 12:
        score += 20
        feedback.append("Password length is acceptable but could be longer.")
    else:
        score += 30

    # Uppercase: 0 to 15
    if any(char.isupper() for char in password):
        score += 15
    else:
        feedback.append("Password should include at least one uppercase letter.")

    # Lowercase: 0 to 15
    if any(char.islower() for char in password):
        score += 15
    else:
        feedback.append("Password should include at least one lowercase letter.")

    # Digits: 0 to 15
    if any(char.isdigit() for char in password):
        score += 15
    else:
        feedback.append("Password should include at least one digit.")

    # Special characters: 0 to 15
    if any(char in special_characters for char in password):
        score += 15
    else:
        feedback.append("Password should include at least one special character.")

    # Bonus for longer passwords: 0 to 10
    if len(password) >= 16:
        score += 10

    # Cap the score at 100
    score = min(score, 100)

    # Map score to strength level
    if score < 40:
        level = "Weak"
    elif score < 70:
        level = "Moderate"
    elif score < 90:
        level = "Strong"
    else:
        level = "Very Strong"

    return {
        "score": score,
        "strength": level,
        "feedback": feedback
    }