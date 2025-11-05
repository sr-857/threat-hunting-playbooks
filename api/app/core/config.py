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
    redis_url: str = Field(default="redis://redis:6379/0", validation_alias=AliasChoices("REDIS_URL", "CELERY_BROKER_URL"))
    celery_result_backend: str | None = Field(default=None, validation_alias=AliasChoices("CELERY_RESULT_BACKEND"))
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
