-- OpenMetadata metadata database
SELECT 'CREATE DATABASE openmetadata_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'openmetadata_db')\gexec

DO $$
DECLARE
    db_owner TEXT;
BEGIN
    SELECT current_user INTO db_owner;
    EXECUTE format('GRANT ALL PRIVILEGES ON DATABASE openmetadata_db TO %I', db_owner);
END
$$;
