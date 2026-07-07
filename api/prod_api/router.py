from fastapi import APIRouter

# ---------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------

from api.prod_api.storage import (
    provider,
    storage_health,
    artifact_statistics,
    artifacts,
)

# ---------------------------------------------------------------------
# Runtime Settings
# ---------------------------------------------------------------------

from api.prod_api.settings import (
    runtime,
    infrastructure,
    environment,
    configuration,
)

# ---------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------

from api.prod_api.health import (
    health,
    database,
    redis,
    storage,
    kubernetes,
)

# ---------------------------------------------------------------------
# Queues
# ---------------------------------------------------------------------

from api.prod_api.queues import (
    broker_health,
    queues,
)

# ---------------------------------------------------------------------
# Kubernetes
# ---------------------------------------------------------------------

from api.prod_api.kubernetes import (
    cluster_health,
    list_pods,
    list_deployments,
)

# ---------------------------------------------------------------------
# Celery
# ---------------------------------------------------------------------

from api.prod_api.celery import (
    health as celery_health,
    workers,
    active_tasks,
    reserved_tasks,
    scheduled_tasks,
    stats,
)

# ---------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------

from api.prod_api.docker import (
    docker_health,
    containers,
    container,
    restart,
    logs,
)

router = APIRouter()


# =====================================================================
# Storage
# =====================================================================

@router.get("/storage")
def storage_provider():
    return provider()


@router.get("/storage/health")
def storage_status():
    return {
        "status": storage_health(),
    }


@router.get("/storage/statistics")
def storage_stats():
    return artifact_statistics()


@router.get("/storage/artifacts/{job_id}")
def storage_artifacts(job_id: str):
    return artifacts(job_id)


# =====================================================================
# Runtime Settings
# =====================================================================

@router.get("/settings/runtime")
def runtime_settings():
    return runtime()


@router.get("/settings/infrastructure")
def infrastructure_settings():
    return infrastructure()


@router.get("/settings/environment")
def environment_settings():
    return environment()


@router.get("/settings")
def settings():
    return configuration()


# =====================================================================
# Overall Health
# =====================================================================

@router.get("/health")
def overall_health():
    return health()


@router.get("/health/database")
def database_health():
    return database()


@router.get("/health/redis")
def redis_health():
    return redis()


@router.get("/health/storage")
def storage_backend_health():
    return storage()


@router.get("/health/kubernetes")
def kubernetes_health():
    return kubernetes()


# =====================================================================
# Redis
# =====================================================================

@router.get("/redis")
def redis_info():
    return broker_health()


@router.get("/redis/queues")
def redis_queues():
    return queues()


# =====================================================================
# Kubernetes
# =====================================================================

@router.get("/kubernetes")
def kubernetes_info():
    return cluster_health()


@router.get("/kubernetes/pods")
def kubernetes_pods():
    return list_pods()


@router.get("/kubernetes/deployments")
def kubernetes_deployments():
    return list_deployments()


# =====================================================================
# Celery
# =====================================================================

@router.get("/celery")
def celery_info():
    return celery_health()


@router.get("/celery/workers")
def celery_workers():
    return workers()


@router.get("/celery/tasks/active")
def celery_active_tasks():
    return active_tasks()


@router.get("/celery/tasks/reserved")
def celery_reserved():
    return reserved_tasks()


@router.get("/celery/tasks/scheduled")
def celery_scheduled():
    return scheduled_tasks()


@router.get("/celery/stats")
def celery_stats():
    return stats()


# =====================================================================
# Docker
# =====================================================================

@router.get("/docker")
def docker_info():
    return docker_health()


@router.get("/docker/containers")
def docker_containers():
    return containers()


@router.get("/docker/container/{name}")
def docker_container(name: str):
    return container(name)


@router.post("/docker/restart/{name}")
def docker_restart(name: str):
    return restart(name)


@router.get("/docker/logs/{name}")
def docker_logs(name: str, tail: int = 200):
    return logs(name, tail)