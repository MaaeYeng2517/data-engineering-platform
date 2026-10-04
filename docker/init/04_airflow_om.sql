-- Dedicated Airflow metadata database for the OpenMetadata ingestion image.
-- It bundles its own Airflow version, so it must not share the airflow database
-- used by the 2.10.x services in this stack.
SELECT 'CREATE DATABASE airflow_om'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow_om')\gexec

DO $$
DECLARE
    db_owner TEXT;
BEGIN
    SELECT current_user INTO db_owner;
    EXECUTE format('GRANT ALL PRIVILEGES ON DATABASE airflow_om TO %I', db_owner);
END
$$;