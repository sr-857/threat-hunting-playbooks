from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Threat Hunting Playbooks API"
    api_prefix: str = "/api"
    database_url: str
    minio_endpoint: str = "http://minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    samples_root: Path = Field(default=Path("/samples"), validation_alias=AliasChoices("SAMPLES_ROOT", "PLAYBOOK_SAMPLE_PATH"))
    rules_root: Path = Field(default=Path("/rules"), validation_alias=AliasChoices("RULES_ROOT", "PLAYBOOK_RULES_ROOT"))
    artifacts_root: Path = Field(default=Path("/logs"), validation_alias=AliasChoices("ARTIFACTS_ROOT", "PLAYBOOK_ARTIFACT_ROOT"))
    log_level: str = "INFO"
    json_logs: bool = Field(default=False, validation_alias=AliasChoices("JSON_LOGS"))
    enable_metrics: bool = Field(default=True, validation_alias=AliasChoices("ENABLE_METRICS"))
    metrics_endpoint: str = Field(default="/metrics", validation_alias=AliasChoices("METRICS_ENDPOINT"))
    metrics_namespace: str = Field(default="threat_playbooks", validation_alias=AliasChoices("METRICS_NAMESPACE"))
    worker_metrics_port: int = Field(default=9002, validation_alias=AliasChoices("WORKER_METRICS_PORT"))
    alert_confidence_threshold: float = Field(default=0.7, validation_alias=AliasChoices("ALERT_CONFIDENCE_THRESHOLD"))
    alert_webhook_url: str | None = Field(default=None, validation_alias=AliasChoices("ALERT_WEBHOOK_URL"))
    redis_url: str = Field(default="redis://redis:6379/0", validation_alias=AliasChoices("REDIS_URL", "CELERY_BROKER_URL"))
    celery_result_backend: str | None = Field(default=None, validation_alias=AliasChoices("CELERY_RESULT_BACKEND"))
    secret_key: str = Field(default="change-me", validation_alias=AliasChoices("SECRET_KEY", "JWT_SECRET_KEY"))
    access_token_expire_minutes: int = Field(
        default=60,
        validation_alias=AliasChoices("ACCESS_TOKEN_EXPIRE_MINUTES", "JWT_EXPIRE_MINUTES"),
    )
    initial_admin_email: str = Field(
        default="admin@example.com",
        validation_alias=AliasChoices("INITIAL_ADMIN_EMAIL", "ADMIN_EMAIL"),
    )
    initial_admin_password: str = Field(
        default="ChangeMe123!",
        validation_alias=AliasChoices("INITIAL_ADMIN_PASSWORD", "ADMIN_PASSWORD"),
    )
    alert_slack_webhook_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ALERT_SLACK_WEBHOOK_URL"),
    )
    alert_teams_webhook_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ALERT_TEAMS_WEBHOOK_URL"),
    )
    alert_pagerduty_routing_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ALERT_PAGERDUTY_ROUTING_KEY"),
    )
    alert_pagerduty_api_url: str = Field(
        default="https://events.pagerduty.com/v2/enqueue",
        validation_alias=AliasChoices("ALERT_PAGERDUTY_API_URL"),
    )
    alert_email_host: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ALERT_EMAIL_HOST"),
    )
    alert_email_port: int = Field(
        default=587,
        validation_alias=AliasChoices("ALERT_EMAIL_PORT"),
    )
    alert_email_username: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ALERT_EMAIL_USERNAME"),
    )
    alert_email_password: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ALERT_EMAIL_PASSWORD"),
    )
    alert_email_from: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ALERT_EMAIL_FROM"),
    )
    alert_email_to: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ALERT_EMAIL_TO"),
    )
    alert_email_use_tls: bool = Field(
        default=True,
        validation_alias=AliasChoices("ALERT_EMAIL_USE_TLS"),
    )
    splunk_base_url: str | None = Field(default=None, validation_alias=AliasChoices("SPLUNK_BASE_URL"))
    splunk_token: str | None = Field(default=None, validation_alias=AliasChoices("SPLUNK_TOKEN"))
    splunk_username: str | None = Field(default=None, validation_alias=AliasChoices("SPLUNK_USERNAME"))
    splunk_password: str | None = Field(default=None, validation_alias=AliasChoices("SPLUNK_PASSWORD"))
    splunk_verify_ssl: bool = Field(default=True, validation_alias=AliasChoices("SPLUNK_VERIFY_SSL"))
    elastic_endpoint: str | None = Field(default=None, validation_alias=AliasChoices("ELASTIC_ENDPOINT", "ELASTICSEARCH_ENDPOINT"))
    elastic_cloud_id: str | None = Field(default=None, validation_alias=AliasChoices("ELASTIC_CLOUD_ID"))
    elastic_api_key: str | None = Field(default=None, validation_alias=AliasChoices("ELASTIC_API_KEY"))
    elastic_username: str | None = Field(default=None, validation_alias=AliasChoices("ELASTIC_USERNAME"))
    elastic_password: str | None = Field(default=None, validation_alias=AliasChoices("ELASTIC_PASSWORD"))
    sentinel_workspace_id: str | None = Field(default=None, validation_alias=AliasChoices("SENTINEL_WORKSPACE_ID"))
    sentinel_tenant_id: str | None = Field(default=None, validation_alias=AliasChoices("SENTINEL_TENANT_ID"))
    sentinel_client_id: str | None = Field(default=None, validation_alias=AliasChoices("SENTINEL_CLIENT_ID"))
    sentinel_client_secret: str | None = Field(default=None, validation_alias=AliasChoices("SENTINEL_CLIENT_SECRET"))

    model_config = SettingsConfigDict(env_file=".env", extra="allow")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


def get_settings_dict() -> dict[str, Any]:
    settings = get_settings()
    return settings.model_dump()
