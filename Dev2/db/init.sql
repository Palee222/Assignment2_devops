USE [master];
GO

IF DB_ID(N'PasswordServiceDb') IS NULL
BEGIN
    CREATE DATABASE [PasswordServiceDb];
END;
GO

IF DB_ID(N'IncidentsServiceDb') IS NULL
BEGIN
    CREATE DATABASE [IncidentsServiceDb];
END;
GO

ALTER DATABASE [PasswordServiceDb] SET DB_CHAINING OFF;
ALTER DATABASE [IncidentsServiceDb] SET DB_CHAINING OFF;
GO

IF SUSER_ID(N'password_service_login') IS NULL
BEGIN
    CREATE LOGIN [password_service_login]
        WITH PASSWORD = N'$(PASSWORD_DB_PASSWORD)',
        CHECK_POLICY = ON,
        CHECK_EXPIRATION = OFF;
END
ELSE
BEGIN
    ALTER LOGIN [password_service_login]
        WITH PASSWORD = N'$(PASSWORD_DB_PASSWORD)',
        CHECK_POLICY = ON,
        CHECK_EXPIRATION = OFF;
END;
GO

IF SUSER_ID(N'incidents_service_login') IS NULL
BEGIN
    CREATE LOGIN [incidents_service_login]
        WITH PASSWORD = N'$(INCIDENTS_DB_PASSWORD)',
        CHECK_POLICY = ON,
        CHECK_EXPIRATION = OFF;
END
ELSE
BEGIN
    ALTER LOGIN [incidents_service_login]
        WITH PASSWORD = N'$(INCIDENTS_DB_PASSWORD)',
        CHECK_POLICY = ON,
        CHECK_EXPIRATION = OFF;
END;
GO

ALTER LOGIN [password_service_login]
    WITH DEFAULT_DATABASE = [PasswordServiceDb];
ALTER LOGIN [incidents_service_login]
    WITH DEFAULT_DATABASE = [IncidentsServiceDb];
GO

USE [PasswordServiceDb];
GO

IF DATABASE_PRINCIPAL_ID(N'password_service_login') IS NULL
BEGIN
    CREATE USER [password_service_login] FOR LOGIN [password_service_login];
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.database_role_members AS role_member
    JOIN sys.database_principals AS role_principal
        ON role_member.role_principal_id = role_principal.principal_id
    JOIN sys.database_principals AS member_principal
        ON role_member.member_principal_id = member_principal.principal_id
    WHERE role_principal.name = N'db_datareader'
      AND member_principal.name = N'password_service_login'
)
    ALTER ROLE [db_datareader] ADD MEMBER [password_service_login];
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.database_role_members AS role_member
    JOIN sys.database_principals AS role_principal
        ON role_member.role_principal_id = role_principal.principal_id
    JOIN sys.database_principals AS member_principal
        ON role_member.member_principal_id = member_principal.principal_id
    WHERE role_principal.name = N'db_datawriter'
      AND member_principal.name = N'password_service_login'
)
    ALTER ROLE [db_datawriter] ADD MEMBER [password_service_login];
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.database_role_members AS role_member
    JOIN sys.database_principals AS role_principal
        ON role_member.role_principal_id = role_principal.principal_id
    JOIN sys.database_principals AS member_principal
        ON role_member.member_principal_id = member_principal.principal_id
    WHERE role_principal.name = N'db_ddladmin'
      AND member_principal.name = N'password_service_login'
)
    ALTER ROLE [db_ddladmin] ADD MEMBER [password_service_login];
GO

USE [IncidentsServiceDb];
GO

IF DATABASE_PRINCIPAL_ID(N'incidents_service_login') IS NULL
BEGIN
    CREATE USER [incidents_service_login] FOR LOGIN [incidents_service_login];
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.database_role_members AS role_member
    JOIN sys.database_principals AS role_principal
        ON role_member.role_principal_id = role_principal.principal_id
    JOIN sys.database_principals AS member_principal
        ON role_member.member_principal_id = member_principal.principal_id
    WHERE role_principal.name = N'db_datareader'
      AND member_principal.name = N'incidents_service_login'
)
    ALTER ROLE [db_datareader] ADD MEMBER [incidents_service_login];
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.database_role_members AS role_member
    JOIN sys.database_principals AS role_principal
        ON role_member.role_principal_id = role_principal.principal_id
    JOIN sys.database_principals AS member_principal
        ON role_member.member_principal_id = member_principal.principal_id
    WHERE role_principal.name = N'db_datawriter'
      AND member_principal.name = N'incidents_service_login'
)
    ALTER ROLE [db_datawriter] ADD MEMBER [incidents_service_login];
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.database_role_members AS role_member
    JOIN sys.database_principals AS role_principal
        ON role_member.role_principal_id = role_principal.principal_id
    JOIN sys.database_principals AS member_principal
        ON role_member.member_principal_id = member_principal.principal_id
    WHERE role_principal.name = N'db_ddladmin'
      AND member_principal.name = N'incidents_service_login'
)
    ALTER ROLE [db_ddladmin] ADD MEMBER [incidents_service_login];
GO
