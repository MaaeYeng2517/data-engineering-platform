#!/bin/bash
set -e

# Create superset database if not exists
export PGPASSWORD=${POSTGRES_PASSWORD:-dataair}
psql -h postgres -U ${POSTGRES_USER:-dataair} -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'superset'" | grep -q 1 || psql -h postgres -U ${POSTGRES_USER:-dataair} -d postgres -c "CREATE DATABASE superset;"

# Wait for postgres
until pg_isready -h postgres -U ${POSTGRES_USER:-dataair}; do
  echo "Waiting for postgres..."
  sleep 2
done

# Initialize Superset
superset db upgrade
superset fab create-admin \
  --username ${SUPERSET_ADMIN_USER} \
  --firstname ${SUPERSET_ADMIN_FIRSTNAME} \
  --lastname ${SUPERSET_ADMIN_LASTNAME} \
  --email ${SUPERSET_ADMIN_EMAIL} \
  --password ${SUPERSET_ADMIN_PASSWORD} || true
superset init

if [ "${SUPERSET_LOAD_EXAMPLES}" = "yes" ]; then
  superset load_examples
fi

echo "Superset initialization complete"
