IF OBJECT_ID(N'dbo.weak_passwords', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.weak_passwords (
        id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        password NVARCHAR(255) NOT NULL,
        source NVARCHAR(255) NULL
    );
END;

IF OBJECT_ID(N'dbo.password_rules', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.password_rules (
        id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        name NVARCHAR(255) NOT NULL,
        description NVARCHAR(MAX) NULL,
        min_length INT NULL,
        require_upper BIT NULL,
        require_lower BIT NULL,
        require_digit BIT NULL,
        require_symbol BIT NULL
    );
END;
