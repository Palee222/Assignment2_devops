from db import get_connection
conn = get_connection()

def create_incident(title, description, severity, status):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO incidents (title, description, severity, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
    """, (title, description, severity, status))
    conn.commit()
    return cur.lastrowid

def list_incidents():
    cur = conn.cursor()
    cur.execute("SELECT * FROM incidents")
    return cur.fetchall()

def get_incident_by_id(incident_id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
    return cur.fetchone()

def update_incident(incident_id, title=None, description=None, severity=None, new_status=None):
    cur = conn.cursor()
    incident = get_incident_by_id(incident_id)
    if not incident:
        return None

    updated_title = title if title is not None else incident[1]
    updated_description = description if description is not None else incident[2]
    updated_severity = severity if severity is not None else incident[3]
    updated_status = new_status if new_status is not None else incident[4]

    cur.execute("""
        UPDATE incidents
        SET title = ?, description = ?, severity = ?, status = ?, updated_at = datetime('now')
        WHERE id = ?
    """, (updated_title, updated_description, updated_severity, updated_status, incident_id))
    conn.commit()
    return get_incident_by_id(incident_id)

def add_tags_to_incident(incident_id, tags):
    cur = conn.cursor()
    for tag in tags:
        cur.execute("""
            INSERT INTO incident_tags (incident_id, tag)
            VALUES (?, ?)
        """, (incident_id, tag))
    conn.commit()