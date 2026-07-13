# BRIXTA

> **The integration-first runtime and control plane for AI data pipelines.**

**Connect anything. Process everything. Control it from one place.**

BRIXTA is not another parser, embedding library, vector database, or RAG framework. It is the orchestration layer around those systems: a stable runtime, plugin contracts, asynchronous pipelines, artifact management, infrastructure controls, and a dashboard that makes the entire system operable.

The long-term goal is straightforward:

> **Become the operating system for AI integrations.**

Today, BRIXTA provides a working ingestion runtime that accepts URLs and files, processes them through selectable plugins, generates model-aware embeddings, stores them in PostgreSQL with pgvector, and exposes operational state through a Next.js dashboard. Retrieval, packaged RAG, MCP serving, marketplace installation, and enterprise hardening are the next major layers—not features that are being claimed as complete today.

---

## Why BRIXTA exists

Connecting enterprise knowledge to AI usually requires teams to assemble and operate many independent tools:

- source connectors and crawlers;
- document parsing and OCR;
- chunking and enrichment;
- embedding providers and local models;
- object and vector storage;
- schedulers, queues, and workers;
- monitoring, logs, and deployment controls;
- retrieval APIs and model integrations.

Those components are useful, but the glue between them becomes a product of its own. BRIXTA owns that glue.

The design rule is:

> **Write the glue, not the world.**

BRIXTA integrates mature systems behind stable contracts instead of recreating them. A pipeline may use Docling today and another parser tomorrow; local Sentence Transformers today and a hosted embedding API tomorrow; pgvector today and another storage backend later. The runtime should not need to be rewritten each time.

---

## Project status

BRIXTA is currently an **end-to-end ingestion MVP and control-plane prototype**.

| Area | Status | What works now |
| --- | --- | --- |
| URL ingestion | Working | Downloads and processes one HTTP seed page |
| File ingestion | Working | Drag-and-drop/API upload for PDF, DOCX, PPTX, XLSX, HTML, Markdown, and text up to 50 MiB |
| Pipeline execution | Working | Celery dispatch across downloader, parser, chunker, embedding, and storage stages |
| Plugin selection | Working | Global defaults plus per-job and per-source overrides |
| Model profiles | Working | Approved model IDs, dimensions, prefixes, revisions, normalization, trust policy, and device policy |
| Parsing and OCR | Working | Docling standard document pipeline with configurable accelerator |
| Embeddings | Working | Sentence Transformers with Nomic, BGE, and E5 profiles |
| Vector persistence | Working | PostgreSQL + pgvector with model and dimension metadata |
| Artifact storage | Working | Local filesystem or MinIO |
| Scheduled sources | Working MVP | Five-field cron expressions checked by Celery Beat once per minute |
| Dashboard | Working MVP | Ingestion, sources, plugins, settings, jobs, health, Docker, Kubernetes, Celery, Redis, and MinIO views |
| Recursive crawling | Not implemented | Source schema anticipates it; current HTTP downloader processes only the seed page |
| Retrieval API | Not implemented | Embeddings are stored, but a search/query service is still required |
| Ready-made RAG | Not implemented | Retrieval, prompt assembly, citations, and generation must be added |
| MCP server | Not implemented | Planned as a first-class integration surface |
| Plugin marketplace | Not implemented | Catalog exists; safe install, update, disable, and uninstall do not |
| Authentication/RBAC | Not implemented | Tenant IDs are metadata, not an authorization boundary |
| Production hardening | In progress | Kubernetes manifests and controls exist, but need security and deployment validation |

### Proven locally

The current pipeline has been exercised end to end with both web and PDF inputs:

```text
Download
  -> Parse with Docling
  -> Hybrid chunk
  -> Generate Nomic embeddings
  -> Persist to pgvector
  -> Mark job completed
```

On macOS, Docling and embedding workers should default to CPU. Apple MPS can abort inside Celery prefork workers; use a dedicated non-forking worker only when explicitly testing MPS.

---

## Architecture

