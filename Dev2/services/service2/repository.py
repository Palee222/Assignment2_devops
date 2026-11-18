from datetime import datetime, timezone

from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError

from .database import engine, incident_tags, incidents, tags


def create_incident(title: str, description: str, severity: str, status: str) -> int:
    now = datetime.now(timezone.utc)
    with engine.begin() as connection:
        result = connection.execute(
            insert(incidents).values(
                title=title,
                description=description,
                severity=severity,
                status=status,
                created_at=now,
                updated_at=now,
            )
        )
        incident_id = result.inserted_primary_key[0]
        if incident_id is None:
            raise RuntimeError("The incident record was not inserted.")
        return incident_id


def list_incidents() -> list[dict]:
    with engine.connect() as connection:
        rows = connection.execute(select(incidents).order_by(incidents.c.id))
        return [dict(row) for row in rows.mappings()]


def get_incident_by_id(incident_id: int) -> dict | None:
    with engine.connect() as connection:
        row = connection.execute(
            select(incidents).where(incidents.c.id == incident_id)
        ).mappings().first()
        return dict(row) if row is not None else None


def update_incident_status(incident_id: int, new_status: str) -> dict | None:
    if get_incident_by_id(incident_id) is None:
        return None
    with engine.begin() as connection:
        connection.execute(
            update(incidents)
            .where(incidents.c.id == incident_id)
            .values(status=new_status, updated_at=datetime.now(timezone.utc))
        )
    return get_incident_by_id(incident_id)


def add_tags_to_incident(incident_id: int, tag_names: list[str]) -> list[str]:
    attached = []
    with engine.begin() as connection:
        for tag_name in tag_names:
            name = tag_name.strip()
            if not name:
                continue
            tag_id = connection.execute(
                select(tags.c.id).where(tags.c.name == name)
            ).scalar_one_or_none()
            if tag_id is None:
                try:
                    with connection.begin_nested():
                        result = connection.execute(insert(tags).values(name=name))
                        tag_id = result.inserted_primary_key[0]
                except IntegrityError:
                    tag_id = connection.execute(
                        select(tags.c.id).where(tags.c.name == name)
                    ).scalar_one()
            link_exists = connection.execute(
                select(incident_tags.c.incident_id).where(
                    incident_tags.c.incident_id == incident_id,
                    incident_tags.c.tag_id == tag_id,
                )
            ).first()
            if link_exists is None:
                connection.execute(
                    insert(incident_tags).values(
                        incident_id=incident_id, tag_id=tag_id
                    )
                )
            attached.append(name)
    return attached


def get_tags_for_incident(incident_id: int) -> list[str]:
    with engine.connect() as connection:
        rows = connection.execute(
            select(tags.c.name)
            .select_from(tags.join(incident_tags, incident_tags.c.tag_id == tags.c.id))
            .where(incident_tags.c.incident_id == incident_id)
            .order_by(tags.c.name)
        )
        return [row.name for row in rows]
