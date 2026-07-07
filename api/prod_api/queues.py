import redis

from core.config import REDIS_URL


def client() -> redis.Redis:
    """
    Returns the configured Redis client.
    """

    return redis.Redis.from_url(
        REDIS_URL,
        decode_responses=True,
    )


def broker_health() -> dict:
    """
    Returns Redis health.
    """

    try:
        client().ping()

        return {
            "provider": "redis",
            "healthy": True,
        }

    except Exception as e:

        return {
            "provider": "redis",
            "healthy": False,
            "error": str(e),
        }


def queues() -> dict:
    """
    Returns queue statistics.
    """

    r = client()

    names = []

    for key in r.scan_iter(match="*"):

        try:

            if r.type(key) == "list":

                names.append(
                    {
                        "name": key,
                        "pending": r.llen(key),
                    }
                )

        except Exception:
            continue

    return {
        "provider": "redis",
        "queues": names,
    }


def queue(name: str) -> dict:
    """
    Returns a single queue.
    """

    r = client()

    return {
        "name": name,
        "pending": r.llen(name),
    }


def purge_queue(name: str) -> dict:
    """
    Deletes all queued messages.
    """

    r = client()

    deleted = r.delete(name)

    return {
        "queue": name,
        "deleted": bool(deleted),
    }