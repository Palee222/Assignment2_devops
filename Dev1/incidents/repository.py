"""repository.py for incidents: all SQL, and nothing else.

Rows are converted to plain dicts before leaving this module, because
sqlite3.Row is not JSON-serialisable and FastAPI would fail to encode it.
A connection is opened per call rather than once at import time, because a
single sqlite3 connection cannot be reused across threads, and FastAPI runs
sync endpoints on a threadpool.
"""

from db import get_connection

INCIDENT_COLUMNS = "id, title, description, severity, status, created_at, updated_at"


def _row_to_dict(row):
    return dict(row) if row is not None else None


def create_incident(title, description, severity, status):
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO incidents (title, description, severity, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            (title, description, severity, status),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def list_incidents():
    conn = get_connection()
    try:
        rows = conn.execute(f"SELECT {INCIDENT_COLUMNS} FROM incidents ORDER BY id").fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_incident_by_id(incident_id):
    conn = get_connection()
    try:
        row = conn.execute(
            f"SELECT {INCIDENT_COLUMNS} FROM incidents WHERE id = ?", (incident_id,)
        ).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def update_incident(incident_id, title=None, description=None, severity=None, new_status=None):
    """Read-modify-write. Any argument left as None keeps its current value."""
    incident = get_incident_by_id(incident_id)
    if incident is None:
        return None

    # Look fields up by name, not by tuple index: index positions silently
    # break the moment a column is added to the table.
    updated_title = title if title is not None else incident["title"]
    updated_description = description if description is not None else incident["description"]
    updated_severity = severity if severity is not None else incident["severity"]
    updated_status = new_status if new_status is not None else incident["status"]

    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE incidents
            SET title = ?, description = ?, severity = ?, status = ?, updated_at = datetime('now')
            WHERE id = ?
            """,
            (updated_title, updated_description, updated_severity, updated_status, incident_id),
        )
        conn.commit()
    finally:
        conn.close()

    return get_incident_by_id(incident_id)


def add_tags_to_incident(incident_id, tags):
    """Attach tag names to an incident, creating any tag that does not exist yet.

    incident_tags stores a tag_id, not the tag text (the previous version wrote
    into a `tag` column that the schema doesn't have), so each name is resolved
    to a row in `tags` first.
    """
    attached = []
    conn = get_connection()
    try:
        for tag in tags:
            name = tag.strip()
            if not name:
                continue

            conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (name,))
            row = conn.execute("SELECT id FROM tags WHERE name = ?", (name,)).fetchone()

            conn.execute(
                "INSERT OR IGNORE INTO incident_tags (incident_id, tag_id) VALUES (?, ?)",
                (incident_id, row["id"]),
            )
            attached.append(name)
        conn.commit()
    finally:
        conn.close()

    return attached


def get_tags_for_incident(incident_id):
    """service.py calls this on every get_incident(), but it never existed."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT tags.name
            FROM tags
            JOIN incident_tags ON incident_tags.tag_id = tags.id
            WHERE incident_tags.incident_id = ?
            ORDER BY tags.name
            """,
            (incident_id,),
        ).fetchall()
        return [row["name"] for row in rows]
    finally:
        conn.close()
