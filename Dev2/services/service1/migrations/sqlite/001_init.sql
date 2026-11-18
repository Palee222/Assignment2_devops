CREATE TABLE IF NOT EXISTS weak_passwords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    password VARCHAR(255) NOT NULL,
    source VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS password_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    min_length INTEGER,
    require_upper BOOLEAN,
    require_lower BOOLEAN,
    require_digit BOOLEAN,
    require_symbol BOOLEAN
);
