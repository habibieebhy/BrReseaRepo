from pydantic import BaseModel


# ---------------------------------------------------------------------
# Infrastructure
# ---------------------------------------------------------------------


class Service(BaseModel):
    name: str
    provider: str
    healthy: bool
    version: str | None = None
    endpoint: str | None = None


class ServicesResponse(BaseModel):
    services: list[Service]


# ---------------------------------------------------------------------
# Celery
# ---------------------------------------------------------------------


class Worker(BaseModel):
    name: str
    status: str
    active_tasks: int


class Task(BaseModel):
    id: str
    name: str
    worker: str
    state: str


# ---------------------------------------------------------------------
# Queues
# ---------------------------------------------------------------------


class Queue(BaseModel):
    name: str
    pending: int
    consumers: int
    healthy: bool = True


# ---------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------


class StorageProvider(BaseModel):
    provider: str
    healthy:bool
    endpoint: str | None = None
    bucket: str | None = None


class Artifact(BaseModel):
    job_id: str
    artifact_type: str
    location: str
    size: int | None = None

# ---------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------


class DockerContainer(BaseModel):
    id: str
    name: str
    image: str
    status: str


class DockerContainersResponse(BaseModel):
    containers: list[DockerContainer]


class DockerHealth(BaseModel):
    provider: str
    healthy: bool
    error: str | None = None


class DockerLogs(BaseModel):
    container: str
    logs: str


# ---------------------------------------------------------------------
# Runtime Settings
# ---------------------------------------------------------------------


class RuntimeSettings(BaseModel):
    artifact_backend: str
    embedding_plugin: str
    embedding_model: str
    log_level: str


# ---------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------


class ComponentHealth(BaseModel):
    component: str
    healthy: bool
    message: str | None = None


class HealthResponse(BaseModel):
    components: list[ComponentHealth]

# ---------------------------------------------------------------------
# Celery
# ---------------------------------------------------------------------

class WorkersResponse(BaseModel):
    workers: list[Worker]


class CeleryTask(BaseModel):
    id: str
    name: str
    worker: str
    state: str


class TasksResponse(BaseModel):
    tasks: list[CeleryTask]


class CeleryStats(BaseModel):
    workers: dict


class CeleryHealth(BaseModel):
    provider: str
    healthy: bool
    error: str | None = None

# ---------------------------------------------------------------------
# Plugins
# ---------------------------------------------------------------------


class EmbeddingPlugin(BaseModel):
    name: str
    version: str
    models: list[str]


class DownloaderPlugin(BaseModel):
    name: str
    version: str
    source_types: list[str]


class EmbeddingPluginsResponse(BaseModel):
    plugins: list[EmbeddingPlugin]


class DownloaderPluginsResponse(BaseModel):
    plugins: list[DownloaderPlugin]

# ---------------------------------------------------------------------
# Chunker Plugins
# ---------------------------------------------------------------------


class ChunkerPlugin(BaseModel):
    name: str
    version: str


class ChunkerPluginsResponse(BaseModel):
    plugins: list[ChunkerPlugin]