```mermaid
flowchart TD
    A["Dashboard / API client"] --> B["FastAPI gateway"]
    B --> C["PipelineContext"]
    C --> D["Celery + Redis runtime"]
    D --> E["Plugin registry and loader"]
    E --> F["Downloader"]
    F --> G["Parser"]
    G --> H["Chunker"]
    H --> I["Embedding"]
    I --> J["Storage"]
    F --> K["Artifact repository"]
    G --> K
    H --> K
    I --> K
    K --> L["Local filesystem / MinIO"]
    J --> M["PostgreSQL + pgvector"]
```

### The execution contract

Every job is represented by a serializable `PipelineContext`. It carries:

- job and tenant identity;
- source type and target;
- selected plugin IDs;
- runtime configuration and pipeline order;
- artifact paths;
- extensible metadata.

Each plugin receives the context, performs one responsibility, enriches the context, and returns it. Celery serializes the context between queues, so stages remain independently deployable.

### Default event flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Redis
    participant Worker
    participant Artifacts
    participant Postgres

    Client->>API: Submit URL or file
    API->>Redis: Queue downloader task
    Redis->>Worker: Dispatch configured stages
    Worker->>Artifacts: Save raw, parsed, chunks, embeddings
    Worker->>Postgres: Persist job state and vectors
    Worker-->>Redis: Complete pipeline
