# BRIXTA Research Pipeline

A modular, event-driven research ingestion pipeline designed for scalable document acquisition, parsing, semantic chunking, embedding generation, and vector storage.

---
## Architecture

```text
                               Client
                                  │
                                  ▼
                         FastAPI Gateway
                                  │
                                  ▼
                    Neon PostgreSQL (ingestion_jobs)
                                  │
                                  ▼
                         Redis Message Broker
                                  │
                                  ▼
                          Celery Task Queue
                                  │
                                  ▼
                        Document Downloader
                                  │
                                  ▼
                           storage/raw/
                                  │
                                  ▼
                           Docling Parser
                                  │
          ┌───────────────────────┴───────────────────────┐
          ▼                                               ▼
 storage/docling/                               storage/markdown/
 (Canonical DoclingDocument)                            │
                                                        ▼
                                            Hybrid Chunking Engine
                                                        │
                                                        ▼
                                               storage/chunks/
                                                        │
                                                        ▼
                                           Nomic Embed v1.5 (OSS)
                                                        │
                                                        ▼
                                            storage/embeddings/
                                                        │
                                                        ▼
                                             Storage Persistence
                                                        │
                                                        ▼
                          Neon PostgreSQL (document_chunks + pgvector)
```
---

## Project Structure

BRIXTAresearchPipeline/
├── Resea/                  # Python Virtual Environment
│
├── infra/                  # Drizzle ORM Schema & Infrastructure
│   ├── drizzle/
│   ├── drizzle.config.ts
│   └── schema.ts
│
├── gateway/
│   └── main.py
│
├── shared/
│   ├── config.py
│   ├── constants.py
│   ├── database.py
│   ├── enums.py
│   ├── exceptions.py
│   └── schemas.py
│
├── workers/
│   ├── celery_app.py
│   │
│   ├── tasks/
│   │   ├── ingestion.py
│   │   ├── parser.py
│   │   ├── chunker.py
│   │   ├── embeddings.py
│   │   └── storage.py
│   │
│   ├── downloader/
│   │   └── service.py
│   │
│   ├── parser/
│   │   └── service.py
│   │
│   ├── chunker/
│   │   └── service.py
│   │
│   ├── embeddings/
│   │   └── service.py
│   │
│   ├── storage/
│   │   └── service.py
│   │
│   └── utils/
│       └── job_status.py
│
├── storage/
│   ├── raw/
│   ├── docling/
│   ├── markdown/
│   ├── chunks/
│   └── embeddings/
│
├── .env
├── requirements.txt
└── README.md


---

## Technology Stack

| Layer | Technology |
|--------|------------|
| API | FastAPI |
| Validation | Pydantic |
| Database | Neon PostgreSQL |
| ORM / Schema | Drizzle ORM |
| Queue Broker | Redis |
| Task Queue | Celery |
| Document Parsing | Docling |
| Document Representation | DoclingDocument |
| Chunking | HybridChunker |
| Embeddings | Nomic Embed v1.5 |
| Vector Database | PostgreSQL + pgvector |
| HTTP Client | Requests |
| Container Runtime | Docker + Colima |
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

BRIXTA follows an **Integration-First** architecture.

Instead of reinventing mature technologies, BRIXTA integrates specialized open-source components into a unified research ingestion platform.

Each pipeline stage performs exactly one responsibility and produces a deterministic artifact that can be independently inspected, regenerated, or replaced.

```text
Acquire
    │
    ▼
Normalize
    │
    ▼
Parse
    │
    ▼
Chunk
    │
    ▼
Embed
    │
    ▼
Store
```

Core principles:

- Integration over reinvention
- Single Responsibility Principle
- Configuration over hardcoded implementations
- Asynchronous processing
- Reproducible pipelines
- Vendor-independent architecture
- Deterministic artifacts
- Horizontally scalable workers

---

# Worker Architecture

Every Celery worker performs one responsibility only.

```text
Downloader
      │
      ▼
Parser
      │
      ▼
Chunker
      │
      ▼
Embedding
```

Each worker:

- Receives a single input
- Produces a deterministic output
- Dispatches the next worker
- Does not know how previous stages work

This keeps the pipeline loosely coupled and allows individual stages to evolve independently.

---

# Artifact Pipeline

Every stage produces a permanent artifact.

```text
storage/

raw/
    Original downloaded document

docling/
    Canonical DoclingDocument

markdown/
    Markdown representation

chunks/
    Hybrid semantic chunks

embeddings/
    Embedding vectors
```

Artifacts allow:

- Reproducibility
- Easy debugging
- Pipeline inspection
- Reprocessing
- Model upgrades
- Re-embedding without downloading documents again

The filesystem is treated as BRIXTA's **Artifact Repository**.

---

# Configuration-Driven Architecture

Infrastructure is selected through configuration instead of hardcoded implementations.

Examples:

- PostgreSQL
- Redis
- Embedding Provider
- Embedding Model
- Logging
- Future LLM Providers

Current development configuration:

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
Celery
     │
     ▼
Nomic Embed
```

Production architecture:

```text
Linux
     │
     ▼
Redis Cluster
     │
     ▼
Celery Workers
     │
     ▼
GPU Embedding Workers
     │
     ▼
Neon PostgreSQL (pgvector)
```

Because infrastructure is configuration-driven, BRIXTA can migrate from local development to cloud deployment without changing business logic.

---

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
uvicorn gateway.main:app --reload
```

### Start Celery Worker (macOS Development)

```bash
celery -A workers.celery_app.celery worker \
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

## Roadmap

### Retrieval Layer

- [ ] Semantic Vector Search
- [ ] Semantic Search API
- [ ] Research Retrieval (RAG) API
- [ ] Metadata Filtering
- [ ] Hybrid Retrieval (Vector + BM25)

### Pipeline Improvements

- [ ] Markdown Cleaner
- [ ] Connection Pooling (psycopg_pool)
- [ ] Worker Monitoring (Prometheus)
- [ ] Grafana Dashboards

### User Platform

- [ ] Frontend Dashboard
- [ ] Google Drive / OneDrive Connectors
- [ ] Multi-Tenant Workspace Management

### Infrastructure

- [ ] Docker Compose Deployment
- [ ] Kubernetes Deployment (AWS EKS)
- [ ] Terraform Infrastructure

---

### Completed

- [x] FastAPI Gateway
- [x] Redis + Celery Worker Pipeline
- [x] Document Downloader
- [x] Docling Parsing
- [x] Canonical DoclingDocument Serialization
- [x] Hybrid Semantic Chunking
- [x] Open-Source Embedding Generation (Nomic Embed v1.5)
- [x] Automatic Vector Persistence (pgvector)
- [x] End-to-End AI Ingestion Pipeline