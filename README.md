# BRIXTA Core

A modular, event-driven research ingestion pipeline designed for scalable document acquisition, parsing, semantic chunking, embedding generation, and vector storage.

---
## Architecture

```text
                     Client
                        │
                        ▼
                    FastAPI API
                        │
                        ▼
                PipelineContext
                        │
                        ▼
                 Celery Runtime
                        │
                        ▼
                  Plugin Loader
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
 DownloaderPlugin   ParserPlugin   StoragePlugin
        │               │                │
        ▼               ▼                ▼
Official Plugins (Default, Docling, Nomic, pgvector)
                        │
                        ▼
                Artifact Repository
                        │
                        ▼
              PostgreSQL + pgvector
```
---

## Project Structure

```text
brixta-core/

├── api/
│
├── runtime/
│   ├── tasks/
│   ├── downloader/
│   ├── parser/
│   ├── chunker/
│   ├── embeddings/
│   └── storage/
│
├── brixta_sdk/
│   ├── context.py
│   ├── downloader.py
│   ├── parser.py
│   ├── chunker.py
│   ├── embedding.py
│   └── storage.py
│
├── plugins/
│   ├── downloader/
│   ├── parser/
│   ├── chunker/
│   ├── embedding/
│   └── storage/
│
├── core/
│   ├── plugin_loader.py
│   ├── config.py
|   ├── constants.py
|   ├── enums.py
|   ├── exceptions.py
│   └── database.py
│
├── storage/
├── infra/
├── k8s/
└── README.md
```

---

## Core Components
- API
- Runtime
- SDK
- Plugin Loader
- Official Plugins
- Artifact Repository
- Infrastructure

## Technology Stack

| Layer | Technology |
|--------|------------|
| API Runtime | FastAPI |
| Validation | Pydantic |
| Pipeline Runtime | Celery |
| Message Broker | Redis |
| Plugin SDK | BRIXTA SDK |
| Plugin Loader | BRIXTA Plugin Loader |
| Downloader Plugin | Default Downloader |
| Parser Plugin | Docling |
| Chunking Plugin | HybridChunker |
| Embedding Plugin | Nomic Embed v1.5 |
| Storage Plugin | PostgreSQL + pgvector |
| Pipeline Context | BRIXTA PipelineContext |
| Artifact Repository | Local Filesystem *(MinIO Planned)* |
| Relational Database | Neon PostgreSQL |
| Schema Management | Drizzle ORM |
| HTTP Client | Requests |
| Containerization | Docker |
| Local Development | Colima |
| Container Orchestration | Kubernetes (K3s) |
| Secrets Management | Infisical Operator |
---

## Current Progress

- ✅ FastAPI Gateway
- ✅ Neon PostgreSQL
- ✅ Drizzle ORM Schema
- ✅ pgvector Extension
- ✅ Redis Infrastructure
- ✅ Celery Worker Engine
- ✅ Asynchronous Worker Chaining
- ✅ Job Status Tracking
- ✅ HTML/PDF Downloader
- ✅ Docling Parsing
- ✅ Canonical DoclingDocument Serialization
- ✅ Markdown Export
- ✅ Hybrid Semantic Chunking
- ✅ Open-Source Embedding Generation (Nomic Embed v1.5)
- ✅ Automatic Vector Persistence
- ✅ pgvector Storage
- ✅ End-to-End AI Ingestion Pipeline
---

# Design Philosophy

BRIXTA Core follows an **Integration-First** architecture.

Rather than reinventing mature technologies, BRIXTA integrates proven open-source systems through stable interfaces. The core runtime is responsible only for orchestration, pipeline execution, state management, and scheduling. Specialized capabilities such as downloading, parsing, chunking, embedding generation, and storage are implemented as interchangeable plugins.

The runtime never depends on a specific implementation. It depends only on SDK contracts.

```text
                  Runtime
                      │
                      ▼
               Plugin Loader
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
 DownloaderPlugin ParserPlugin StoragePlugin
        │             │             │
        ▼             ▼             ▼
 Default       Docling       PostgreSQL
 Downloader                    + pgvector
```

Core principles:

- Integration over reinvention
- Plugin-first architecture
- Stable SDK contracts
- Single Responsibility Principle
- Configuration over hardcoded implementations
- Asynchronous event-driven execution
- Deterministic processing
- Artifact-driven pipelines
- Vendor-independent architecture
- Horizontally scalable workers

---

# Runtime Architecture

BRIXTA Runtime is responsible for executing pipeline stages, scheduling work, and orchestrating plugins.

```text
Gateway
    │
    ▼
PipelineContext
    │
    ▼
Downloader Plugin
    │
    ▼
Parser Plugin
    │
    ▼
Chunker Plugin
    │
    ▼
Embedding Plugin
    │
    ▼
Storage Plugin
```