```

The default order is:

```text
downloader -> parser -> chunker -> embedding -> storage
```

The control plane can persist a different order for the middle stages, but the installed official plugins currently depend on artifacts produced by the default order. Until BRIXTA has typed input/output contracts and DAG validation, the default order is the only guaranteed-compatible order.

---

## Core components

| Component | Responsibility |
| --- | --- |
| FastAPI gateway | Accept ingestion requests and expose control-plane APIs |
| `PipelineContext` | Stable serialized contract shared across every stage |
| BRIXTA SDK | Abstract interfaces implemented by plugins |
| Plugin registry | Declare IDs, stages, capabilities, entrypoints, defaults, and model profiles |
| Plugin loader | Validate selections and lazily import runtime implementations |
| Celery runtime | Execute pipeline stages asynchronously |
| Redis | Broker, result backend, queue inspection, and scheduler transport |
| Job repository | Persist job lifecycle and failure messages |
| Artifact repository | Provide one interface over local or MinIO artifacts |
| PostgreSQL + pgvector | Store jobs, chunks, model metadata, and vectors |
| Source scheduler | Persist reusable sources and dispatch due cron schedules |
| Production API | Expose health, workers, queues, containers, pods, logs, and settings |
| BRIXTA Dashboard | Mission Control for ingestion, sources, plugins, and infrastructure |

---

## Current plugin catalog

| Stage | Plugin ID | Implementation | Capabilities |
| --- | --- | --- | --- |
| Downloader | `http` | HTTP Downloader | URL/HTML seed-page ingestion |
| Downloader | `local-file` | Local File | Uploaded PDF, office, HTML, Markdown, and text files |
| Parser | `docling` | Docling Parser | HTML, PDF, office formats, OCR |
| Chunker | `docling-hybrid` | Docling Hybrid Chunker | Structure-aware contextual chunks |
| Embedding | `sentence-transformers` | Sentence Transformers | Local approved models |
| Storage | `pgvector` | PostgreSQL + pgvector | Vector and metadata persistence |

### Approved embedding profiles

| Model | Dimensions | Document prefix | Query prefix | Default device |
| --- | ---: | --- | --- | --- |
| `nomic-ai/nomic-embed-text-v1.5` | 768 | `search_document: ` | `search_query: ` | CPU |
| `BAAI/bge-large-en-v1.5` | 1024 | — | — | CPU |
| `intfloat/e5-large-v2` | 1024 | `passage: ` | `query: ` | CPU |

Model IDs are not accepted arbitrarily. They must be declared by the selected embedding plugin. A model profile controls dimensions, prefixes, normalization, pinned revision, remote-code policy, and allowed devices. Public plugin responses intentionally omit the internal `trust_remote_code` flag.

---

## Why the system is modular

BRIXTA's modularity comes from several boundaries working together:

1. **Stable interfaces** — every stage implements one SDK abstract class.
2. **Stable identifiers** — jobs select plugin IDs, not Python imports.
3. **Lazy entrypoints** — heavy libraries are loaded only inside the worker that needs them.
4. **Shared context** — plugins exchange a known contract rather than directly calling each other.
5. **Artifact boundaries** — intermediate results live behind an artifact repository.
6. **Per-job selection** — two jobs can use different registered implementations without changing runtime code.
7. **Model profiles** — model-specific behavior is metadata, not scattered `if model == ...` branches.
8. **Runtime separation** — queues allow light stages and ML-heavy stages to scale independently.

This is source-level modularity today. Dynamic package installation is intentionally not implemented yet; installed plugins are registered by trusted code at startup.

---

## Repository layout

```text
.
├── api/
│   ├── main.py                 # Ingestion API and plugin catalog
│   ├── sources.py              # Reusable sources and schedules
│   └── prod_api/               # Runtime and infrastructure control plane
├── brixta_sdk/
│   ├── context.py              # PipelineContext
│   ├── downloader.py
│   ├── parser.py
│   ├── chunker.py
│   ├── embedding.py
│   └── storage.py
├── core/
│   ├── config.py               # Environment-backed runtime config
│   ├── database.py
│   ├── enums.py
│   ├── exceptions.py
│   └── plugin_loader.py        # Registry, model profiles, lazy loader
├── plugins/
│   ├── downloader/
│   ├── parser/
│   ├── chunker/
│   ├── embedding/
│   └── storage/
├── runtime/
│   ├── artifacts/              # Local and MinIO backends
│   ├── jobs/
│   ├── parser/
│   ├── settings/
│   ├── sources/
│   ├── storage/
│   ├── tasks/                  # Celery stage tasks and dispatch flow
│   └── celery_app.py
├── brixta-dashboard/           # Next.js Mission Control
├── infra/                      # Drizzle schema and migrations
├── k8s/                        # Kubernetes workloads and RBAC
├── storage/                    # Local artifacts and control-plane state
├── tests/
├── requirements-api.txt
├── requirements-workers.txt
└── Dockerfile
```

---

## Local development

### Prerequisites

- Python 3.11 or 3.12;
- Node.js and npm;
- PostgreSQL with pgvector, or a hosted pgvector-compatible PostgreSQL service;
- Redis;
- Docker Desktop if using MinIO or the Docker control page.

Python 3.9 is unsupported because the codebase uses modern union annotations such as `Path | None`. Python 3.14 is not the recommended target for the current ML dependency stack. Python 3.11 and the Dockerfile's Python 3.12 are the supported development choices.

### 1. Create the environment

```bash
python3.11 -m venv Resea
source Resea/bin/activate
python -m pip install --upgrade pip
```

For a full local worker environment:

```bash
pip install -r requirements-workers.txt
```

For an API-only environment:

```bash
pip install -r requirements-api.txt
```

The root `requirements.txt` is a legacy environment snapshot. It contains platform-specific exact pins and should not be used as the supported installation path.

### 2. Configure environment variables

Create `.env` in the repository root:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require
REDIS_URL=redis://localhost:6379/0

ARTIFACT_BACKEND=local

EMBEDDING_PLUGIN=sentence-transformers
EMBEDDING_MODEL=nomic-ai/nomic-embed-text-v1.5

BRIXTA_DOCLING_DEVICE=cpu
BRIXTA_DOCLING_THREADS=4

LOG_LEVEL=INFO
```

Optional MinIO settings:

```env
ARTIFACT_BACKEND=minio
MINIO_ENDPOINT=localhost:9000
MINIO_CONSOLE_URL=http://localhost:9001
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=change-this-password
MINIO_BUCKET=brixta
MINIO_SECURE=false
```

An optional `HF_TOKEN` increases Hugging Face rate limits. Never commit `.env`, tokens, database URLs, or MinIO credentials.

### 3. Start Redis

Use an existing Redis service or run:

```bash
docker run -d --name brixta-redis -p 6379:6379 redis:7-alpine
```

For an existing container:

```bash
docker start brixta-redis
```

