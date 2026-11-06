# Assignment2_devops

# Step-by-step guide for Assignment 2

You have until Nov 22, about 16 days. The commit-cadence rule (12+ commits, 6+ distinct days, no day over 40%) means you can't do this in a weekend. Work in short branches and merge via pull requests from day one.

## Phase 0: Prepare (Day 1)

2. **Get the professor's items**: `system.schema.json` and the class service principal credentials. Store the credentials only as GitHub secrets, never in a file.
3. **Plan the time**: set a rough plan like the one at the bottom, and commit something small every working session.
4. **Repo hygiene**: in the same Assignment 1 repo, enable GitHub secret scanning and push protection. Add a `.gitignore` covering `.env`, and branch protection on `main` (require PR plus passing CI). A leaked secret is an incident, so prevent it.

## Phase 1: Restructure and split the code (Days 1-3)

5. Create the layout:
   ```
   services/<a>/   (app code, tests, Dockerfile, migrations/, requirements/package.json)
   services/<b>/
   ui/
   db/init.sql
   docker-compose.yml
   system.yaml, system.schema.json
   .github/workflows/
   ```
6. **Assign tables to services.** Each table belongs to exactly one service. Turn cross-seam foreign keys into plain IDs, and note what integrity you lose (needed for ADR-7).
7. **Port to SQL Server** (`INT IDENTITY`, `NVARCHAR`, `OFFSET…FETCH`). Use `pymssql` or `tedious`/`mssql`, or your ORM's provider.
8. **Add the required service behaviour** to each service:
   - Config via env: `PORT`, `DATABASE_URL`, `<OTHER>_URL`, `<OTHER>_TIMEOUT_S`, and the UI origin for CORS.
   - CORS limited to the UI's origin.
   - The cross-seam call over HTTP with a timeout and a designed failure behaviour (degrade, retry, etc.). At least one flow must cross the seam server side.
   - `GET /health` returning 200 `{"status","db","version"}` only if it can read and write its own DB, else 503. It must not depend on the other service.
   - One stdout log line per request (method, path, status, duration).
   - Idempotent seed data per service.
9. **Convert the UI to static files** in `ui/` that fetch JSON from the services. Load the base URLs from a `config.js`, not hardcoded.

## Phase 2: Migrations (Days 3-4)

10. Write a runner, or pick a tool (Alembic, Knex, Prisma). It must apply numbered files in order at startup, record them in `schema_migrations`, and apply nothing on a second boot.
11. Write `001_init.sql` per service.
12. **Write `002_*.sql` but do NOT merge it to main yet.** It must change a table that already holds data (add a column with default/backfill, etc.). Keep it on a branch until you've seeded data on Azure (Phase 7).
13. Add **connect retries with backoff** (Azure SQL error 40613 while resuming from pause) around DB connection and migration start.

## Phase 3: Containers and compose (Days 4-6)

14. Write one **Dockerfile per service**: pinned dependencies, non-root user, no `COPY . .` (copy specific paths), no secrets or `.env`.
15. Write `docker-compose.yml` with:
    - `mssql` (`mcr.microsoft.com/mssql/server:2022-latest`) with a healthcheck
    - a one-off `db-init` service running `db/init.sql` (idempotent: creates both DBs and logins, each login limited to its own DB)
    - the two services, wired via env vars (e.g. `CATALOG_URL=http://catalog:8000`)
    - `nginx:alpine` serving `ui/` (volume mount, no Dockerfile)
16. Test from a **clean clone**: `docker compose up --build`. Then test `docker compose stop <service>` and confirm the other keeps working and the cross-seam flow fails gracefully.

## Phase 4: Tests and docs-as-code (Days 5-7)

17. Add unit tests per service and measure coverage (≥70% on core logic for each).
18. Add **one cross-seam integration test**, against the compose stack or with the other service stubbed. Justify the choice in ADR-9.
19. Add a linter per service.
20. Write `openapi.yaml` per service (including `/health`). The endpoints one service calls on the other must match in both documents.
21. Copy `system.schema.json` to the root and write `system.yaml` with every service, env var (secrets with `secret: true`, no default), cross-seam calls, and Azure resource names. Validate it locally.

## Phase 5: CI workflow (Day 7)

22. `.github/workflows/ci.yml` on every push and PR:
    - install, lint and test each service against a **SQL Server service container** (never Azure SQL)
    - coverage gate ≥70% per service
    - validate `system.yaml` against the schema and each OpenAPI file against the spec
    - build both Docker images
23. Open a PR and watch it run. Keep one genuine failed-then-fixed run for the report.

## Phase 6: One-time Azure setup (Days 8-9)

Use your prefix on every resource (e.g. `jsmith-ieu2023`), and the resource group for your class (`rg-sdd-3a` or `3b`). Don't create resource groups, and don't exceed 2 Container Apps, 2 SQL DBs, 1 Static Web App. Either script this in Bicep/Terraform or document every command in the README. Sketch with Azure CLI:

