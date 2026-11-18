IF OBJECT_ID(N'dbo.health_probes', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.health_probes (
        probe_id NVARCHAR(36) NOT NULL PRIMARY KEY,
        checked_at DATETIMEOFFSET NOT NULL
    );
END;