### 4. Start MinIO when selected

```bash
docker run -d \
  --name brixta-minio \
  -p 9000:9000 \
  -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=change-this-password \
  -v ~/minio-data:/data \
  quay.io/minio/minio \
  server /data --console-address :9001
```

Open `http://localhost:9001` for the MinIO console.

### 5. Apply the database schema

```bash
cd infra
npm install
npm run db:push
cd ..
```

The current `document_chunks.embedding` column is an unconstrained pgvector `vector`. Each row also stores `embedding_model` and `embedding_dimension`, allowing approved models with different dimensions to coexist. Retrieval queries must filter by both fields before comparing vectors.

### 6. Start the API

```bash
uvicorn api.main:app --reload
```

API documentation is available at `http://127.0.0.1:8000/docs`.

### 7. Start the worker

For the simplest local setup, run one worker that consumes every configured queue:

```bash
python -m celery -A runtime.celery_app.celery worker --loglevel=info
```

Start the scheduler in another terminal when using cron sources:

```bash
python -m celery -A runtime.celery_app.celery beat --loglevel=info
```

### 8. Start the dashboard

```bash
cd brixta-dashboard
npm install
npm run dev
```

Open `http://localhost:3000`. The dashboard proxies browser requests through `/api/core` to `PYTHON_BACKEND_URL`, which defaults to `http://127.0.0.1:8000`.

---

## Running ingestion

### URL

```bash
curl -X POST http://127.0.0.1:8000/ingest \
  -H 'Content-Type: application/json' \
  -d '{
    "source_url": "https://example.com",
    "tenant_id": "demo",
    "plugins": {
      "downloader": "http",
      "parser": "docling",
      "chunker": "docling-hybrid",
      "embedding": "sentence-transformers",
      "storage": "pgvector"
    },
    "config": {
      "embedding_model": "nomic-ai/nomic-embed-text-v1.5"
    }
  }'
```

The current HTTP plugin downloads only the supplied page. Recursive and sitemap behavior require future crawler plugins.

### File

```bash
curl -X POST http://127.0.0.1:8000/ingest/file \
  -F 'file=@./document.pdf' \
  -F 'tenant_id=demo' \
  -F 'parser=docling' \
  -F 'chunker=docling-hybrid' \
  -F 'embedding=sentence-transformers' \
  -F 'storage=pgvector' \
  -F 'embedding_model=nomic-ai/nomic-embed-text-v1.5'
```

### Discover installed plugins

```bash
curl http://127.0.0.1:8000/plugins
curl 'http://127.0.0.1:8000/plugins?stage=embedding'
```

Unknown plugin IDs and unapproved model IDs are rejected before dispatch.

---

## Sources and cron schedules

Reusable sources are managed through `/sources`. The MVP repository stores definitions in `storage/control-plane/sources.json`; that keeps self-hosted development simple, but it is not suitable for a multi-replica cloud control plane.

Create a scheduled source:

```bash
curl -X POST http://127.0.0.1:8000/sources \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Product docs",
    "tenant_id": "demo",
    "start_url": "https://docs.example.com/start",
    "crawl_strategy": "single_page",
    "schedule_enabled": true,
    "cron_expression": "0 */6 * * *",
    "timezone": "Asia/Kolkata",
    "plugins": {},
    "config": {
      "embedding_model": "nomic-ai/nomic-embed-text-v1.5"
    }
  }'
```

Sync immediately:

```bash
curl -X POST http://127.0.0.1:8000/sources/SOURCE_ID/sync
```

Celery Beat checks due schedules once per minute. Cron expressions must contain five fields. Invalid cron expressions and timezones are logged and skipped.

---

## Dashboard and control plane

The dashboard is operational Mission Control, not a mock-only UI.

