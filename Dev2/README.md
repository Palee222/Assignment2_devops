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
points both variables at the local combined FastAPI app; replace them with
the appropriate service URLs for each environment. These `VITE_` values are
public and must contain URLs only, never secrets. When set, they take priority
over URLs saved in browser settings.

Set `CORS_ALLOWED_ORIGINS` in the backend environment to a comma-separated
list of exact UI origins (scheme, hostname, and optional port; no paths or
wildcards). The command above permits the two common local Vite origins. For
production, configure only the deployed UI origin, for example
`CORS_ALLOWED_ORIGINS=https://your-ui.example.com`, and use HTTPS. The same
allowlist protects both APIs served by the combined FastAPI app.

The password page sends a password only when **Check password** is pressed;
it is not stored in browser storage.

## Database

The combined development app uses SQLite by default and creates
`data/secnote.db`. Set `DATA_DIR` to change the local database directory.
The Compose setup runs the password and incidents services separately, each
with its own `DATABASE_URL` and database.

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
The app image installs `unixODBC` and Microsoft's ODBC Driver 18. SQL Server's
official Linux container is x86-64 only; this Compose file requests
`linux/amd64`, but emulation on Apple Silicon is not an officially supported
SQL Server configuration.

Each service applies its own ordered migrations at startup and records them in
`schema_migrations`. SQL Server and SQLite have dialect-specific scripts under
`src/password/migrations/` and `src/incidents/migrations/`. Applied migration
files are checksum-verified and immutable: make a new numbered migration for
every schema change.
The password service's second migration adds `is_active` to
`weak_passwords` with a default, preserving existing rows. The password
service owns and seeds the weak-password list; the incidents service owns
incidents and tags.

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

To apply it using the ODBC-enabled app image, start only SQL Server and its
initializer, wait for initialization, migrate before launching the password
service, then start both APIs:

```sh
docker compose up -d sqlserver db-init
docker compose wait db-init
docker compose run --build --rm --no-deps \
  -v ./data:/migration-data:ro \
  --entrypoint python password-service \
  /app/scripts/migrate_sqlite_to_sqlserver.py \
  --source /migration-data/secnote.db --service password --apply
docker compose up --build password-service incidents-service
```

The target database must be empty. The migration preserves IDs, checks
schemas, and verifies row counts in one transaction. Use `--service incidents`
for incident and tag records from the same SQLite file.
