from api.prod_api.queues import broker_health
from api.prod_api.storage import provider as storage_provider
from core.database import get_connection


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

    Executes a lightweight query against the configured PostgreSQL database.
    """

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        return {"provider": "postgresql", "healthy": True}
    except Exception as exc:
        return {"provider": "postgresql", "healthy": False, "error": str(exc)}


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


def health() -> dict:
    """
    Returns the overall BRIXTA infrastructure health.
    """

    services = {
        "runtime": runtime(),
        "database": database(),
        "redis": redis(),
        "storage": storage(),
    }

    overall = all(
        service["healthy"]
        for service in services.values()
    )

    return {
        "healthy": overall,
        "services": services,
    }