| Page | Current behavior |
| --- | --- |
| Dashboard | Shows API, Celery, Redis, artifact storage, Docker, and Kubernetes availability |
| Ingestion | URL/file modes, drag-and-drop, per-stage selectors, embedding model selector |
| Sources | Create, schedule, sync, list, and delete reusable sources |
| Plugins | Displays installed registry entries, capabilities, versions, defaults, and models |
| Settings | Select default plugins/model, configure artifact backend, and reorder middle stages |
| Celery | Workers plus active, reserved, scheduled tasks and persisted jobs |
| Redis | Broker health and queue depths |
| Storage | Active backend, MinIO objects, bucket, endpoint, and console link |
| Docker | Container status, logs, and restart controls |
| Kubernetes | Deployments, pods, logs, and rolling restart controls |
| Health | Database, Redis, storage, and Kubernetes checks |
| Marketplace | Honest placeholder describing the missing lifecycle guarantees |

Docker and Kubernetes mutation endpoints are powerful. They must be placed behind authentication, authorization, an allowlist, and audit logging before any internet-facing deployment.

Kubernetes views use local kubeconfig during development and an in-cluster service account when deployed. The supplied RBAC permits pod/deployment reads, pod logs, and deployment patches for rolling restart.

---

## Developer guide: building plugins

### Plugin lifecycle today

The current lifecycle is code-driven:

```text
Implement SDK class
  -> add module
  -> register PluginSpec
  -> install dependency
  -> test
  -> restart API/workers
  -> plugin appears in /plugins and dashboard selectors
```

There is no safe runtime package installer yet. The dashboard deliberately does not pretend that install/delete is available.

### 1. Choose the stage contract

Implement exactly one of:

- `DownloaderPlugin.download(context)`
- `ParserPlugin.parse(context)`
- `ChunkerPlugin.chunk(context)`
- `EmbeddingPlugin.embed(context, model, profile)`
- `StoragePlugin.persist(context)`

### 2. Add the implementation

Example downloader:

```python
from pathlib import Path

from brixta_sdk.context import PipelineContext
from brixta_sdk.downloader import DownloaderPlugin
from runtime.artifacts.repository import ArtifactRepository


class ExampleDownloaderPlugin(DownloaderPlugin):
    name = "Example Downloader"
    version = "1.0.0"
    source_types = ["url"]

    def download(self, context: PipelineContext) -> PipelineContext:
        if context.source_type != "url":
            raise ValueError(f"Unsupported source type: {context.source_type}")

        data = fetch_from_your_provider(context.source_target)
        ArtifactRepository.save_raw(context.job_id, data)
        context.raw_path = Path(f"raw/{context.job_id}.html")
        return context
```

Place it under the matching stage, for example:

```text
plugins/downloader/example.py
```

### 3. Register the plugin

Add a `PluginSpec` in `core/plugin_loader.py`:

```python
registry.register(
    PluginSpec(
        id="example",
        stage="downloader",
        name="Example Downloader",
        version="1.0.0",
        entrypoint="plugins.downloader.example:ExampleDownloaderPlugin",
        capabilities=("url",),
    )
)
```

Plugin IDs must be unique within a stage. Only one plugin per stage may be marked `default=True`.

### 4. Register embedding models safely

Embedding plugins declare approved models with `ModelSpec`:

```python
ModelSpec(
    id="provider/model-name",
    dimensions=1024,
    document_prefix="passage: ",
    query_prefix="query: ",
    normalize=True,
    trust_remote_code=False,
    revision="PINNED_COMMIT_OR_TAG",
    device="cpu",
    allowed_devices=("cpu",),
    default=False,
)
```

Do not infer trust from a model-name conditional. Remote code, revisions, dimensions, prefixes, and devices belong in an approved profile. Pin externally loaded code and review it before approval.

### 5. Add dependencies in the correct layer

- API/control-plane dependency: `requirements-api.txt`
- parser/embedding/worker dependency: `requirements-workers.txt`
- dashboard dependency: `brixta-dashboard/package.json`
- schema tooling dependency: `infra/package.json`

Avoid adding new exact pins to the legacy root snapshot as the primary installation mechanism.

### 6. Test the plugin

At minimum, test:

- registry discovery;
- default resolution;
- per-job override;
- unsupported source or model rejection;
- artifact creation;
- output shape and declared dimensions;
- failure behavior;
- one end-to-end job.

Run the current tests:

