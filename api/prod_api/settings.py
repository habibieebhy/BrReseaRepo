from core.config import (
    ARTIFACT_BACKEND,
    EMBEDDING_PLUGIN,
    EMBEDDING_MODEL,
    LOG_LEVEL,
)

from runtime.artifacts.repository import ArtifactRepository

from api.prod_api.models import RuntimeSettings
from pydantic import BaseModel, Field
from core.plugin_loader import registry
from runtime.settings import RuntimeSettingsRepository
from api.prod_api.health import database as database_health
from api.prod_api.queues import broker_health


class DesiredRuntimeSettings(BaseModel):
    artifact_backend: str = "local"
    minio_endpoint: str = "localhost:9000"
    minio_console_url: str = "http://localhost:9001"
    minio_bucket: str = "brixta"
    default_plugins: dict[str, str] = Field(default_factory=dict)
    embedding_model: str = "nomic-ai/nomic-embed-text-v1.5"
    pipeline_order: list[str] = Field(default_factory=lambda: ["downloader", "parser", "chunker", "embedding", "storage"])


def runtime() -> RuntimeSettings:
    """
    Returns the active runtime configuration.
    """

    return RuntimeSettings(
        artifact_backend=ARTIFACT_BACKEND,
        embedding_plugin=EMBEDDING_PLUGIN,
        embedding_model=EMBEDDING_MODEL,
        log_level=LOG_LEVEL,
    )


def infrastructure() -> dict:
    """
    Returns infrastructure status.

    Never exposes credentials or connection strings.
    """

    return {
        "database": {
            "provider": "postgresql",
            "connected": database_health()["healthy"],
        },
        "redis": {
            "provider": "redis",
            "connected": broker_health()["healthy"],
        },
        "storage": {
            "provider": ArtifactRepository.provider(),
            "connected": ArtifactRepository.health(),
        },
    }


def environment() -> dict:
    """
    Returns non-sensitive runtime environment information.
    """

    return {
        "artifact_backend": ARTIFACT_BACKEND,
        "embedding_plugin": EMBEDDING_PLUGIN,
        "embedding_model": EMBEDDING_MODEL,
        "log_level": LOG_LEVEL,
    }


def configuration() -> dict:
    """
    Returns the complete runtime configuration.
    """

    return {
        "runtime": runtime().model_dump(),
        "infrastructure": infrastructure(),
        "environment": environment(),
    }


def desired() -> dict:
    saved = RuntimeSettingsRepository.get()
    defaults = DesiredRuntimeSettings(
        artifact_backend=ARTIFACT_BACKEND,
        default_plugins=registry.validate_selection({}),
        embedding_model=EMBEDDING_MODEL,
    ).model_dump()
    saved = {**defaults, **saved, "default_plugins": {**defaults["default_plugins"], **saved.get("default_plugins", {})}}
    return {"settings": saved, "active": runtime().model_dump(), "restart_required": saved.get("artifact_backend") != ARTIFACT_BACKEND}


def save_desired(payload: DesiredRuntimeSettings) -> dict:
    data = payload.model_dump()
    data["default_plugins"] = registry.validate_selection(data["default_plugins"])
    if sorted(data["pipeline_order"]) != ["chunker", "downloader", "embedding", "parser", "storage"] or data["pipeline_order"][0] != "downloader" or data["pipeline_order"][-1] != "storage":
        raise ValueError("Pipeline order must contain every stage exactly once, begin with downloader, and end with storage.")
    RuntimeSettingsRepository.save(data)
    return {"settings": data, "active": runtime().model_dump(), "restart_required": data["artifact_backend"] != ARTIFACT_BACKEND, "message": "Settings saved to the control-plane runtime environment. Restart BRIXTA Core and workers to apply infrastructure changes."}
