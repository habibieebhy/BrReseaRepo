from fastapi import APIRouter, HTTPException

# ---------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------

from api.prod_api.storage import (
    provider,
    storage_health,
    artifact_statistics,
    artifacts,
    objects,
)

# ---------------------------------------------------------------------
# Runtime Settings
# ---------------------------------------------------------------------

from api.prod_api.settings import (
    runtime,
    infrastructure,
    environment,
    configuration,
    desired,
    save_desired,
    DesiredRuntimeSettings,
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
    pod_logs,
    restart_deployment,
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
# Plugins
# ---------------------------------------------------------------------

from api.prod_api.plugins import (
    embedding_plugins,
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
from runtime.jobs.repository import JobRepository
from runtime.jobs.service import JobRetryError, retry_failed_job

router = APIRouter()


@router.get("/jobs")
def ingestion_jobs(limit: int = 100, tenant_id: str | None = None):
    try:
        return {"jobs": JobRepository.list(limit=min(max(limit, 1), 500), tenant_id=tenant_id)}
    except Exception as exc:
        return {"jobs": [], "error": str(exc)}


@router.post("/jobs/{job_id}/retry")
def retry_ingestion_job(job_id: str):
    try:
        return retry_failed_job(job_id)
    except JobRetryError as exc:
        message = str(exc)
        status_code = 404 if message == "Job not found." else 409
        raise HTTPException(status_code=status_code, detail=message) from exc

from api.prod_api.plugins import (
    embedding_plugins,
    downloader_plugins,
)
from api.prod_api.plugins import (
    embedding_plugins,
    downloader_plugins,
    chunker_plugins,
)

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


@router.get("/storage/objects")
def storage_objects(prefix: str = ""):
    return objects(prefix)


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


@router.get("/settings/control-plane")
def control_plane_settings():
    return desired()


@router.put("/settings/control-plane")
def update_control_plane_settings(payload: DesiredRuntimeSettings):
    return save_desired(payload)


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


@router.get("/kubernetes/pods/{namespace}/{name}/logs")
def kubernetes_pod_logs(namespace: str, name: str, tail: int = 200):
    return pod_logs(namespace, name, tail)


@router.post("/kubernetes/deployments/{namespace}/{name}/restart")
def kubernetes_restart_deployment(namespace: str, name: str):
    return restart_deployment(namespace, name)


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

# =====================================================================
# Plugins
# =====================================================================

@router.get("/plugins/embedding")
def plugins_embedding():
    return embedding_plugins()

@router.get("/plugins/downloader")
def plugins_downloader():
    return downloader_plugins()

@router.get("/plugins/chunker")
def plugins_chunker():
    return chunker_plugins()
