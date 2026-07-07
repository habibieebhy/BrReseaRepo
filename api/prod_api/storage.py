from runtime.artifacts.repository import ArtifactRepository

from api.prod_api.models import StorageProvider


def provider() -> StorageProvider:
    """
    Returns information about the currently configured
    artifact storage backend.
    """

    info = ArtifactRepository.info()

    return StorageProvider(
        provider=ArtifactRepository.provider(),
        healthy=ArtifactRepository.health(),
        endpoint=info.get("endpoint"),
        bucket=info.get("bucket"),
    )


def storage_health() -> str:
    """
    Returns the overall storage health.
    """

    return (
        "healthy"
        if provider().healthy
        else "unhealthy"
    )


def artifact_statistics() -> dict:
    """
    Returns artifact repository statistics.

    Placeholder for future implementations:
    - object count
    - total storage
    - backend metrics
    """

    storage = provider()

    return {
        "provider": storage.provider,
        "healthy": storage.healthy,
    }


def artifacts(job_id: str) -> dict:
    """
    Returns which artifacts exist for a given job.
    """

    return {
        "job_id": job_id,
        "raw": ArtifactRepository.raw_exists(job_id),
        "docling": ArtifactRepository.docling_exists(job_id),
        "markdown": ArtifactRepository.markdown_exists(job_id),
        "chunks": ArtifactRepository.chunks_exists(job_id),
        "embeddings": ArtifactRepository.embeddings_exists(job_id),
    }