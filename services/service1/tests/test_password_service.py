from password.service import score_password


def test_short_password_is_weak():
    result = score_password("abc123")

    assert result["score"] < 40
    assert result["strength"] == "Weak"


def test_long_mixed_character_password_is_strong():
    result = score_password("LongPassword123!")

    assert result["score"] >= 70
    assert result["strength"] in {"Strong", "Very Strong"}


def test_password_in_weak_passwords_is_forced_low_score():
    result = score_password("password")

    assert result["score"] < 40
    assert result["strength"] == "Weak"