Each stage:

- Receives a shared `PipelineContext`
- Performs one responsibility
- Updates the context
- Produces deterministic artifacts
- Dispatches the next stage
- Knows nothing about previous implementations

This keeps the runtime loosely coupled while allowing plugins to evolve independently.

---

# Plugin Architecture

Every capability inside BRIXTA is represented by an SDK interface.

```text
BRIXTA Runtime
       │
       ▼
Plugin Loader
       │
       ▼
BRIXTA SDK Interfaces
       │
       ▼
Official Plugins
       │
       ▼
Open Source Technologies
```

Current official plugins:

| Plugin Type | Current Implementation |
|--------------|------------------------|
| Downloader | Default Downloader |
| Parser | Docling |
| Chunker | HybridChunker |
| Embedding | Nomic Embed v1.5 |
| Storage | PostgreSQL + pgvector |

Because the runtime depends only on SDK contracts, implementations can be replaced without modifying pipeline logic.

---

# Pipeline Context

Every stage receives the same `PipelineContext`.

```text
Gateway
    │
    ▼
PipelineContext
    │
    ▼
Downloader
    │
    ▼
PipelineContext
    │
    ▼
Parser
    │
    ▼
PipelineContext
    │
    ▼
Chunker
    │
    ▼
PipelineContext
    │
    ▼
Embedding
    │
    ▼
PipelineContext
    │
    ▼
Storage
```

The context contains the complete state of a processing job, including source information, generated artifacts, metadata, runtime configuration, and future plugin-specific data.

---

# Artifact Repository

Every pipeline stage produces a permanent artifact.

```text
storage/

raw/
    Downloaded documents

docling/
    Canonical DoclingDocument

markdown/
    Markdown representation

chunks/
    Semantic chunks

embeddings/
    Generated embedding vectors
```

Artifacts enable:

- Pipeline reproducibility
- Independent debugging
- Pipeline inspection
- Incremental reprocessing
- Model upgrades
- Re-embedding without downloading again
- Offline analysis

The filesystem serves as BRIXTA's **Artifact Repository**, while PostgreSQL stores searchable knowledge.

---

# Configuration-Driven Architecture

Infrastructure and plugins are selected through configuration rather than hardcoded implementations.

Examples:

- Downloader Plugin
- Parser Plugin
- Chunking Plugin
- Embedding Plugin
- Storage Plugin
- Logging
- Message Broker
- Future LLM Providers

Development architecture:

```text
MacBook
    │
    ▼
Docker
    │
    ▼
Redis
    │
    ▼
Celery Runtime
    │
    ▼
Official Plugins
```

Production architecture:

```text
Kubernetes
      │
      ▼
Redis
      │
      ▼
Celery Runtime
      │
      ▼
Plugin Loader
      │
      ▼
Official Plugins
      │
      ▼
PostgreSQL + pgvector
```

Because the runtime depends only on SDK interfaces, BRIXTA can evolve from local development to distributed cloud deployments without changing business logic. New plugins, infrastructure providers, and commercial services can be introduced by configuration rather than code changes.

# Why Artifact Storage?

The `storage/` directory is intentionally preserved.

Instead of discarding intermediate processing stages, BRIXTA stores every generated artifact.

This enables:

- Re-chunking without downloading documents again
- Re-generating embeddings with newer models
- Debugging every pipeline stage independently
- Reproducible research ingestion
- Offline inspection of processed documents

The filesystem stores immutable processing artifacts.

Neon PostgreSQL stores searchable knowledge.

---

## Development Commands

### Start Colima

```bash
colima start
```

### Start Redis Container (First Time)

```bash
docker run -d \
  --name brixta-redis \
  -p 6379:6379 \
  redis:7
```

### Start Existing Redis Container

```bash
docker start brixta-redis
```

### Verify Running Containers

```bash
docker ps
```

### Start FastAPI Gateway

```bash
uvicorn api.main:app --reload
```

### Start Celery Worker (macOS Development)

```bash
celery -A runtime.celery_app.celery worker \
    --pool=solo \
    --loglevel=info
```

### Start Celery Worker (Linux / Production)

```bash
celery -A workers.celery_app.celery worker \
    --loglevel=info
```

### Stop Redis

```bash
docker stop brixta-redis
```

### Stop Colima

```bash
colima stop
```

### Remove Stopped Containers & Cache

```bash
docker system prune -f
```

### Remove Everything (Images + Cache + Volumes)

```bash
docker system prune -a --volumes -f
```

---

## Kubernetes Operations (K3s)

The production environment is orchestrated using a lightweight **K3s Kubernetes** cluster with automated secret injection through the **Infisical Operator**.

---

### Start the Cluster