```bash
python -m compileall -q api brixta_sdk core plugins runtime tests
python -m unittest discover -s tests -v
```

### Renaming or moving a plugin

To move a Python module without changing its public identity:

1. move the implementation file;
2. update `PluginSpec.entrypoint`;
3. keep the same plugin `id` so saved jobs and sources remain valid;
4. update imports and tests;
5. restart API and workers.

Changing the plugin ID is a breaking configuration change. Migrate saved source definitions and control-plane defaults before removing the old ID.

A plugin cannot simply be moved to another stage. Stage contracts are different; moving from parser to chunker, for example, requires implementing `ChunkerPlugin` and producing the artifact expected by the next stage.

### Removing a plugin safely

1. If it is the default, register another default first.
2. Search saved settings and `storage/control-plane/sources.json` for its ID.
3. Migrate those selections to a replacement.
4. Remove its `registry.register(...)` declaration.
5. Remove the implementation and unused dependencies.
6. Update tests and documentation.
7. Restart API and workers.

Removing an ID while saved sources still reference it causes validation failure—which is safer than silently substituting a different implementation.

### Changing pipeline order

The settings page can drag parser, chunker, and embedding while downloader remains first and storage remains last. This is an orchestration capability, not proof that every order is semantically valid. A plugin must receive the artifact type it expects. Typed artifact contracts and DAG validation are planned before arbitrary workflow graphs are considered production-ready.

---

## Developer guide: extending the runtime

### Add a new task

1. Add a task module under `runtime/tasks/`.
2. Decorate the function with the shared Celery application.
3. Add its module to `celery.conf.imports`.
4. Add an explicit task route and queue.
5. Add dispatch logic in `runtime/tasks/flow.py` if it is a pipeline stage.
6. Add a worker deployment or update an existing worker queue list.
7. Define status transitions and failure recording.

If adding an entirely new stage, also update:

- `PLUGIN_STAGES`;
- the SDK contract;
- registry validation;
- `PipelineContext` where required;
- the dashboard's `PluginStage` type and selectors;
- settings validation;
- tests and deployment manifests.

### Add a new artifact type or backend

For a new artifact type:

1. extend `ArtifactBackend`;
2. implement it in both local and MinIO backends;
3. expose it through `ArtifactRepository`;
4. update artifact status APIs and tests.

For a new backend such as S3, R2, or Azure Blob:

1. implement the full `ArtifactBackend` contract;
2. select it from configuration;
3. keep credentials outside API responses;
4. implement health and non-sensitive `info()`;
5. verify all workers share the same backend configuration.

### Add a production API

Add the implementation under `api/prod_api/`, then expose a thin route in `api/prod_api/router.py`. Read-only endpoints should return actionable health information without secrets. Mutation endpoints require authentication, authorization, validation, audit history, and a narrow target allowlist before production exposure.

### Add persistent control-plane state

The source and settings repositories currently use local JSON files. Replace their narrow repository interfaces with PostgreSQL implementations before horizontal API scaling. Keep the API and scheduler dependent on repository methods rather than direct file access.

---

## From ingestion to ready-made RAG

BRIXTA currently completes the **indexing half** of RAG:

```text
source -> parse -> chunk -> embed -> store
```

A ready-made RAG service adds:

```text
question -> query embedding -> filtered vector search -> context assembly -> LLM -> cited answer
```

### Required retrieval invariants

Every search must filter by:

- `tenant_id`;
- `embedding_model`;
- `embedding_dimension`.

Vectors produced by different models or dimensions must never be compared. The query must use the same profile and its `query_prefix`; documents use the profile's `document_prefix`.

### Retrieval SQL

After generating a query vector with the selected model profile:

```sql
SELECT
    id,
    job_id,
    chunk_index,
    content,
    embedding <=> %(query_vector)s::vector AS distance
FROM "BrResearch".document_chunks
WHERE tenant_id = %(tenant_id)s
  AND embedding_model = %(embedding_model)s
  AND embedding_dimension = %(embedding_dimension)s
ORDER BY embedding <=> %(query_vector)s::vector
LIMIT %(limit)s;
```

