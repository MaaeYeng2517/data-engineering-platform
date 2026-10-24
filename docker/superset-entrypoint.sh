#!/bin/bash
set -e

export PGPASSWORD=${POSTGRES_PASSWORD:-dataair}
# Ensure database exists
psql -h postgres -U ${POSTGRES_USER:-dataair} -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'superset'" | grep -q 1 || psql -h postgres -U ${POSTGRES_USER:-dataair} -d postgres -c "CREATE DATABASE superset;"

# Start Superset
/bin/sh -c "/usr/bin/run-server.sh"
