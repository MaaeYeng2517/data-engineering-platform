-- Airflow metadata database
SELECT 'CREATE DATABASE airflow'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow')\gexec

DO $$
DECLARE
    db_owner TEXT;
BEGIN
    SELECT current_user INTO db_owner;
    EXECUTE format('GRANT ALL PRIVILEGES ON DATABASE airflow TO %I', db_owner);
END
$$;
