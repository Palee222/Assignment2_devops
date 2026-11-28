# Assignment 2 DevOps

Security Incident Notebook and Password Hygiene Checker.

## Live deployment

| Component | Live URL |
|---|---|
| Web UI | https://lsomogyiieu2024ui.z43.web.core.windows.net/ |
| Password API | https://lsomogyi-ieu2024-password.yellowwater-b5191301.spaincentral.azurecontainerapps.io |
| Incidents API | https://lsomogyi-ieu2024-incidents.yellowwater-b5191301.spaincentral.azurecontainerapps.io |

The UI is hosted in Azure Storage static website hosting. The password and
incidents APIs are separate Azure Container Apps in Spain Central.

## Architecture

```text
Browser UI
  |-- VITE_PASSWORD_API_URL ---> Password FastAPI service
  |-- VITE_INCIDENTS_API_URL --> Incidents FastAPI service

Password service  <---- separate database ---> Password SQL Server database
Incidents service <---- separate database ---> Incidents SQL Server database
```

- `Dev2/ui`: Vite/React/TypeScript frontend.
- `Dev2/services/service1`: password scoring and weak-password service.
- `Dev2/services/service2`: incident and tag CRUD service.
- `Dev2/src`: shared combined-development application.
- `Dev2/services/*/migrations`: ordered service-owned database migrations.
- `Dev2/system.yaml`: system and service contract.
- `Dev2/ADR.md`: architecture decisions.

The password service calls the incidents service only when the UI explicitly
requests an incident for a weak result. Password values are not persisted.

## Local setup

Requirements:

- Python 3.12+
- Bun or Node.js/npm
- Docker and Docker Compose for the container/SQL Server setup

Backend and combined development app:

```sh
cd Dev2
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt

CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173 \
DATA_DIR=data \
PYTHONPATH=src \
python -u app.py
```

The combined app runs on port 8000 and uses SQLite.

Frontend:

```sh
cd Dev2/ui
npm install
cp .env.example .env.local
npm run dev
```

For combined-app development, set both API values in `ui/.env.local`:

```dotenv
VITE_PASSWORD_API_URL=http://127.0.0.1:8000
VITE_INCIDENTS_API_URL=http://127.0.0.1:8000
```

For standalone Compose services:

```sh
cd Dev2
cp .env.example .env
# Replace database passwords in .env with strong URL-safe values.
docker compose up --build
```

Compose exposes the password service on port 8001, the incidents service on
8002, and SQL Server on `127.0.0.1:1433`.

## Environment configuration

### Backend

| Variable | Required | Purpose |
|---|---:|---|
| `DATABASE_URL` | Yes | SQLAlchemy connection string for the service database |
| `PORT` | No | Listen port; defaults to `8000` |
| `GIT_SHA` | No | Release identifier returned by `/health`; defaults to `unknown` |
| `CORS_ALLOWED_ORIGINS` | Production: yes | Exact comma-separated HTTPS UI origins |
| `INCIDENTS_SERVICE_URL` | Password service | Base URL of the incidents service |
| `INCIDENTS_TIMEOUT_S` | No | Incident reporting timeout; defaults to `2` seconds |
| `DATA_DIR` | No | SQLite data directory for combined local development |

`DATABASE_URL` values are secrets and must not be committed. CORS origins must
contain scheme, hostname, and optional port, but no paths or wildcards.

### Frontend

| Variable | Purpose |
|---|---|
| `VITE_PASSWORD_API_URL` | Public base URL for the password service |
| `VITE_INCIDENTS_API_URL` | Public base URL for the incidents service |

These variables contain public URLs only, never credentials or secrets.

## Tests

Run the service-specific backend coverage checks:

```sh
cd Dev2
PYTHONPATH=.:src python -m pytest services/service1/tests \
  --cov=services.service1 --cov-fail-under=70 --cov-report=term-missing

PYTHONPATH=.:src python -m pytest services/service2/tests tests/test_cross_service.py \
  --cov=services.service2 --cov-fail-under=70 --cov-report=term-missing
```

Validate system configuration and OpenAPI documents:

```sh
cd Dev2
python -m pytest tests/test_system_contract.py tests/test_migrations.py -q
npx @redocly/cli lint \
  services/service1/openapi.yaml \
  services/service2/openapi.yaml
```

Lint and build the UI:

```sh
cd Dev2/ui
bun install --frozen-lockfile
bunx eslint src/lib/security.ts src/lib/use-password-checker.ts src/routes/password.tsx
bun run build
```

GitHub Actions runs these checks in CI before container images are published.
The workflow configuration is in `.github/workflows/ci.yml`.

## Database and migrations

The combined development app uses SQLite at `Dev2/data/secnote.db`.
Standalone services use separate SQL Server databases:

- Password service database
- Incidents service database

Each service owns an immutable, ordered migration history and records applied
versions in `schema_migrations`. Startup applies pending migrations and then
verifies checksums on later starts. Production recovery follows
[ADR-7](Dev2/ADR.md).

A migration dry run for existing SQLite data is:

```sh
cd Dev2
PYTHONPATH=src python scripts/migrate_sqlite_to_sqlserver.py \
  --source data/secnote.db --service password
```

Use `--service incidents` for incident and tag records. Applying the migration
requires the SQL Server target URL in `MIGRATION_DATABASE_URL` and a one-off
migration runner.

## Deployment

Deployment is performed through GitHub Actions and Azure:

1. CI validates configuration, OpenAPI, tests, coverage, frontend lint, and builds.
2. The CD workflow pushes commit-specific container images to GHCR.
3. Azure Container Apps are updated with the password and incidents images.
4. The UI is built with the deployed API URLs.
5. The UI build is uploaded to Azure Storage static website hosting.
6. Post-deployment checks call `GET /health` on both services.

Configure these GitHub Actions variables:

- `PREFIX`
- `RESOURCE_GROUP`
- `UI_STORAGE`
- `PASSWORD_SERVICE_URL`
- `INCIDENTS_SERVICE_URL`

Configure the Azure deployment credentials as GitHub Actions secrets:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`

The reusable health workflow is `.github/workflows/post-deployment-health-check.yml`.
It retries each `/health` endpoint until the timeout expires and fails the
deployment if either service does not return HTTP 200.

Deployment workflow configuration is in `.github/workflows/cd.yml`.
