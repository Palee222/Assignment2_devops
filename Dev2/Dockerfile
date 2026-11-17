FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src:/app/services:/app

WORKDIR /app

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates curl gnupg unixodbc-dev; \
    install -d /usr/share/keyrings; \
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
        | gpg --dearmor --yes -o /usr/share/keyrings/microsoft-prod.gpg; \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" \
        > /etc/apt/sources.list.d/mssql-release.list; \
    apt-get update; \
    ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18; \
    rm -rf /var/lib/apt/lists/*

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup --uid 10001 appuser

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY app.py ./app.py
COPY db/db.py ./db/db.py
COPY db/migrations.py ./db/migrations.py
COPY src/ ./src/
COPY scripts/migrate_sqlite_to_sqlserver.py ./scripts/migrate_sqlite_to_sqlserver.py
COPY services/service1/app.py ./services/service1/app.py
COPY services/service1/routes.py ./services/service1/routes.py
COPY services/service2/app.py ./services/service2/app.py
COPY services/service2/routes.py ./services/service2/routes.py

USER appuser

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]