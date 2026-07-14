import json
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

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
)

# ---------------------------------------------------------------------
# Queues
# ---------------------------------------------------------------------

from api.prod_api.queues import (
    broker_health,
    queues,
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
from runtime.jobs.repository import JobRepository
from runtime.jobs.service import JobRetryError, retry_failed_job
from runtime.knowledge import (
    KnowledgeAccessRepository,
    KnowledgeBaseError,
    describe_knowledge_base,
    fetch_chunk,
    list_knowledge_bases,
    search_knowledge_base,
)


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    limit: int = Field(default=5, ge=1, le=20)


class KnowledgeAccessRequest(BaseModel):
    enabled: bool

router = APIRouter()


@router.get("/jobs")
def ingestion_jobs(limit: int = 100, tenant_id: str | None = None):
    try:
        return {"jobs": JobRepository.list(limit=min(max(limit, 1), 500), tenant_id=tenant_id)}
    except Exception as exc:
        return {"jobs": [], "error": str(exc)}


@router.get("/jobs/{job_id}")
def ingestion_job(job_id: str):
    job = JobRepository.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    response = {"job": job}
    if job["status"] == "completed":
        try:
            response["knowledge_base"] = describe_knowledge_base(job_id)
        except KnowledgeBaseError:
            pass
    return response


@router.post("/jobs/{job_id}/retry")
def retry_ingestion_job(job_id: str):
    try:
        return retry_failed_job(job_id)
    except JobRetryError as exc:
        message = str(exc)
        status_code = 404 if message == "Job not found." else 409
        raise HTTPException(status_code=status_code, detail=message) from exc


# =====================================================================
# Knowledge bases and semantic retrieval
# =====================================================================

@router.get("/knowledge")
def knowledge_bases(limit: int = 100, tenant_id: str | None = None):
    return {
        "knowledge_bases": list_knowledge_bases(
            tenant_id=tenant_id,
            limit=limit,
        )
    }


@router.get("/knowledge/{job_id}")
def knowledge_base(job_id: str):
    try:
        return {"knowledge_base": describe_knowledge_base(job_id)}
    except KnowledgeBaseError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/knowledge/{job_id}/search")
def knowledge_search(job_id: str, payload: KnowledgeSearchRequest):
    try:
        manifest = describe_knowledge_base(job_id)
        return {
            "knowledge_base_id": job_id,
            "query": payload.query,
            "results": search_knowledge_base(
                job_id,
                payload.query,
                limit=payload.limit,
                tenant_id=manifest["tenant_id"],
            ),
        }
    except KnowledgeBaseError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/knowledge/{job_id}/chunks/{chunk_index}")
def knowledge_chunk(job_id: str, chunk_index: int):
    try:
        manifest = describe_knowledge_base(job_id)
        return fetch_chunk(
            f"{job_id}:{chunk_index}",
            knowledge_base_id=job_id,
            tenant_id=manifest["tenant_id"],
        )
    except KnowledgeBaseError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/knowledge/{job_id}/access")
def knowledge_access(job_id: str):
    try:
        manifest = describe_knowledge_base(job_id)
    except KnowledgeBaseError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "knowledge_base_id": job_id,
        "tenant_id": manifest["tenant_id"],
        "enabled": KnowledgeAccessRepository.is_enabled(manifest["tenant_id"], job_id),
    }


@router.put("/knowledge/{job_id}/access")
def update_knowledge_access(job_id: str, payload: KnowledgeAccessRequest):
    try:
        manifest = describe_knowledge_base(job_id)
    except KnowledgeBaseError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    enabled = KnowledgeAccessRepository.set_enabled(
        manifest["tenant_id"],
        job_id,
        payload.enabled,
    )
    return {"knowledge_base_id": job_id, "enabled": enabled}


@router.get("/mcp/status")
def mcp_status():
    state_path = Path(".brixta/connection.json")
    state = {}
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            state = {}
    def process_alive(pid: object) -> bool:
        if isinstance(pid, bool):
            return False

        if isinstance(pid, int):
            process_id = pid
        elif isinstance(pid, str):
            try:
                process_id = int(pid)
            except ValueError:
                return False
        else:
            return False

        # PID zero and negative PIDs address process groups rather than one
        # BRIXTA-managed process, so they must never be probed here.
        if process_id <= 0:
            return False

        try:
            os.kill(process_id, 0)
            return True
        except (OSError, OverflowError):
            return False

    mcp_alive = process_alive(state.get("mcp_pid"))
    tunnel_alive = process_alive(state.get("tunnel_pid"))
    public_url = state.get("mcp_url") or os.getenv("BRIXTA_MCP_PUBLIC_URL", "")
    configured = bool(public_url.startswith("https://"))
    local_client = state.get("mode") == "local-client" and public_url.startswith(
        ("http://127.0.0.1", "http://localhost")
    )
    return {
        "connected": (
            local_client and mcp_alive
        ) or (
            configured and (
                (mcp_alive and tunnel_alive)
                if state.get("mode") == "local"
                else True
            )
        ),
        "mode": state.get("mode") or ("production" if configured else "disconnected"),
        "mcp_url": public_url if configured or local_client else None,
        "authenticated": state.get("auth_mode") == "oauth-local" or os.getenv("BRIXTA_MCP_AUTH_MODE") == "jwt",
        "shared_gateway": True,
    }

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