Starts the K3s environment, applies all Kubernetes manifests from the `k8s/` directory, and synchronizes secrets using the Infisical Operator.

The stuff is inside ~/brresea/

```bash
./start.sh
```

---

### Check Cluster Status

View the status of all running pods, deployments, and services.

```bash
kubectl get pods
```

For a more detailed overview:

```bash
kubectl get all
```

---

### View Application Logs

Stream live logs from the running deployments.

#### FastAPI Gateway

```bash
kubectl logs deployment/gateway -f
```

#### Celery Worker (Light)

```bash
kubectl logs deployment/workers-light -f
```

#### Embedding Worker

```bash
kubectl logs deployment/worker-embeddings -f
```

---

### Restart Deployments

Perform a rolling restart without downtime.

```bash
kubectl rollout restart deployment gateway
kubectl rollout restart deployment workers-light
kubectl rollout restart deployment worker-embeddings
```

Or restart all three in one command:

```bash
kubectl rollout restart deployment \
    gateway \
    workers-light \
    worker-embeddings
```

---

### Stop the Cluster

Delete all deployed Kubernetes resources.

```bash
kubectl delete -f k8s/
```

---

## Roadmap

### Phase 1 — BRIXTA Core

The open-source runtime powering the BRIXTA ecosystem.

#### Architecture

- [x] FastAPI API Runtime
- [x] Celery Runtime
- [x] Redis Message Broker
- [x] Kubernetes (K3s) Deployment
- [x] Plugin SDK
- [x] PipelineContext
- [x] Plugin Loader
- [x] Official Plugin Architecture

#### Official Plugins

- [x] Default Downloader
- [x] Docling Parser
- [x] HybridChunker
- [x] Nomic Embed v1.5
- [x] PostgreSQL + pgvector Storage

#### Runtime Improvements

- [ ] Dynamic Plugin Discovery
- [ ] Plugin Configuration (`plugins.yaml`)
- [ ] Retry Policies
- [ ] Dead Letter Queues
- [ ] Connection Pooling (`psycopg_pool`)
- [ ] Metrics API
- [ ] Prometheus Integration
- [ ] Grafana Dashboards
- [ ] OpenTelemetry Tracing
- [ ] Horizontal Pod Autoscaling
- [ ] KEDA Event Scaling

---

### Phase 2 — BRIXTA Platform

Hosted Vector Embeddings as a Service.

- [ ] Authentication
- [ ] API Keys
- [ ] Credits & Usage Metering
- [ ] Billing
- [ ] User Dashboard
- [ ] Organization & Team Workspaces
- [ ] Multi-Tenant Runtime
- [ ] REST API
- [ ] Python SDK
- [ ] JavaScript SDK
- [ ] CLI

---

### Phase 3 — BRIXTA Marketplace

The OpenRouter for Vector Embeddings.

- [ ] Plugin Registry
- [ ] Plugin Installation
- [ ] Plugin Updates
- [ ] Plugin Versioning
- [ ] Plugin Verification
- [ ] Community Plugins
- [ ] Commercial Plugins
- [ ] Revenue Sharing
- [ ] Plugin Marketplace

---

### Phase 4 — BRIXTA Cloud

Managed Infrastructure.

- [ ] Distributed Worker Clusters
- [ ] GPU Compute Pools
- [ ] Autoscaling
- [ ] Managed Storage
- [ ] Distributed Artifact Repository
- [ ] Global API
- [ ] Multi-Region Deployment
- [ ] Enterprise Management

---

### Phase 5 — BRIXTA Ecosystem

Industry-specific embedding solutions built on BRIXTA Core.

- [ ] Document Intelligence
- [ ] Legal AI
- [ ] Medical Knowledge
- [ ] Financial Research
- [ ] Geospatial Embeddings
- [ ] Multimodal Embeddings
- [ ] Image Search
- [ ] Audio Embeddings
- [ ] Video Embeddings
- [ ] Scientific Knowledge Pipelines

---

## Completed

### Runtime

- [x] FastAPI API
- [x] Celery Runtime
- [x] Redis Broker
- [x] Kubernetes Deployment
- [x] Plugin SDK
- [x] PipelineContext
- [x] Plugin Loader
- [x] Integration-First Architecture

### Official Plugins

- [x] Default Downloader
- [x] Docling Parser
- [x] HybridChunker
- [x] Nomic Embed v1.5
- [x] PostgreSQL + pgvector Storage

### Pipeline

- [x] End-to-End Asynchronous Processing
- [x] HTML / PDF Download
- [x] Canonical DoclingDocument Generation
- [x] Markdown Export
- [x] Semantic Chunking
- [x] Embedding Generation
- [x] Vector Persistence
- [x] Artifact Repository
- [x] Production Kubernetes Deployment
- [x] Production Load Testing (k6)