CREATE TABLE IF NOT EXISTS health_probes (
    probe_id VARCHAR(36) PRIMARY KEY,
    checked_at DATETIME NOT NULL
);
