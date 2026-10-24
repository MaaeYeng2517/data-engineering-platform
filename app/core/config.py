"""
Enterprise Data API - Configuration
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    app_env: str = Field(default="dev")
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_prefix: str = Field(default="/api/v1")
    log_level: str = Field(default="INFO")

    database_url: str = Field(default="postgresql+asyncpg://data_api:change_me@localhost:5432/enterprise_data")
    db_pool_size: int = Field(default=20)
    db_max_overflow: int = Field(default=10)

    redis_url: str = Field(default="redis://localhost:6379/0")
    celery_broker_url: str = Field(default="redis://localhost:6379/0")
    celery_result_backend: str = Field(default="redis://localhost:6379/1")

    s3_endpoint: str = Field(default="http://localhost:9000")
    s3_region: str = Field(default="us-east-1")
    s3_access_key: str = Field(default="minioadmin")
    s3_secret_key: str = Field(default="minioadmin")
    s3_bucket_raw: str = Field(default="enterprise-raw")
    s3_bucket_curated: str = Field(default="enterprise-curated")
    s3_use_ssl: bool = Field(default=False)

    oidc_issuer: str = Field(default="")
    oidc_audience: str = Field(default="")
    oidc_jwks_url: str = Field(default="")
    jwt_algorithm: str = Field(default="RS256")

    rate_limit_per_minute: int = Field(default=60)
    request_timeout_seconds: int = Field(default=30)
    max_upload_size_mb: int = Field(default=100)
    idempotency_ttl_seconds: int = Field(default=3600)

    otel_exporter_otlp_endpoint: str = Field(default="http://localhost:4318")
    prometheus_metrics_path: str = Field(default="/metrics")


settings = Settings()
