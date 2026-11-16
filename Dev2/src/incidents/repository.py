"""Persistence operations for incidents and their tags."""

from datetime import datetime, timezone

from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError

from db.db import get_connection, incident_tags, incidents, tags


def _row_to_dict(row):
    return dict(row) if row is not None else None


def create_incident(title, description, severity, status):
    now = datetime.now(timezone.utc)
    with get_connection() as conn, conn.begin():
        result = conn.execute(
            insert(incidents).values(
                title=title,
                description=description,
                severity=severity,
                status=status,
                created_at=now,
                updated_at=now,
            )
        )
        return result.inserted_primary_key[0]


def list_incidents():
    with get_connection() as conn:
        rows = conn.execute(select(incidents).order_by(incidents.c.id))
        return [dict(row) for row in rows.mappings()]


def get_incident_by_id(incident_id):
    with get_connection() as conn:
        row = conn.execute(
            select(incidents).where(incidents.c.id == incident_id)
        ).mappings().first()
        return _row_to_dict(row)


def update_incident(
    incident_id, title=None, description=None, severity=None, new_status=None
):
    incident = get_incident_by_id(incident_id)
    if incident is None:
        return None

    updated_values = {
        "title": title if title is not None else incident["title"],
        "description": (
            description if description is not None else incident["description"]
        ),
        "severity": severity if severity is not None else incident["severity"],
        "status": new_status if new_status is not None else incident["status"],
        "updated_at": datetime.now(timezone.utc),
    }

    with get_connection() as conn, conn.begin():
        conn.execute(
            update(incidents)
            .where(incidents.c.id == incident_id)
            .values(**updated_values)
        )

    return get_incident_by_id(incident_id)


def add_tags_to_incident(incident_id, tag_names):
    attached = []
    with get_connection() as conn, conn.begin():
        for tag_name in tag_names:
            name = tag_name.strip()
            if not name:
                continue

            tag_id = conn.execute(
                select(tags.c.id).where(tags.c.name == name)
            ).scalar_one_or_none()
            if tag_id is None:
                try:
                    with conn.begin_nested():
                        result = conn.execute(insert(tags).values(name=name))
                        tag_id = result.inserted_primary_key[0]
                except IntegrityError:
                    tag_id = conn.execute(
                        select(tags.c.id).where(tags.c.name == name)
                    ).scalar_one()

            existing_link = conn.execute(
                select(incident_tags.c.incident_id).where(
                    incident_tags.c.incident_id == incident_id,
                    incident_tags.c.tag_id == tag_id,
                )
            ).first()
            if existing_link is None:
                conn.execute(
                    insert(incident_tags).values(
                        incident_id=incident_id,
                        tag_id=tag_id,
                    )
                )
            attached.append(name)

    return attached


def get_tags_for_incident(incident_id):
    with get_connection() as conn:
        rows = conn.execute(
            select(tags.c.name)
            .select_from(
                tags.join(
                    incident_tags,
                    incident_tags.c.tag_id == tags.c.id,
                )
            )
            .where(incident_tags.c.incident_id == incident_id)
            .order_by(tags.c.name)
        )
        return [row.name for row in rows]
