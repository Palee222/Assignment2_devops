IF COL_LENGTH(N'dbo.weak_passwords', N'is_active') IS NULL
BEGIN
    ALTER TABLE dbo.weak_passwords
    ADD is_active BIT NOT NULL
        CONSTRAINT DF_weak_passwords_is_active DEFAULT (1);
END;
