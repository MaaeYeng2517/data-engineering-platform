-- Data warehouse: medallion layer layout inside the dataair database
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;
CREATE SCHEMA IF NOT EXISTS audit;

COMMENT ON SCHEMA raw IS 'Immutable landing zone. Append-only, never updated in place.';
COMMENT ON SCHEMA staging IS 'Typed and deduplicated intermediate tables.';
COMMENT ON SCHEMA marts IS 'Business-facing models consumed by BI and APIs.';
COMMENT ON SCHEMA audit IS 'dbt, Great Expectations and pipeline run metadata.';

-- Audit / metadata tables used by dbt and Great Expectations
CREATE TABLE IF NOT EXISTS audit.elt_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id VARCHAR(64) NOT NULL,
    model_name VARCHAR(255) NOT NULL,
    layer VARCHAR(50) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    duration_seconds DOUBLE PRECISION,
    rows_affected BIGINT DEFAULT 0,
    extra JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_elt_runs_model ON audit.elt_runs(model_name, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_elt_runs_run ON audit.elt_runs(run_id);

CREATE TABLE IF NOT EXISTS audit.data_quality_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id VARCHAR(64) NOT NULL,
    suite_name VARCHAR(255) NOT NULL,
    checkpoint_name VARCHAR(255) NOT NULL,
    data_asset VARCHAR(500),
    status VARCHAR(30) NOT NULL,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    expectation_config JSONB NOT NULL DEFAULT '{}',
    result JSONB NOT NULL DEFAULT '{}',
    observed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dq_results_suite ON audit.data_quality_results(suite_name, observed_at DESC);