For scale, create model/dimension-specific partial or expression vector indexes. A single unconstrained `vector` column cannot use one ordinary fixed-dimension ANN index for every model shape.

### Recommended BRIXTA RAG layer

Add these components:

```text
runtime/retrieval/service.py     # query embedding and pgvector search
api/query.py                     # authenticated retrieval/RAG endpoints
brixta_sdk/generation.py         # optional generation provider contract
plugins/generation/              # OpenAI, local, or other LLM providers
runtime/citations/               # source and chunk attribution
mcp/                             # BRIXTA MCP server
```

The first useful API can be:

```text
POST /query/search   -> retrieved chunks only
POST /query/answer   -> generated answer plus citations
```

Keep retrieval separate from generation. That allows BRIXTA to serve search results to ChatGPT, another model, an agent framework, or a custom application without forcing a particular LLM.

### MCP integration target

An MCP server should expose narrow tools such as:

- `brixta_search(query, tenant_id, source_ids?, limit?)`
- `brixta_get_chunk(chunk_id)`
- `brixta_list_sources(tenant_id)`
- `brixta_sync_source(source_id)`

The MCP layer must authenticate the caller and derive tenant access from authorization—not trust a tenant ID supplied by the model. Search results should include document identity, chunk identity, source URL/file metadata, and relevance score so the model can cite evidence.

### Connecting another application today

Until the retrieval API exists, an application can:

1. select an approved model profile;
2. generate a normalized query vector using the profile's query prefix;
3. execute the filtered SQL above;
4. assemble the top chunks into a prompt;
5. send that prompt to the LLM of choice;
6. return chunk/job references as citations.

That path works, but the goal is to make it a supported BRIXTA service instead of application-specific glue.

---

## Self-hosting and deployment

### Current modes

- **Local development:** API, Celery, Beat, Redis, PostgreSQL, optional MinIO, and dashboard.
- **Docker image:** a current single image exists, but dependency layering should be split before production optimization.
- **Kubernetes:** manifests exist for gateway, workers, scheduler, Redis, MinIO, PVC, autoscaling, migrations, secrets, and control-plane RBAC.

### Kubernetes control behavior

The gateway uses local kubeconfig during development and in-cluster configuration in Kubernetes. The dashboard can list pods/deployments, read recent pod logs, and request a rolling deployment restart by patching a pod-template annotation.

Before production:

- replace development image references and hard-coded MinIO credentials;
- apply least-privilege namespace-scoped RBAC where possible;
- verify `REDIS_URL` consistently across all workloads;
- separate API, parser, embedding, and migration images/dependencies;
- add readiness/liveness probes;
- validate scheduler and RBAC deployment in the release path;
- add network policies, TLS, ingress, authentication, and audit logs;
- convert manifests into versioned Helm charts or an operator.

---

## Security boundaries

The current repository is a development-stage system. Do not expose it directly to untrusted networks.

Known security work:

- authenticate API and dashboard users;
- enforce tenant authorization server-side;
- protect Docker restart/log access;
- protect Kubernetes log/restart access;
- prevent arbitrary internal URL access in the HTTP downloader (SSRF controls);
- validate uploaded content beyond filename extensions;
- add malware scanning and document sandboxing;
- sign and verify plugin packages;
- isolate plugin execution and dependency installation;
- encrypt secrets and remove development credentials;
- add rate limiting, quotas, audit trails, and retention policies;
- review all models that require remote code and pin every executable revision.

`tenant_id` currently partitions records logically; it is not an authentication or authorization mechanism.

---

## Current technical debt and limitations

- HTTP ingestion is single-page, not a complete crawler.
- `SourceRepository` and runtime settings use local files.
- Only the downloader task currently has automatic retry configuration.
- Pipeline cancellation, pause/resume, and stage replay are not implemented.
- Job records lack full timestamps, progress percentages, and attempt history.
- Deduplication, content hashing, incremental sync, and deletion propagation are not implemented.
- Query/retrieval and vector indexes are not implemented.
- Plugin package installation and dependency isolation are not implemented.
- Dashboard login is not backed by a completed authentication system.
- Control-plane mutation APIs are not production-safe without auth and audit.
- Kubernetes manifests require release engineering and configuration cleanup.
- The root frozen requirements file and current all-in-one Docker build need replacement with reproducible layered builds.
- Metrics, tracing, alerting, and SLOs are not yet integrated.

