from runtime.celery_app import celery

from api.prod_api.models import (
    CeleryHealth,
    CeleryStats,
    CeleryTask,
    TasksResponse,
    Worker,
    WorkersResponse,
)


def inspect():
    """
    Returns the Celery inspection interface.
    """

    return celery.control.inspect()


def health() -> CeleryHealth:
    """
    Returns Celery health.
    """

    try:

        healthy = inspect().ping() is not None

        return CeleryHealth(
            provider="celery",
            healthy=healthy,
        )

    except Exception as e:

        return CeleryHealth(
            provider="celery",
            healthy=False,
            error=str(e),
        )


def workers() -> WorkersResponse:
    """
    Returns all Celery workers.
    """

    ping = inspect().ping() or {}
    active = inspect().active() or {}

    workers = []

    for worker_name in ping.keys():

        workers.append(
            Worker(
                name=worker_name,
                status="online",
                active_tasks=len(active.get(worker_name, [])),
            )
        )

    return WorkersResponse(
        workers=workers,
    )


def active_tasks() -> TasksResponse:
    """
    Returns active Celery tasks.
    """

    active = inspect().active() or {}

    tasks = []

    for worker_name, worker_tasks in active.items():

        for task in worker_tasks:

            tasks.append(
                CeleryTask(
                    id=task.get("id", ""),
                    name=task.get("name", ""),
                    worker=worker_name,
                    state="ACTIVE",
                )
            )

    return TasksResponse(
        tasks=tasks,
    )


def reserved_tasks() -> TasksResponse:
    """
    Returns reserved Celery tasks.
    """

    reserved = inspect().reserved() or {}

    tasks = []

    for worker_name, worker_tasks in reserved.items():

        for task in worker_tasks:

            tasks.append(
                CeleryTask(
                    id=task.get("id", ""),
                    name=task.get("name", ""),
                    worker=worker_name,
                    state="RESERVED",
                )
            )

    return TasksResponse(
        tasks=tasks,
    )


def scheduled_tasks() -> TasksResponse:
    """
    Returns scheduled Celery tasks.
    """

    scheduled = inspect().scheduled() or {}

    tasks = []

    for worker_name, worker_tasks in scheduled.items():

        for task in worker_tasks:

            request = task.get("request", {})

            tasks.append(
                CeleryTask(
                    id=request.get("id", ""),
                    name=request.get("name", ""),
                    worker=worker_name,
                    state="SCHEDULED",
                )
            )

    return TasksResponse(
        tasks=tasks,
    )


def stats() -> CeleryStats:
    """
    Returns Celery worker statistics.
    """

    return CeleryStats(
        workers=inspect().stats() or {},
    )