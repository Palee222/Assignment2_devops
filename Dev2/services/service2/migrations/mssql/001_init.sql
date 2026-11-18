IF OBJECT_ID(N'dbo.incidents', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.incidents (
        id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        title NVARCHAR(500) NOT NULL,
        description NVARCHAR(MAX) NOT NULL,
        severity NVARCHAR(50) NOT NULL,
        status NVARCHAR(50) NOT NULL,
        created_at DATETIMEOFFSET NOT NULL,
        updated_at DATETIMEOFFSET NOT NULL
    );
END;

IF OBJECT_ID(N'dbo.tags', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.tags (
        id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        name NVARCHAR(255) NOT NULL UNIQUE
    );
END;

IF OBJECT_ID(N'dbo.incident_tags', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.incident_tags (
        incident_id INT NOT NULL,
        tag_id INT NOT NULL,
        CONSTRAINT FK_incident_tags_incidents
            FOREIGN KEY (incident_id) REFERENCES dbo.incidents(id),
        CONSTRAINT FK_incident_tags_tags
            FOREIGN KEY (tag_id) REFERENCES dbo.tags(id),
        CONSTRAINT UQ_incident_tags UNIQUE (incident_id, tag_id)
    );
END;
