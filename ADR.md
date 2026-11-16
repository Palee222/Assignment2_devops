## Security Incident Notebook + Password Hygiene Checker

### ADR-7: Versioned database migrations and recovery

- **Status:** Accepted
- **Decision:** Each service owns an ordered, immutable migration history.
  The service startup runner applies pending migrations in a transaction and
  records each successful version in that database's `schema_migrations`
  table. A failed migration is not recorded as applied.
- **Data preservation:** Schema changes use additive or explicitly
  data-preserving operations. Never drop or recreate a database or table
  during deployment. Back up the database and verify the backup before
  applying production migrations.
- **Recovery:** If a migration fails, stop the rollout and keep the affected
  service out of rotation. Inspect the migration error and database state,
  then restore the verified pre-migration backup only when the migration left
  data or schema integrity uncertain. If the schema is sound, correct the
  issue with a new forward migration; never edit an already-applied migration.
  Re-run the migration runner and verify both the ledger and representative
  data before resuming the rollout. If rollback is necessary, use a separately
  reviewed, tested compensating migration rather than dropping/recreating
  objects.
