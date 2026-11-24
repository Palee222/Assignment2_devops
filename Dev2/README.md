# Assignment2_devops

      pip install pre-commit

Starting up the things:
- Backend:
   - python3 -m venv .venv
   - source .venv/bin/activate
   - python -m pip install -r requirements.txt
   - CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173 PYTHONPATH=src python -u app.py
- Frontend
   - cd ui
   - npm install
   - cp .env.example .env.local
   - npm run dev

The UI connects to the incident API (`GET/POST /incidents` and
`POST /incidents/{id}/status`) and the password API (`POST
/password/api/check`, JSON body `{"password":"..."}`). The UI's API base URLs
are configured per environment with `VITE_INCIDENTS_API_URL` and
`VITE_PASSWORD_API_URL` in `ui/.env.local` for development or the frontend
deployment's build environment for production. The sample `.env.example`
points at the standalone Compose services on ports 8001 and 8002. When using
the combined development app on port 8000, set both values to
`http://127.0.0.1:8000`. These `VITE_` values are
public and must contain URLs only, never secrets. When set, they take priority
over URLs saved in browser settings.

Set `CORS_ALLOWED_ORIGINS` in the backend environment to a comma-separated
list of exact UI origins (scheme, hostname, and optional port; no paths or
wildcards). Compose allows the usual local Vite origins on port 5173 and the
project's sandbox dev-server origins on port 8080. For production, configure
only the deployed UI origin, for example
`CORS_ALLOWED_ORIGINS=https://your-ui.example.com`, and use HTTPS. The same
allowlist protects both APIs served by the combined FastAPI app.

The password page sends a password only when **Check password** is pressed;
it is not stored in browser storage. The optional **Create an incident if the
result is weak** setting sends only the score and strength from the Password
service to the Incidents service. If Incidents is unavailable, the password
score is still returned and the UI reports that the incident was not created.

## Database

The combined development app uses SQLite by default and creates
`data/secnote.db`. Set `DATA_DIR` to change the local database directory.
The Compose setup runs the password and incidents services separately, each
with its own `DATABASE_URL` and database. Each image is built from its own
context (`services/service1` or `services/service2`) and has its own Dockerfile,
routes, repository, business logic, database migrations, and OpenAPI document.
`system.yaml` describes these services and is validated by `system.schema.json`.

For local services, copy `.env.example` to `.env`, replace all three values
with different strong passwords, then run:

```sh
docker compose up --build
```

The password service is available on port 8001 and the incidents service on
port 8002. SQL Server listens on port 1433. `db/init.sql` creates both databases and separate logins; each login is mapped
and granted permissions only in its own database. The login has `db_ddladmin`
in that database so the service can apply schema migrations at startup. The
`db-init` container runs the idempotent database/login setup after SQL Server
is healthy.

The service passwords must contain only URL-safe letters, digits, hyphens, or
underscores; include uppercase, lowercase, and digits to satisfy SQL Server's
password policy. Keep `.env` private and never commit real passwords.
Each service image installs `unixODBC` and Microsoft's ODBC Driver 18. SQL Server's
official Linux container is x86-64 only; this Compose file requests
`linux/amd64`, but emulation on Apple Silicon is not an officially supported
SQL Server configuration.

Each standalone service applies its own ordered migrations at startup and
records them in `schema_migrations`. Their SQL Server and SQLite scripts live
under `services/service1/migrations/` and `services/service2/migrations/`.
Each newly applied migration is logged; later starts verify its checksum and
skip it. Applied migration files are immutable: make a new numbered migration
for every schema change. The combined development app still
uses the corresponding scripts under `src/password/migrations/` and
`src/incidents/migrations/`.
The password service's second migration adds `is_active` to
`weak_passwords` with a default, preserving existing rows. The password
service owns and seeds the weak-password list; the incidents service owns
incidents and tags. Both services expose `GET /health`; it performs a
transactional database write/read/delete probe and reports HTTP 503 if that
probe fails. The response includes `status`, `database`, and `git_sha`. Set
`GIT_SHA` during image builds/deployments for a release identifier; otherwise
the response reports `unknown`. Each service logs one JSON request record to
stdout with method, path, status, and elapsed time.

The password service's outbound incident request has a two-second timeout
(`INCIDENTS_TIMEOUT_S`). Browser-to-service API calls have an eight-second
timeout. Configure `CORS_ALLOWED_ORIGINS` to the exact UI origin(s) when
running the services outside Compose.

Run the backend tests and coverage report with:

```sh
PYTHONPATH=.:src python -m pytest services/service1/tests \
  --cov=services.service1 --cov-fail-under=70 --cov-report=term-missing
PYTHONPATH=.:src python -m pytest services/service2/tests tests/test_cross_service.py \
  --cov=services.service2 --cov-fail-under=70 --cov-report=term-missing
```

The coverage checks are measured and enforced separately for each service.
Compose tests target the local SQL Server container on `127.0.0.1:1433`;
they must not be pointed at Azure SQL.

GitHub Actions runs backend tests with coverage, lints the modified UI API
files, and builds the UI. The OpenAPI specifications are at
`services/service1/openapi.yaml` and `services/service2/openapi.yaml`.
Validate both documents from the repository root with:

```sh
npx @redocly/cli lint services/service1/openapi.yaml services/service2/openapi.yaml
```

The repository does not provision Azure resources. Set up an Azure deployment
environment and credentials before configuring `system.yaml` with actual
resource names or enabling cloud deployment.

The reusable post-deployment health-check workflow waits for both services'
`/health` endpoints to return HTTP 200. Call it from a deployment workflow after
the deploy job succeeds:

```yaml
jobs:
  post-deployment-health-check:
    needs: deploy
    uses: ./.github/workflows/post-deployment-health-check.yml
    with:
      password_service_url: ${{ vars.PASSWORD_SERVICE_URL }}
      incidents_service_url: ${{ vars.INCIDENTS_SERVICE_URL }}
      timeout_seconds: 300
      retry_interval_seconds: 10
```

Configure the two base URLs as GitHub Actions variables. The check job fails
if either endpoint does not return HTTP 200 before its timeout.

For a failed production migration, follow ADR-7 in [ADR.md](./ADR.md): stop
the rollout, retain the database and migration ledger, restore a verified
pre-migration backup only if data integrity is at risk, and otherwise ship a
new forward migration to correct the issue. Never drop or recreate a database
or table as a deployment recovery step.

To inspect or migrate the selected SQLite data into the corresponding SQL
Server database, specify the service. Run the dry run first:

```sh
PYTHONPATH=src python scripts/migrate_sqlite_to_sqlserver.py --source data/secnote.db --service password
```

To apply it, start only SQL Server and its initializer, wait for initialization,
then run the one-off migration image against the selected service database.
Set `MIGRATION_DATABASE_URL` to the target database URL in your shell:

```sh
docker compose up -d sqlserver db-init
docker compose wait db-init
MIGRATION_DATABASE_URL='mssql+pyodbc://password_service_login:...@sqlserver:1433/PasswordServiceDb?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=yes' \
docker compose run --build --rm --no-deps migration-runner \
  python \
  /app/scripts/migrate_sqlite_to_sqlserver.py \
  --source /migration-data/secnote.db --service password --apply
docker compose up --build password-service incidents-service
```

The target database must be empty. The migration preserves IDs, checks schemas, and verifies row counts in one transaction. Use `--service incidents` for incident and tag records from the same SQLite file. The migration runner is a one-off tool built from the repository root; the deployed service images remain independent.