24. **SQL server**: `az sql server create -g <rg> -n <prefix>-sql -l <region> -u <admin> -p <pw>`
25. **Two databases**, each serverless:
    ```
    az sql db create -g <rg> -s <prefix>-sql -n <prefix>-<svc>-db \
      --edition GeneralPurpose --family Gen5 --compute-model Serverless \
      --min-capacity 0.5 --capacity 1 --auto-pause-delay <shortest allowed> \
      --max-size 2GB --backup-storage-redundancy Local
    ```
26. **Firewall**: add the "allow Azure services" rule (0.0.0.0-0.0.0.0). Add your own IP only temporarily.
27. **Logins**: connect once as admin; in `master` run `CREATE LOGIN`, then in each DB `CREATE USER` and grant rights, so each login has access only to its own DB.
28. **Container Apps environment** (`<prefix>-env`, Consumption), then the two apps: external ingress, `--min-replicas 0 --max-replicas 1`, `DATABASE_URL` as a **secret** referenced via `secretref:`, and the other service's URL plus CORS origin as env vars.
29. **Static Web App** `<prefix>-ui`. Save its deployment token as a GitHub secret.
30. **GitHub secrets**: service principal credentials, DB passwords, SWA token, and anything else sensitive.
31. **Registry**: GHCR by default. Make the packages public, or give Container Apps pull credentials as a secret.

## Phase 7: CD workflow (Days 9-11)

32. `.github/workflows/cd.yml`, on push to `main` only, and only if CI passed on the same commit (a `needs:` chain in one workflow, or `workflow_run`):
    - log in to GHCR and push images tagged with the **commit SHA**
    - `az login` with the service principal, then `az containerapp update --image ...:<sha>` for each service
    - generate `ui/config.js` with the services' URLs and deploy `ui/` to the SWA
    - **post-deploy `/health` check** on both services, retrying for several minutes to tolerate cold start and DB resume; fail the run if it doesn't get 200
33. Deploy with only `001` merged. Use the live app to create real data, then record it (screenshot or query) as "before" evidence.

## Phase 8: Migration evidence (Day 11-12)

34. **Now merge the `002` branch via PR.** Capture:
    - the successful CD run
    - the startup log line showing the migration applied
    - the data "after", showing rows preserved
35. Verify a second restart applies nothing.

## Phase 9: Partial-failure and pipeline evidence (Day 12-13)

36. Capture a screenshot or response of what users see when the other service is down. For the cold-start/failure paths, also scale one app down or stop it locally.
37. Collect links: one successful CD run on `main`, and one failed run that you fixed (note the cause).

## Phase 10: Documentation (Days 13-15)

38. **ADR.md**: keep 1-5 untouched (mark superseded ones). Add 6-10 (split, data/migrations, Azure hosting and scale-to-zero consequences plus 100x changes, pipeline/testing, one thing not built). The entries must span ≥3 commit dates, so write them as you go rather than at the end.
39. **AI_USAGE.md**: log AI help including Dockerfiles, workflows and IaC, and explain each file in your own words.
40. **README**: running locally, running one service, tests/coverage, how deployment works, reproducing the Azure setup, the live URL, and any incident record.
41. **Report (4-5 pages)**: before/after architecture, deployment diagram naming the Azure resources, DB diagram per service, migration evidence, partial-failure evidence, pipeline evidence, AI disclosure statement.
42. Make sure `system.yaml`, the OpenAPI files, diagrams and deployment all match what is actually deployed.

## Phase 11: Submit (by Nov 21 to be safe)

43. Confirm that `main` is deployed and the live URL works (cold-start it once).
44. Check you have ≥12 new commits over ≥6 days with no day over 40%.
45. Tag and push:
    ```
    git tag submission <full-sha>
    git push origin submission
    ```
    Submit the repo URL and the full SHA (they must match the tag).
46. Leave Azure running until grades are published.

## Prepare for the comprehension check

It's on paper without notes and **multiplies your grade**. Be able to explain every line of your Dockerfiles, compose file, workflows and migration runner, why you chose each approach, what happens at cold start, and how the cross-seam failure is handled. Don't paste AI output you can't explain.

## Common pitfalls

- Committing a secret, even once. Rotate it within 24h and log it in the README.
- Merging the data-changing migration before Azure has data (you lose the evidence).
- Recreating the DB or deleting a volume to "fix" a deployment.
- Making `/health` depend on the other service.
- Forgetting timeouts on outbound calls.
- Hardcoded URLs or ports.
- Using `latest` only as the image tag.
- Creating a third container or extra Azure resources (even temporarily).
- Leaving all commits to the last two days.

## Suggested schedule

| Days | Focus |
|---|---|
| 1-3 | Phases 0-1 (split, port, endpoints) |
| 3-6 | Phases 2-3 (migrations, Docker, compose) |
| 5-7 | Phases 4-5 (tests, specs, CI) |
| 8-11 | Phases 6-8 (Azure setup, CD, migration evidence) |
| 12-13 | Phase 9 (failure and pipeline evidence) |
| 13-16 | Phases 10-11 (docs, report, tag, study) |

If you tell me your Assignment 1 stack (Python/Node, framework, ORM) and what the two domains are, I can help with specific Dockerfiles, the compose file, the migration runner, or the workflows.
