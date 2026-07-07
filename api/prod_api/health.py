from api.prod_api.kubernetes import cluster_health
from api.prod_api.queues import broker_health
from api.prod_api.storage import provider as storage_provider


def runtime() -> dict:
    """
    Returns Runtime health.
    """

    return {
        "provider": "brixta-runtime",
        "healthy": True,
    }


def database() -> dict:
    """
    Returns Database health.

    TODO:
    Replace with a real PostgreSQL health check.
    """

    return {
        "provider": "postgresql",
        "healthy": True,
    }


def redis() -> dict:
    """
    Returns Redis health.
    """

    return broker_health()


def storage() -> dict:
    """
    Returns Storage health.
    """

    storage = storage_provider()

    return {
        "provider": storage.provider,
        "healthy": storage.healthy,
    }


def kubernetes() -> dict:
    """
    Returns Kubernetes health.
    """

    return cluster_health()


def health() -> dict:
    """
    Returns the overall BRIXTA infrastructure health.
    """

    services = {
        "runtime": runtime(),
        "database": database(),
        "redis": redis(),
        "storage": storage(),
        "kubernetes": kubernetes(),
    }

    overall = all(
        service["healthy"]
        for service in services.values()
    )

    return {
        "healthy": overall,
        "services": services,
    }