These are roadmap items, not hidden capabilities.

---

## Roadmap

### Phase 1 — Stabilize the ingestion runtime

- explicit and tested queue topology;
- idempotent stage execution and retries for every stage;
- job timestamps, attempts, progress, cancellation, and replay;
- database-backed sources and settings;
- content hashing, deduplication, incremental sync, and deletion handling;
- reproducible dependency locks and separate API/worker images;
- comprehensive unit, contract, integration, and end-to-end tests.

### Phase 2 — Ship retrieval and RAG

- query embedding contract;
- tenant/model/dimension-safe pgvector retrieval;
- hybrid lexical + vector search;
- metadata filters, reranking, and citations;
- `/query/search` and `/query/answer` APIs;
- provider-agnostic generation plugins;
- MCP server for ChatGPT and other clients;
- evaluation datasets and retrieval quality metrics.

### Phase 3 — Real connectors and crawling

- recursive and sitemap crawler plugins;
- robots.txt, rate limits, canonical URLs, and crawl budgets;
- GitHub, Google Drive, Slack, SharePoint, S3, Notion, email, and database connectors;
- webhooks and change-data capture;
- connector credentials, scopes, and sync cursors;
- OCR, translation, cleaning, enrichment, and PII plugins.

### Phase 4 — Plugin SDK and marketplace

- versioned plugin manifest specification;
- `brixta create-plugin` scaffolding CLI;
- isolated dependencies and execution environments;
- compatibility and capability validation;
- signing, provenance, permissions, and vulnerability scanning;
- install, enable, disable, update, rollback, and uninstall;
- marketplace publishing and licensing.

### Phase 5 — Production control plane

- authentication, SSO, users, teams, projects, and RBAC;
- secrets manager integrations;
- OpenTelemetry, Prometheus, Grafana, structured logs, and alerts;
- Helm chart and Kubernetes operator;
- autoscaling by queue depth and resource profile;
- backup, restore, retention, quotas, and billing controls;
- self-hosted and managed-cloud parity.

### Phase 6 — AI integration operating system

- visual DAG pipeline builder;
- typed artifacts and compatibility-aware composition;
- reusable pipeline templates and environments;
- agent/workspace actions backed by BRIXTA knowledge;
- fine-tuning dataset preparation and evaluation workflows;
- local and hosted compute routing based on cost, privacy, and latency;
- enterprise marketplace for AI data and action integrations.

---

## Engineering principles

- **Integration first:** prefer stable adapters over rebuilding mature systems.
- **Plugin first:** product capabilities should be replaceable implementations.
- **OSS first:** self-hosting and inspectability are core product qualities.
- **Vendor agnostic:** providers are choices, not architectural dependencies.
- **Event driven:** long-running work belongs in observable asynchronous jobs.
- **Operational by design:** logs, status, retries, storage, and workers are part of the product.
- **Secure by default:** powerful infrastructure controls require narrow permissions and auditability.
- **Truthful interfaces:** unfinished lifecycle operations are labeled unfinished rather than represented by fake buttons.

---

## Contributing

Before opening a change:

```bash
python -m compileall -q api brixta_sdk core plugins runtime tests
python -m unittest discover -s tests -v

cd brixta-dashboard
npm run lint
npm run build
```

For plugin changes, document the contract, capabilities, dependencies, security requirements, failure modes, and supported runtime profiles. For schema changes, include a migration and an upgrade path for existing installations.

---

## The destination

The default BRIXTA pipeline is currently:

```text
Download -> Parse -> Chunk -> Embed -> Store
```

That pipeline is not the final product. It is the first useful workflow running on the product.

The destination is a stable runtime, plugin ecosystem, SDK, control plane, marketplace, and integration surface that can connect almost any source to AI workflows.

> **Need to connect enterprise data to AI? Deploy BRIXTA.**