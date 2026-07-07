from core.config import (
    ARTIFACT_BACKEND,
    EMBEDDING_MODEL,
    EMBEDDING_PROVIDER,
    LOG_LEVEL,
)

from runtime.artifacts.repository import ArtifactRepository

from api.prod_api.models import RuntimeSettings


def runtime() -> RuntimeSettings:
    """
    Returns the active runtime configuration.
    """

    return RuntimeSettings(
        artifact_backend=ARTIFACT_BACKEND,
        embedding_provider=EMBEDDING_PROVIDER,
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
            "connected": True,      # we'll replace with a real health check next
        },
        "redis": {
            "provider": "redis",
            "connected": True,      # real ping later
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
        "embedding_provider": EMBEDDING_PROVIDER,
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