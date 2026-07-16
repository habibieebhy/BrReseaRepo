# BRIXTA

> **The integration-first operating system for AI data pipelines and deterministic engineering simulations.**

BRIXTA connects data sources, processes documents, creates model-aware vector knowledge bases, exposes those knowledge bases to AI clients through a shared MCP gateway, and runs validated simulation packs through isolated solver workers.

Its default ingestion pipeline is:

```text
source -> download -> parse -> chunk -> embed -> persist -> retrieve
```

That pipeline is only one workload on the larger platform. BRIXTA's durable product boundary is the combination of:

- a stable API and Celery runtime;
- a registry-driven plugin system;
- PostgreSQL/pgvector knowledge storage;
- MinIO artifact storage;
- recurring source synchronization;
- a shared, tenant-scoped MCP gateway;
- a dashboard and CLI;
- deterministic simulation packs;
- Docker and Kubernetes deployment surfaces.

BRIXTA follows one rule: **write the glue, not the world**. Docling parses, Sentence Transformers embeds, pgvector retrieves, MinIO stores artifacts, Celery schedules work, FastMCP exposes tools, OpenFOAM and CalculiX solve engineering cases. BRIXTA validates, composes, scopes, operates, and observes those systems.

---

## Documentation status and release truth

This README describes the repository as it exists now. Labels have precise meanings:

| Label | Meaning |
|---|---|
| **Implemented** | Code exists in this repository and can be exercised when its dependencies are running. |
| **Development-only** | Useful locally but intentionally unsuitable as a production security or availability boundary. |
| **Production-required** | Architecture or configuration that must be supplied before exposing BRIXTA publicly. |
| **Not implemented** | A planned capability; do not sell or depend on it yet. |
| **Release blocker** | Fix before treating the current repository as a production release. |

### Current maturity at a glance

| Area | State | Important truth |
|---|---|---|
| URL and file ingestion | Implemented | URL ingestion fetches one page. Recursive and sitemap crawling are represented in source configuration but are not implemented by the current downloader. |
| Plugin selection | Implemented | Users can select registered plugins/models per job. Pipeline stage order remains fixed. |
| Scheduled synchronization | Implemented, single-control-plane | Celery Beat dispatches five-field cron schedules. Source definitions are JSON files, not a shared database. |
| Vector knowledge bases | Implemented | Completed jobs with persisted chunks become searchable knowledge bases. |
| Semantic retrieval | Implemented | Retrieval preserves embedding model, dimension, tenant, and knowledge-base scope. It is exact pgvector search; no ANN index exists yet. |
| Shared MCP gateway | Implemented | Seven tools are exposed. Local OAuth and quick tunnels are development conveniences; production needs stable HTTPS and a real identity provider. |
| ChatGPT connection | Implemented for developer testing | A user must perform ChatGPT's one-time consent. BRIXTA cannot silently sign in, create a ChatGPT app, or approve by email. Public distribution requires plugin submission. |
| Generic MCP clients | Implemented locally | `brixta connect client --local` exposes a loopback-only gateway. The selected client/model must support tool calling. |
| Dashboard | Implemented prototype | Operational pages exist. Authentication and authorization are not enabled. Do not expose Docker controls or tenant APIs publicly. |
| CalculiX simulation | Implemented preview + solver path | Deterministic structural coupon pack. Solver mode requires the dedicated worker image. |
| OpenFOAM simulation | Implemented preview + solver path | Deterministic channel-flow case compiler. JSON is compiled into an OpenFOAM case; OpenFOAM does not open the JSON directly. |
| Kubernetes manifests | Deployment skeleton | Useful foundation, not a finished secure production platform. Several gaps are listed in [Production readiness gates](#production-readiness-gates). |

### Production readiness gates

Do not call the current checkout production-ready until these are addressed:

1. **Rotate exposed credentials.** Any key ever pasted into chat, a ticket, a commit, or a shared ZIP must be considered compromised. Revoke and recreate OpenAI, Neon, Infisical, MinIO, registry, and OAuth credentials. Never reuse example secrets.
2. **Add dashboard/API identity and tenant authorization.** The current login page is a placeholder; API routes accept tenant identifiers from request data. Production must derive tenant and roles from a verified session/token.
3. **Reconcile database migrations.** `infra/schema.ts` contains the current target schema, while the migration history does not fully create all recovery/context columns and contains legacy/duplicate migration numbering. Add a forward-only migration and validate a fresh database.
4. **Fix the Compose PostgreSQL initialization reference.** `docker-compose.yml` mounts `infra/postgres-init.sql`, which is absent from this archive. Use Neon/external PostgreSQL or add a reviewed initializer before relying on Compose PostgreSQL.
5. **Add `PUT` to the Next.js API proxy.** The knowledge-access UI uses `PUT`, but `brixta-dashboard/app/api/core/[...path]/route.ts` currently exports GET/POST/PATCH/DELETE only.
6. **Replace local JSON control-plane state.** Sources and runtime settings are stored under `storage/control-plane`. A multi-replica deployment needs PostgreSQL-backed repositories or another shared transactional control plane.
7. **Use stable production MCP ingress and OAuth/OIDC.** Never use a random `trycloudflare.com` quick-tunnel URL in production.
8. **Use production Redis and object storage.** The included Redis and MinIO manifests use development credentials/configuration and lack production durability/security.
9. **Fix shared filesystem assumptions.** The `local-path` ReadWriteOnce PVC is not a multi-node shared filesystem. Prefer MinIO for artifacts and database-backed state, or provide RWX storage.
10. **Align images and manifests.** The workflow, package, dashboard, MCP, and simulation manifests currently contain different tags/placeholders. Publish immutable image digests and update every workload.
11. **Protect or remove Docker control endpoints.** They can restart containers and read logs. They must never be available to untrusted users.
12. **Add production observability, backups, policies, and tests.** At minimum: structured logs, metrics, alerts, database/PITR verification, object-store lifecycle/backups, NetworkPolicies, RBAC, PDBs, vulnerability scans, and release-gating integration tests.

---

## Table of contents

- [Product model](#product-model)
- [System architecture](#system-architecture)
- [Repository map](#repository-map)
- [Requirements](#requirements)
- [Security first](#security-first)
- [Environment configuration](#environment-configuration)
- [Local installation](#local-installation)
- [Starting the complete local stack](#starting-the-complete-local-stack)
- [Ingestion and knowledge lifecycle](#ingestion-and-knowledge-lifecycle)
- [Plugin system](#plugin-system)
- [Sources, crawling, and schedules](#sources-crawling-and-schedules)
- [Celery runtime, retries, and recovery](#celery-runtime-retries-and-recovery)
- [PostgreSQL, Neon, and pgvector](#postgresql-neon-and-pgvector)
- [Artifacts and MinIO](#artifacts-and-minio)
- [API reference](#api-reference)
- [Dashboard](#dashboard)
- [MCP and AI-client integration](#mcp-and-ai-client-integration)
- [CLI reference](#cli-reference)
- [Simulation Lab](#simulation-lab)
- [Docker images](#docker-images)
- [Kubernetes deployment](#kubernetes-deployment)
- [Infisical and `start.sh`](#infisical-and-startsh)
- [GitHub Actions and releases](#github-actions-and-releases)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [How to extend or remove components](#how-to-extend-or-remove-components)
- [Strengths, weaknesses, and roadmap](#strengths-weaknesses-and-roadmap)
- [When to split the monorepo](#when-to-split-the-monorepo)
- [Contributing](#contributing)
- [Glossary](#glossary)

---

## Product model

### What BRIXTA is

BRIXTA is an integration and operations layer. It gives one control plane to otherwise disconnected components:

```mermaid
flowchart TD
    A[Sources and files] --> B[Ingestion runtime]
    B --> C[Knowledge bases]
    C --> D[HTTP retrieval]
    C --> E[Shared MCP gateway]
    E --> F[ChatGPT or MCP client]
    C --> G[Simulation evidence]
    G --> H[Validated case compiler]
    H --> I[Solver workers]
    I --> J[Reports and artifacts]
```

### What BRIXTA is not

- It is not an LLM.
- It is not a vector database.
- It is not a replacement for Docling, Hugging Face, Celery, MinIO, PostgreSQL, OpenFOAM, or CalculiX.
- It does not currently crawl an entire website.
- It does not currently generate final RAG answers in the API; the connected AI client uses BRIXTA's search/fetch tools to answer.
- It does not currently use `OPENAI_API_KEY` in application code.
- It does not generate or compile arbitrary C++ at simulation runtime.
- It does not make an engineering simulation certified, safe, or physically valid merely because it ran.

### Tenant model

Every ingestion job, chunk, knowledge-base query, access record, and simulation run carries a `tenant_id`. Today that is an application-level boundary. Production must enforce it at the identity, API, database, object-storage, MCP, and audit layers. A request-supplied tenant string is not security.

---

## System architecture

### Runtime topology

```mermaid
flowchart TD
    UI[Next.js dashboard] --> API[FastAPI gateway]
    API --> DB[(PostgreSQL + pgvector)]
    API --> R[(Redis)]
    API --> OBJ[(MinIO)]
    R --> W1[Light workers]
    R --> W2[Embedding worker]
    R --> W3[Simulation workers]
    BEAT[Celery Beat] --> R
    MCP[Shared MCP gateway] --> DB
    MCP --> OBJ
    CLIENT[ChatGPT / MCP client] --> MCP
```

### Ingestion message flow

1. FastAPI validates the request and plugin selection.
2. `JobRepository` persists a replayable `PipelineContext` in PostgreSQL.
3. Celery sends the download task to `downloader`.
4. Each stage updates the job's status/current stage and enqueues the next queue.
5. Heavy embedding work is isolated on the embedding worker.
6. Storage writes chunks and model metadata to pgvector.
7. The job becomes `completed`; it is now eligible to appear as a knowledge base.

The stage order is intentionally invariant:

```text
downloader -> parser -> chunker -> embedding -> storage
```

Modularity means each stage implementation can be selected or replaced without changing the orchestration contract. It does **not** mean the dashboard can arbitrarily reorder stages.

### Data ownership

| Data | Current authority | Production direction |
|---|---|---|
| Jobs, chunks, knowledge access, simulation metadata | PostgreSQL | Keep; add RLS, migrations, audit, backups. |
| Vector embeddings | pgvector | Keep initially; partition/index by model and dimension as scale grows. |
| Uploaded/generated artifacts | Local filesystem or MinIO | Prefer MinIO/S3-compatible storage. |
| Queue state/results | Redis | Use a managed or highly available Redis-compatible service. |
| Source definitions | `storage/control-plane/sources.json` | Move to PostgreSQL before multiple API replicas. |
| Runtime settings | `storage/control-plane/settings.json` and `runtime.env` | Move to versioned database/config service. |
| CLI connection state | `.brixta/connection.json` | Local machine only; never a production authority. |

---

## Repository map

```text
.
├── api/
│   ├── main.py                    FastAPI app, ingestion, file upload, plugin list
│   ├── sources.py                 source/schedule CRUD and manual sync
│   ├── simulations.py             Simulation Lab API
│   ├── mcp_server.py              compatibility entry point for the MCP gateway
│   └── prod_api/                  health, jobs, knowledge, infra and control APIs
├── brixta-dashboard/              Next.js 16 / React 19 dashboard
├── brixta_cli/                    `brixta` command implementation
├── brixta_mcp/
│   ├── auth.py                    none, local OAuth, static token, JWT auth
│   ├── server.py                  shared FastMCP server
│   └── tools/                     knowledge, source and simulation tools
├── brixta_sdk/                    stable plugin and simulation contracts
├── core/                          config, database, registry, enums, retry policy
├── plugins/
│   ├── downloader/                HTTP and local-file adapters
│   ├── parser/                    Docling and engineering text parsers
│   ├── chunker/                   Docling hybrid and text-window chunkers
│   ├── embedding/                 Sentence Transformers adapter/models
│   ├── storage/                   pgvector persistence
│   └── simulation/                compiler, runner and postprocessor plugins
├── runtime/
│   ├── artifacts/                 local/MinIO artifact backends
│   ├── jobs/                      job persistence
│   ├── knowledge/                 manifests, search and chunk retrieval
│   ├── settings/                  local control-plane settings repository
│   ├── sources/                   source repository/service
│   ├── simulations/               case cards, registry, repository and service
│   ├── tasks/                     Celery task graph, schedules, recovery, simulations
│   └── celery_app.py              queues, routing and periodic schedules
├── infra/
│   ├── schema.ts                  current Drizzle target schema
│   ├── drizzle/                   migration history
│   └── package.json               migration commands
├── k8s/                           Kubernetes workload/service/autoscaling manifests
├── scripts/bootstrap-local.sh     local bootstrap helper; see caveat below
├── start.sh                       Infisical-aware Kubernetes bootstrap helper
├── Dockerfile                     API/worker/MCP-capable Python image
├── Dockerfile.openfoam            OpenFOAM simulation worker image
├── Dockerfile.simulations         CalculiX simulation worker image
├── docker-compose.yml             local PostgreSQL, Redis and MinIO
├── pyproject.toml                 Python package/CLI metadata
├── requirements-*.txt             maintained dependency groups
└── tests/                          unit tests for registry, sources, knowledge, recovery
```

Generated/runtime files that should not be committed or shipped include `.env`, `.brixta/`, `.webui_secret_key`, `Resea/`, `node_modules/`, `.next/`, `brixta.egg-info/`, `celerybeat-schedule.db`, `__pycache__/`, local logs, and uploaded artifacts.

---

## Requirements

### Supported development versions

- macOS or Linux. Windows users should use WSL2 for the documented shell workflow.
- Python **3.11, 3.12, or 3.13**. The package declares `>=3.11,<3.14`; Python 3.14 is not supported.
- Node.js 20+ and npm for the dashboard/Drizzle.
- Docker Desktop or Docker Engine with Compose.
- PostgreSQL with the `vector` extension, locally or on Neon.
- Redis.
- MinIO or another S3-compatible object store when `ARTIFACT_BACKEND=minio`.
- `cloudflared` only for local ChatGPT testing.
- `kubectl`, a Kubernetes cluster, an ingress controller, metrics-server, and optionally the Infisical/VPA operators for Kubernetes.

### Dependency groups

| File | Install on | Contains |
|---|---|---|
| `requirements-api.txt` | API, lightweight workers, simulation workers | FastAPI, Celery/Redis, PostgreSQL/pgvector, MinIO, Docker/Kubernetes clients. |
| `requirements-workers.txt` | document and embedding workers | API dependencies plus Docling and Sentence Transformers. |
| `requirements-rag.txt` | retrieval API/MCP/CLI host | API dependencies plus Sentence Transformers, `einops`, and FastMCP. |
| `requirements.txt` | Historical only | A platform-specific freeze that has previously produced incompatible NumPy/Transformers/Docling combinations. Do not use as the canonical clean install. |

`pyproject.toml` installs the `brixta` command and local packages, but intentionally does not declare the heavyweight runtime dependency groups. Install the appropriate requirements first, then install the project editable.

---

## Security first

### Rotate secrets before deployment

If a real credential appeared in a previous README, screenshot, shell transcript, chat, ZIP, Git history, or CI log, rotate it now. At minimum review:

- `OPENAI_API_KEY`;
- `DATABASE_URL`/Neon password;
- Infisical machine-identity client ID and secret;
- MinIO root/application keys;
- container-registry credentials;
- OAuth/JWT signing keys and tokens;
- Kubernetes Secrets and TLS private keys.

Use `git log -p`, GitHub secret scanning, and the provider's audit/revocation UI. Removing a secret from the current file does not remove it from Git history.

### Never commit

```gitignore
.env
.env.*
!.env.example
.brixta/
.webui_secret_key
Resea/
node_modules/
.next/
*.egg-info/
celerybeat-schedule.db
storage/uploads/
storage/control-plane/runtime.env
*.log
```

### Public exposure rules

- Do not expose the current dashboard/API until login, RBAC, tenant derivation, CSRF/session protection, rate limits, and audit logging exist.
- Never expose the Docker control endpoints to ordinary users.
- Run MCP with `jwt` auth in production, not `none` or ephemeral `oauth-local`.
- Store secrets in Infisical, External Secrets, Vault, a cloud secret manager, or sealed secrets—not plaintext Git manifests.
- Use separate MinIO application credentials with minimum bucket permissions. Do not use root credentials in application workloads.
- Use TLS to PostgreSQL, Redis where supported, MinIO, dashboard, API, and MCP.

---

## Environment configuration

BRIXTA loads `storage/control-plane/runtime.env`, then `.env`, while existing process environment variables take precedence. Kubernetes normally injects variables through `app-secrets`. The dashboard has a separate Next.js environment.

### Safe local `.env` template

Create `.env` from `.env.example`, then use placeholders like these—never copy real values into documentation:

```dotenv
# Required core services
DATABASE_URL=postgresql://brixta:change-me@127.0.0.1:5432/brixta
REDIS_URL=redis://127.0.0.1:6379/0

# Ingestion defaults
EMBEDDING_PLUGIN=sentence-transformers
EMBEDDING_MODEL=nomic-ai/nomic-embed-text-v1.5
BRIXTA_DOCLING_DEVICE=cpu
BRIXTA_DOCLING_THREADS=4
LOG_LEVEL=INFO

# Artifact backend: local or minio
ARTIFACT_BACKEND=minio
MINIO_ENDPOINT=127.0.0.1:9000
MINIO_CONSOLE_URL=http://127.0.0.1:9001
MINIO_ACCESS_KEY=brixta-app
MINIO_SECRET_KEY=replace-with-a-long-random-secret
MINIO_BUCKET=brixta
MINIO_SECURE=false

# Local MinIO server bootstrap only; do not give these to the app in production
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=replace-this-local-password

# Public URLs
BRIXTA_API_PUBLIC_URL=http://127.0.0.1:8000
BRIXTA_DASHBOARD_PUBLIC_URL=http://127.0.0.1:3000
BRIXTA_MCP_PUBLIC_URL=http://127.0.0.1:8001/mcp

# Job recovery
MAX_TASK_ATTEMPTS=3
TASK_RETRY_BACKOFF_SECONDS=15
ORPHAN_TIMEOUT_SECONDS=1800
MAX_JOB_RUNS=3

# Optional Hugging Face access/rate limit improvement
HF_TOKEN=

# Simulation executables/time limits
CALCULIX_EXECUTABLE=ccx
OPENFOAM_BLOCKMESH_EXECUTABLE=blockMesh
OPENFOAM_CHECKMESH_EXECUTABLE=checkMesh
OPENFOAM_RUN_EXECUTABLE=foamRun
OPENFOAM_VTK_EXECUTABLE=foamToVTK
SIMULATION_TIMEOUT_SECONDS=3600

# Not currently consumed by BRIXTA application code
OPENAI_API_KEY=
```

### MinIO credential precedence

The current artifact code checks `MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD` before `MINIO_ACCESS_KEY`/`MINIO_SECRET_KEY`. Therefore, if both pairs are present, the application will use the root pair. For production, remove root credentials from the application secret and provide only limited application credentials. Keep root credentials in the object-store administration secret.

### Core variables

| Variable | Required | Used by | Notes |
|---|---:|---|---|
| `DATABASE_URL` | Yes | API, workers, MCP, CLI doctor, migrations | Must point to PostgreSQL with pgvector. Neon should use `sslmode=require`. |
| `REDIS_URL` | Yes for async work | API/Celery/Beat | Code reads this variable. Some K8s YAML sets `CELERY_BROKER_URL`, which the current code ignores. |
| `EMBEDDING_PLUGIN` | No | ingestion default | Defaults to `sentence-transformers`. |
| `EMBEDDING_MODEL` | No | ingestion/query default | Must be a registry-approved profile. |
| `HF_TOKEN` | No | Hugging Face libraries | Avoids anonymous rate limits and is required for private/gated models. |
| `LOG_LEVEL` | No | runtime logging | Default `INFO`. |
| `BRIXTA_DOCLING_DEVICE` | No | Docling parser | Use `cpu` on ordinary development Macs/containers. |
| `BRIXTA_DOCLING_THREADS` | No | Docling parser | Tune against worker CPU limits. |
| `MAX_TASK_ATTEMPTS` | No | stage retry policy | Default 3. |
| `TASK_RETRY_BACKOFF_SECONDS` | No | stage retry policy | Base delay, default 15 seconds. |
| `ORPHAN_TIMEOUT_SECONDS` | No | reconciler | Default 1800 seconds. |
| `MAX_JOB_RUNS` | No | whole-job replay | Default 3 total runs. |

### Artifact variables

| Variable | Required | Meaning |
|---|---:|---|
| `ARTIFACT_BACKEND` | No | `local` or `minio`; selected when the process imports the backend, so restart after changing it. |
| `MINIO_ENDPOINT` | For MinIO | Host and port without scheme. |
| `MINIO_CONSOLE_URL` | No | Dashboard link to MinIO console. |
| `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | Production MinIO | Preferred application credentials. |
| `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` | Local server bootstrap | Development administration only. |
| `MINIO_BUCKET` | No | Defaults to `brixta`. |
| `MINIO_SECURE` | No | `true` for TLS endpoints. |

### MCP variables

| Variable | Mode | Purpose |
|---|---|---|
| `BRIXTA_MCP_AUTH_MODE` | all | `none`, `oauth-local`, `static`, or `jwt`. |
| `BRIXTA_MCP_HOST` / `BRIXTA_MCP_PORT` | all | Bind address/port; defaults are used by CLI/manifests. |
| `BRIXTA_MCP_TRANSPORT` | all | Normally `http` for remote/streamable HTTP. |
| `BRIXTA_MCP_PUBLIC_URL` | ChatGPT/prod | Complete public URL ending in `/mcp`. |
| `BRIXTA_MCP_TENANT_ID` | local/static | Tenant scope for development or static-token mode. |
| `BRIXTA_MCP_TOKEN` | static | Shared bearer token; not the recommended public ChatGPT design. |
| `BRIXTA_MCP_JWKS_URI` | jwt | IdP JWKS endpoint. |
| `BRIXTA_MCP_JWT_PUBLIC_KEY` | jwt alternative | Inline verification key if JWKS is not used. |
| `BRIXTA_MCP_JWT_ISSUER` | jwt | Exact expected issuer. |
| `BRIXTA_MCP_JWT_AUDIENCE` | jwt | Exact MCP resource audience. |
| `BRIXTA_MCP_JWT_ALGORITHM` | jwt | Allowed JWT algorithm. |
| `BRIXTA_MCP_TENANT_CLAIM` | jwt | Claim name used to derive tenant. |
| `BRIXTA_KNOWLEDGE_ACCESS_BACKEND` | MCP/API | Access-control repository selection where supported. |
| `MCP_ALLOWED_HOSTS` / `MCP_ALLOWED_ORIGINS` | remote | Host/origin allowlists passed to FastMCP. |
| `FASTMCP_CHECK_FOR_UPDATES` | optional | Set `off` in deterministic/server environments. |

### CLI/tunnel variables

| Variable | Purpose |
|---|---|
| `BRIXTA_STATE_DIR` | Override `.brixta` state/log directory. |
| `BRIXTA_CLOUDFLARE_PROTOCOL` | Defaults to `http2`; useful where QUIC is blocked. |
| `BRIXTA_CLOUDFLARE_START_TIMEOUT` | Wait for quick-tunnel URL. |
| `BRIXTA_PUBLIC_VERIFY_TIMEOUT` | Public DNS/edge/MCP verification window. |
| `BRIXTA_PUBLIC_REQUEST_TIMEOUT` | Individual HTTP verification timeout. |
| `BRIXTA_CHATGPT_CONNECT_URL` | Browser destination; defaults to ChatGPT Plugins. |
| `BRIXTA_CHATGPT_DISTRIBUTION` | Metadata for the intended connection/distribution flow. |

### Dashboard variables

| Variable | Scope | Meaning |
|---|---|---|
| `PYTHON_BACKEND_URL` | Next.js server | Internal API origin, e.g. `http://127.0.0.1:8000` locally or `http://gateway-service` in K8s. |
| `NEXT_PUBLIC_PYTHON_BACKEND_URL` | Browser | Optional browser-visible API origin. Prefer the same-origin `/api/core` proxy in production. |

### Infisical and CI variables

| Variable/secret | Used by |
|---|---|
| `INFISICAL_CLIENT_ID`, `INFISICAL_CLIENT_SECRET` | `start.sh` authenticates the Kubernetes secret-sync bootstrap. |
| Infisical project/environment/path in `k8s/infisical-secret.yaml` | Infisical Operator creates/updates `app-secrets`. |
| `DOCKER_USERNAME`, `DOCKER_PASSWORD` | Existing GitHub Actions Docker Hub login. |

`OPENAI_API_KEY` is currently loaded by configuration but not used by ingestion, retrieval, MCP, or simulations. Keep it unset unless new code explicitly requires it.

---

## Local installation

### 1. Enter the repository

```bash
cd "/path/to/BrReseaRepo"
```

Paths containing spaces work when quoted, but a short path such as `~/code/brixta` is easier to operate.

### 2. Create the supported virtual environment

On macOS with Homebrew Python 3.11:

```bash
brew install python@3.11
/opt/homebrew/bin/python3.11 -m venv Resea
source Resea/bin/activate
python --version
```

Expected: Python 3.11.x. On Intel macOS the Homebrew path may be `/usr/local/bin/python3.11`. On Linux, use the installed `python3.11` binary.

If an old environment was created with Python 3.9 or 3.14, deactivate it, move or delete **only the explicit `Resea` directory**, then recreate it:

```bash
deactivate 2>/dev/null || true
mv Resea "Resea.backup.$(date +%Y%m%d%H%M%S)"
python3.11 -m venv Resea
source Resea/bin/activate
```

The move is recoverable. After the new environment works, the backup can be removed intentionally.

### 3. Install maintained dependencies and the CLI

For a complete developer machine that runs API, workers, retrieval, MCP, and CLI:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-workers.txt -r requirements-rag.txt
python -m pip install -e .
rehash 2>/dev/null || true
brixta --help
```

Do not run `pip install requirements.txt`; that asks PyPI for a package literally named `requirements.txt`. `pip install -r requirements.txt` uses the historical freeze but is also not recommended for a clean build. The maintained command is the one above.

### 4. Create `.env`

```bash
cp .env.example .env
chmod 600 .env
```

Edit `.env` and set at least `DATABASE_URL`, `REDIS_URL`, and artifact settings. Use a new database/credentials; do not copy secrets from old logs.

### 5. Install dashboard and migration dependencies

```bash
(cd infra && npm ci)
(cd brixta-dashboard && npm ci)
```

### About `scripts/bootstrap-local.sh`

The helper detects Python 3.11–3.13, creates `Resea`, copies `.env.example`, starts local infrastructure, migrates, and installs dashboard dependencies. In this snapshot it still installs the historical `requirements.txt`. Until that line is changed to the maintained groups, prefer the manual steps above. Also resolve the missing `infra/postgres-init.sql` reference before relying on its Compose PostgreSQL path.

---

## Starting the complete local stack

### Option A: external Neon PostgreSQL, local Redis and MinIO

This avoids the current missing Compose PostgreSQL initializer.

```bash
docker compose up -d redis minio minio-init
docker compose ps
```

Set the Neon `DATABASE_URL` in `.env`, then migrate:

```bash
cd infra
npm run db:migrate
cd ..
```

Because migration history needs reconciliation, compare the resulting database with `infra/schema.ts` before proceeding. In development only, the included Kubernetes migration job uses `drizzle-kit push`; do not substitute schema push for reviewed production migrations.

### Option B: full Compose infrastructure

First create and review `infra/postgres-init.sql`; at minimum it needs:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Then:

```bash
docker compose up -d postgres redis minio minio-init
docker compose ps
```

Do not invent a production database from this one-line initializer. Run the reviewed Drizzle migrations and schema verification described below.

### Processes and terminals

Activate `Resea` in every Python terminal.

**Terminal 1 — API**

```bash
source Resea/bin/activate
python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 — light ingestion worker**

```bash
source Resea/bin/activate
python -m celery -A runtime.celery_app.celery worker \
  --loglevel=info \
  --queues=downloader,parser,chunker \
  --concurrency=2 \
  --hostname=light@%h
```

**Terminal 3 — embedding/storage worker**

On macOS, start with concurrency 1 to avoid multiplying model memory. If Metal/MPS is unstable, use the configured CPU device.

```bash
source Resea/bin/activate
BRIXTA_DOCLING_DEVICE=cpu python -m celery -A runtime.celery_app.celery worker \
  --loglevel=info \
  --queues=embeddings,storage \
  --concurrency=1 \
  --hostname=embedding@%h
```

**Terminal 4 — scheduler and orphan reconciler**

```bash
source Resea/bin/activate
python -m celery -A runtime.celery_app.celery beat --loglevel=info
```

**Terminal 5 — dashboard**

```bash
cd brixta-dashboard
PYTHON_BACKEND_URL=http://127.0.0.1:8000 npm run dev
```

Open:

- API: <http://127.0.0.1:8000>
- API docs: <http://127.0.0.1:8000/docs>
- Dashboard: <http://127.0.0.1:3000>
- MinIO API: <http://127.0.0.1:9000>
- MinIO console: <http://127.0.0.1:9001>

### Verify the stack

```bash
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/prod/health
curl -fsS http://127.0.0.1:8000/plugins
redis-cli -u "$REDIS_URL" ping
brixta doctor
```

`brixta doctor` validates the supported Python runtime, dependencies, `DATABASE_URL`, PostgreSQL/pgvector, ready knowledge bases, and one semantic query. Its first semantic query can load/download an embedding model and therefore take longer.

---

## Ingestion and knowledge lifecycle

### URL ingestion

```bash
curl -X POST http://127.0.0.1:8000/ingest \
  -H 'Content-Type: application/json' \
  -d '{
    "tenant_id": "demo",
    "source_type": "url",
    "source_target": "https://example.com",
    "plugins": {
      "downloader": "http",
      "parser": "docling",
      "chunker": "docling-hybrid",
      "embedding": "sentence-transformers",
      "storage": "pgvector"
    },
    "embedding_model": "nomic-ai/nomic-embed-text-v1.5"
  }'
```

The HTTP downloader currently performs a single request with a 30-second timeout. It does not discover an entire site, render JavaScript, obey source-level recursive rules, or provide browser automation.

### File ingestion

```bash
curl -X POST http://127.0.0.1:8000/ingest/file \
  -F tenant_id=demo \
  -F file=@./document.pdf \
  -F embedding_model=nomic-ai/nomic-embed-text-v1.5
```

The API permits up to 50 MiB and supports PDF, Office, HTML, Markdown, text, CSV, JSON, YAML, XML, common source-code files, and solver-input extensions. Engineering text/source formats select the `plain-text` parser and `text-window` chunker when appropriate.

### Job states

```text
queued -> downloading -> parsing -> chunking -> embedding -> storage -> completed
                                                                \-> failed
```

A completed job is a knowledge base only when it has at least one persisted chunk. The knowledge manifest then contains:

- stable job/knowledge ID;
- `brixta://knowledge/<uuid>` internal handle;
- tenant/source provenance;
- chunk count;
- embedding model and dimension;
- dashboard, retrieval, and MCP metadata.

The `brixta://` handle is an internal stable identifier. It does not itself connect ChatGPT, open pgvector, or define a network protocol. HTTP retrieval and MCP are the transports.

### Retrieval behavior

BRIXTA embeds the query with the same approved model/profile used for the chunks, including any model-specific query prefix. The SQL search filters by:

- tenant;
- knowledge-base/job ID;
- embedding model;
- embedding dimension.

It orders by pgvector cosine distance. This prevents comparing incompatible vector spaces. Search returns chunks and citation metadata; the AI client composes the natural-language answer.

### Knowledge access

`knowledge_access` can enable or disable a knowledge base for a tenant's shared MCP connection. Absence of an override currently means enabled. This is product access configuration—not a substitute for authenticated tenant authorization.

---

## Plugin system

### Plugin stages

The registry in `core/plugin_loader.py` supports exactly:

```text
downloader, parser, chunker, embedding, storage
```

Each `PluginSpec` declares an ID, stage, name, version, import path, capabilities, optional default, and optional embedding model profiles. The loader imports implementations lazily and validates job selection before dispatch.

### Current ingestion plugins

| Stage | ID | Default | Capability/current behavior |
|---|---|---:|---|
| downloader | `http` | Yes | One HTTP URL. |
| downloader | `local-file` | No | Uploaded local artifact. |
| parser | `docling` | Yes | HTML, PDF, Office, OCR through Docling. |
| parser | `plain-text` | No | Source code, solver inputs, CSV, JSON, YAML and text. |
| chunker | `docling-hybrid` | Yes | Structure-aware Docling chunks. |
| chunker | `text-window` | No | Overlapping windows for engineering/plain text. |
| embedding | `sentence-transformers` | Yes | Local Hugging Face/Sentence Transformers profiles. |
| storage | `pgvector` | Yes | Content, embedding, model and dimension in PostgreSQL. |

### Approved embedding profiles

| Model | Dimensions | Special behavior |
|---|---:|---|
| `nomic-ai/nomic-embed-text-v1.5` | 768 | Document/query prefixes, normalization, pinned remote-code revision, CPU default. |
| `BAAI/bge-large-en-v1.5` | 1024 | Approved 1024-dimensional profile. |
| `intfloat/e5-large-v2` | 1024 | Uses `passage: ` for documents and `query: ` for queries. |

Not every Hugging Face model is automatically usable. A model must be registered with its dimension, prefixes, normalization, revision/trust policy, and device behavior. Treat `trust_remote_code=True` as a supply-chain decision: pin/review the revision before deployment.

### Add an ingestion plugin

1. Choose the existing stage and a stable lowercase ID.
2. Implement the matching interface in `brixta_sdk/`.
3. Put the implementation under `plugins/<stage>/`.
4. Avoid importing heavyweight libraries at module import time when the API can run without them.
5. Register one `PluginSpec` in `core/plugin_loader.py`.
6. Add its dependency to the appropriate requirements/image, not blindly to every service.
7. Add registry, validation, success, failure, retry, serialization, and integration tests.
8. Expose any safe configuration in the API/dashboard.
9. Document credentials, artifact contracts, resource requirements, and version support.

Example shape:

```python
registry.register(
    PluginSpec(
        "my-parser",
        "parser",
        "My Parser",
        "1.0.0",
        "plugins.parser.my_parser:MyParserPlugin",
        ("pdf", "text"),
    )
)
```

The class must accept and return a serializable `PipelineContext`. Do not put open database connections, model objects, request objects, or other non-JSON state inside the context passed through Celery.

### Add an embedding model

Add a `ModelSpec` under the existing embedding plugin when the adapter is compatible. Supply:

- exact model ID;
- vector dimensions;
- document and query prefixes;
- normalization setting;
- reviewed revision;
- `trust_remote_code` policy;
- device default.

Then ingest and retrieve a known fixture and verify the stored dimension. Changing a knowledge base's query model without re-embedding its documents is invalid.

### Remove or move a plugin safely

Do not delete a plugin merely because it is not the current default.

1. Search persisted `ingestion_jobs.context_json`, source definitions, settings, tests, docs, UI choices, and deployments for its ID.
2. Mark it deprecated and prevent new selection while allowing historical replay/export.
3. Migrate or re-ingest affected sources if necessary.
4. Remove it from defaults, registry, UI, requirements, image, and tests in one versioned change.
5. Keep a compatibility error that clearly identifies the removed plugin.
6. Only then delete the module.

Moving a file requires changing the registry import path and package/image copy rules. A plugin ID is a persisted contract; changing its ID is a data migration, not a rename.

---

## Sources, crawling, and schedules

The Sources page/API manages reusable source definitions and optional cron schedules. Current state is stored in `storage/control-plane/sources.json`.

### Source API

```text
GET    /sources
POST   /sources
PATCH  /sources/{source_id}
DELETE /sources/{source_id}
POST   /sources/{source_id}/sync
```

Source records include target, tenant, plugin/model choices, enabled state, schedule state, five-field cron expression, timezone, and crawl-strategy fields.

### Scheduler

Celery Beat calls `runtime.tasks.schedules.dispatch_due_sources` every minute. It:

1. loads enabled scheduled sources;
2. validates a five-field cron expression;
3. resolves the IANA timezone with `zoneinfo`;
4. evaluates whether the schedule is due since `last_run_at`/creation;
5. creates a normal ingestion job.

Example: every day at 02:30 in Kolkata:

```text
30 2 * * *
timezone: Asia/Kolkata
```

Celery Beat must run continuously. Run only one Beat instance unless you add a distributed scheduler/lock, or duplicate dispatch is possible.

### Crawling limitation

The source schema advertises `single_page`, `sitemap`, and `recursive` strategies plus depth/page/include/exclude settings. Only single-page download is implemented by the current `http` plugin. A real crawler plugin must add URL normalization, robots/sitemap policy, deduplication, limits, retries, content hashing, incremental checkpoints, and JavaScript-rendering strategy as needed.

### Multi-replica limitation

The JSON repository has no transactional row locks, shared revision history, or cross-pod consistency. It is acceptable for one local/control-plane instance. Move sources and scheduler leases to PostgreSQL before production horizontal scaling.

---

## Celery runtime, retries, and recovery

### Queues

| Queue | Work | Recommended worker |
|---|---|---|
| `downloader` | fetch/copy source artifact | light |
| `parser` | Docling/plain-text parse | light or document worker |
| `chunker` | chunk creation | light |
| `embeddings` | model inference | dedicated CPU/GPU worker |
| `storage` | pgvector persistence | embedding/storage worker |
| `simulations.calculix` | CalculiX pack | dedicated CalculiX image, concurrency 1 |
| `simulations.openfoam` | OpenFOAM pack | dedicated OpenFOAM image, concurrency 1 |

Redis is both broker and result backend. Queue depth is not the same as durable job truth; PostgreSQL is the job history authority.

### Stage retry policy

Default task attempts are 3, with exponential delays based on 15 seconds (approximately 15, 30, 60). Validation/type/value/key/file/permission/not-implemented errors, database schema/programming errors, data errors, and HTTP 4xx errors are treated as permanent. Transient operational/network failures can retry.

Terminal failures store a bounded error log. Retrying a job creates a new job linked through `parent_job_id` rather than rewriting historical truth. `MAX_JOB_RUNS` limits replay loops.

### Orphan recovery

Celery Beat runs `runtime.tasks.reconcile.reconcile_orphaned_jobs` every minute. A nonterminal job older than `ORPHAN_TIMEOUT_SECONDS` is checked against active, reserved, and scheduled Celery tasks. If no matching task/progress exists, it is marked failed instead of remaining forever at `queued` or `embedding`.

Requirements for recovery to work:

- Beat is running;
- Redis/Celery inspection works;
- at least one worker consumes the reconciler's routed queue;
- API and workers share PostgreSQL;
- clocks are reasonably synchronized.

Simulation tasks record their own failure state, but simulation orphan reconciliation/retry is not yet equivalent to ingestion recovery. A worker crash can leave a simulation queued/running until an operator resolves it. This is a roadmap item.

### Inspect Celery

```bash
python -m celery -A runtime.celery_app.celery inspect ping
python -m celery -A runtime.celery_app.celery inspect active
python -m celery -A runtime.celery_app.celery inspect reserved
python -m celery -A runtime.celery_app.celery inspect scheduled
redis-cli -u "$REDIS_URL" LLEN downloader
redis-cli -u "$REDIS_URL" LLEN embeddings
```

Do not purge queues as a first response. Confirm which tasks/jobs are affected and preserve job/error evidence.

---

## PostgreSQL, Neon, and pgvector

### Required server features

- PostgreSQL with `gen_random_uuid()` support.
- pgvector extension.
- A database user allowed to use the `BrResearch` schema and the required tables/sequences.
- TLS for remote databases. Neon connection strings normally include `sslmode=require`.

Check:

```sql
SELECT version();
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
SELECT current_database(), current_user;
```

Enable pgvector with an owner-capable connection:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Current logical schema

The target schema is `infra/schema.ts`. The important tables are:

#### `BrResearch.ingestion_jobs`

| Column group | Purpose |
|---|---|
| `id` | UUID job/knowledge-base identity. |
| `source_type`, `source_target`, `tenant_id` | Provenance and scope. |
| `status`, `current_stage`, `terminal`, `retryable`, `error_log` | Durable lifecycle. |
| `created_at`, `updated_at`, `started_at`, `completed_at` | Timing and orphan detection. |
| `celery_task_id` | Correlation to Celery. |
| `attempt_count`, `max_attempts`, `retry_count`, `parent_job_id` | Retry/replay history. |
| `context_json` | Serialized pipeline/plugin/model/artifact context for replay and audit. |

#### `BrResearch.document_chunks`

| Column | Purpose |
|---|---|
| `id` | Bigint primary key. |
| `job_id` | Cascading FK to ingestion job. |
| `tenant_id` | Explicit scope. |
| `chunk_index` | Stable position within job; target schema makes `(job_id, chunk_index)` unique. |
| `content` | Retrieved text. |
| `embedding` | Unbounded pgvector value. |
| `embedding_model`, `embedding_dimension` | Vector-space identity. |

The unbounded vector column permits 768- and 1024-dimensional profiles in one logical table. Every similarity query must filter model and dimension. This flexibility makes a single generic ANN index difficult; see scaling below.

#### `BrResearch.knowledge_access`

Composite key `(tenant_id, knowledge_base_id)`, enabled flag, and update timestamp. It controls which completed knowledge bases are advertised through a tenant's shared gateway.

#### `BrResearch.simulation_runs`

Stores tenant, label, case card, solver, execution mode, status/stage, structured spec/evidence/summary/artifact metadata, error, Celery task ID, artifact prefix, and timestamps. Heavy solver outputs live in the artifact backend.

### Migration warning

The migration directory contains a legacy schema migration, subsequent moves into `BrResearch`, vector-dimension changes, knowledge access, and simulation tables. It also contains duplicate-numbered migration names and does not visibly provide every lifecycle/context column declared by the current `schema.ts`. Therefore:

1. create a disposable fresh PostgreSQL database;
2. run migration history from zero;
3. compare it to `infra/schema.ts`;
4. generate/review one new forward migration that reconciles the difference;
5. test it against a sanitized copy of the current database;
6. take a backup/PITR checkpoint;
7. deploy migration before new application code;
8. never edit a migration that has already run in a shared environment.

Useful inspection SQL:

```sql
SELECT
  ordinal_position,
  column_name,
  data_type,
  udt_name,
  is_nullable,
  column_default
FROM information_schema.columns
WHERE table_schema = 'BrResearch'
  AND table_name IN ('ingestion_jobs', 'document_chunks', 'knowledge_access', 'simulation_runs')
ORDER BY table_name, ordinal_position;

SELECT schemaname, tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'BrResearch'
ORDER BY tablename, indexname;

SELECT
  min(embedding_model) AS model,
  embedding_dimension,
  vector_dims(embedding) AS actual_dimension,
  count(*) AS rows
FROM "BrResearch".document_chunks
GROUP BY embedding_dimension, vector_dims(embedding)
ORDER BY rows DESC;
```

### Neon setup

1. Create a Neon project/database and a least-privilege application role.
2. Enable pgvector.
3. Put the pooled connection URL in application/worker secrets. Confirm Celery concurrency and database pool behavior are compatible with Neon connection limits.
4. Use a direct/owner migration URL in CI or a controlled migration Job when pooled connections are unsuitable for DDL.
5. Run reconciled migrations.
6. Verify schema and one semantic query with `brixta doctor`.
7. Enable Neon backups/PITR appropriate to the environment.

### Strengths

- Durable job history separate from queue memory.
- Cascading chunk ownership.
- Model/dimension provenance enables multiple embedding profiles.
- Serialized context supports replay and investigation.
- Knowledge access and simulation run records are explicit platform concepts.

### Weaknesses and scale plan

- No PostgreSQL Row Level Security today. Add RLS policies keyed from verified tenant context, plus tests that attempt cross-tenant access.
- No vector ANN index today; searches are exact scans. At scale, use model/dimension-specific partitions/tables or reviewed partial/expression HNSW indexes.
- No hybrid full-text + vector ranking, reranker, deduplication, or quality/evaluation table.
- No first-class document version, source revision, crawl page, deletion tombstone, audit, usage, quota, billing, or retention tables.
- `content` lacks general chunk metadata JSON; richer citations will need page/section/source-version metadata.
- Migration drift is currently a deployment risk.
- Sources/settings are not in the database.

---

## Artifacts and MinIO

### Local backend

`ARTIFACT_BACKEND=local` writes under repository storage paths. It is useful for one developer process and not shared across pods/nodes.

### MinIO backend

Start the included local services:

```bash
docker compose up -d minio minio-init
docker compose logs -f minio
```

Or a standalone development container:

```bash
docker run -d \
  --name brixta-minio \
  -p 9000:9000 \
  -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD='replace-this-local-password' \
  -v "$HOME/minio-data:/data" \
  quay.io/minio/minio server /data --console-address ':9001'
```

Restart an existing development container with `docker start brixta-minio`. Use the console only for administration; BRIXTA accesses objects through the S3-compatible API.

Production should use:

- TLS;
- limited application access/secret keys;
- a non-public console;
- bucket versioning/lifecycle/retention as required;
- backup/replication and restore tests;
- tenant-aware object prefixes/policies;
- server-side encryption where required;
- no root credentials in API/worker secrets.

Generated simulation artifacts use a `simulations/<run_id>/...` prefix. Ingestion artifacts and uploaded files must also be treated as untrusted content: validate type/size, scan where required, and never execute arbitrary uploads in a privileged process.

---

## API reference

FastAPI exposes interactive docs at `/docs`. The list below describes the major routes; the OpenAPI document is the exact request/response contract for the running version.

### Core

| Method | Route | Purpose |
|---|---|---|
| GET | `/health` | Basic API health. |
| POST | `/ingest` | Queue URL/source ingestion. |
| POST | `/ingest/file` | Upload and queue a file. |
| GET | `/plugins` | Full registry listing. |
| GET/POST/PATCH/DELETE | `/sources...` | Source and schedule management. |
| POST | `/sources/{id}/sync` | Manual source synchronization. |

### Jobs and knowledge (`/prod`)

| Method | Route | Purpose |
|---|---|---|
| GET | `/prod/jobs` | Persisted job history. |
| GET | `/prod/jobs/{id}` | Job details. |
| POST | `/prod/jobs/{id}/retry` | Create a replay job when allowed. |
| GET | `/prod/knowledge` | Ready knowledge bases. |
| GET | `/prod/knowledge/{id}` | Manifest. |
| POST | `/prod/knowledge/{id}/search` | Semantic search. |
| GET | `/prod/knowledge/{id}/chunks/{index}` | Fetch citation chunk. |
| GET/PUT | `/prod/knowledge/{id}/access` | Read/change tenant availability. |
| GET/POST | `/prod/knowledge/{id}/chatgpt-connection` | Connection readiness/access workflow. |
| GET | `/prod/mcp/status` | Shared gateway configuration/readiness metadata. |

Example search:

```bash
curl -X POST http://127.0.0.1:8000/prod/knowledge/KNOWLEDGE_UUID/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"What does the source say about route handlers?","limit":5}'
```

### Operations (`/prod`)

Storage, runtime settings, health, Redis, Celery, plugin catalog, and Docker inspection/control routes exist under `/prod`. Docker restart/log routes are privileged administration operations. They are not safe for anonymous production traffic.

### Simulations (`/prod/simulations`)

| Method | Route | Purpose |
|---|---|---|
| GET | `/case-cards` | Available validated simulation packs. |
| POST | `/preflight` | Validate/compile preview inputs without launching a solver run. |
| POST | `/runs` | Queue a preview or solver run. |
| GET | `/runs` | Tenant run history. |
| GET | `/runs/{id}` | Run details. |
| POST | `/runs/{id}/cancel` | Revoke/cancel run. |
| GET | `/runs/{id}/artifacts/{path}` | Download an allowed artifact. |

### API security work still required

The current API does not establish a production user session or universally derive tenant from a verified identity. Before public deployment add:

- OIDC/OAuth login and backend token/session validation;
- tenant/role derivation, not request trust;
- admin/worker/service roles;
- RLS or equivalent repository enforcement;
- CSRF protection for cookie sessions;
- rate/size/concurrency limits;
- audit events for access, retries, syncs, settings, Docker controls and simulation runs;
- signed object downloads where appropriate;
- strict CORS and same-origin production proxying.

---

## Dashboard

The dashboard is a Next.js 16/React 19 application. Current pages cover dashboard health/history, ingestion, sources/schedules, knowledge bases, simulations, plugins, settings, Docker, Celery, MinIO, Redis, and documentation. Kubernetes and marketplace navigation were removed.

### Local proxy

Browser requests normally go to `/api/core/...`; `brixta-dashboard/app/api/core/[...path]/route.ts` forwards them to `PYTHON_BACKEND_URL`. If the API is stopped, Next.js reports `ECONNREFUSED 127.0.0.1:8000`. Start Uvicorn or point the variable to the correct service.

Before release add `PUT` forwarding to the proxy because knowledge access uses a PUT endpoint.

### Current UI truth

- Theme controls are client UI.
- Notifications are client-derived; there is no durable event inbox/push provider yet.
- Search is not a full global indexed search service.
- Infrastructure pages reflect reachable backends; they cannot invent Kubernetes/Docker/MinIO state.
- MinIO console is linked, not embedded as a secure single-sign-on administration plane.
- The login page explicitly enters a dashboard whose production authentication is not enabled.

### Production login design

Use one external OIDC identity provider for the dashboard/API and MCP authorization relationship:

1. Browser chooses **Sign in**.
2. Dashboard uses Authorization Code + PKCE with the IdP.
3. Backend establishes an `HttpOnly`, `Secure`, `SameSite` session or validates a short-lived access token.
4. User identity maps to tenant memberships and roles in BRIXTA.
5. API ignores request-supplied tenant when a session exists and derives allowed scope.
6. Admin-only routes require explicit roles and step-up authorization if appropriate.
7. MCP tokens use a distinct MCP audience and include/resolve tenant membership.
8. Logout revokes/ends the BRIXTA session; IdP and MCP refresh-token lifecycle is handled explicitly.

This does not mean logging into BRIXTA automatically logs the user into MinIO, Redis, Celery, or PostgreSQL consoles. Those are infrastructure systems. Surface their safe status/actions through BRIXTA RBAC, or configure each vendor console against the same IdP where supported. Do not proxy root credentials to users.

---

## MCP and AI-client integration

### Shared gateway model

BRIXTA runs one long-lived, tenant-scoped shared MCP gateway—not one process per knowledge base. New completed and enabled knowledge bases appear through the existing connection without another port or ChatGPT reconnection.

### Current tools

| Tool | Access | Purpose |
|---|---|---|
| `brixta_list_knowledge_bases` | read | List enabled ready knowledge bases in token tenant. |
| `brixta_search` | read | Semantic search within an allowed knowledge base. |
| `brixta_get_chunk` | read | Fetch complete text/citation metadata for a search result. |
| `brixta_list_sources` | read | List source definitions in scope. |
| `brixta_sync_source` | write | Trigger a source sync. |
| `brixta_list_simulation_runs` | read | List simulation runs in tenant scope. |
| `brixta_get_simulation_report` | read | Fetch a structured simulation report. |

### Authentication modes

| Mode | Use | Security boundary |
|---|---|---|
| `none` | Local generic clients only | Server must bind to loopback. |
| `oauth-local` | Local ChatGPT developer testing | Ephemeral in-memory OAuth/DCR/PKCE; restart loses registrations/tokens. |
| `static` | Controlled internal testing | Shared bearer token + fixed tenant; weak operational model. |
| `jwt` | Production | Verify IdP-issued token with JWKS/public key, issuer, audience, algorithm, and tenant claim. |

The local provider includes a compatibility adapter for FastMCP 2.14-era access-token type mismatches. Keep FastMCP/MCP packages pinned and rebuild all MCP runtimes together when upgrading.

### Local ChatGPT developer flow

Prerequisite:

```bash
brew install cloudflared
cloudflared --version
```

Then:

```bash
source Resea/bin/activate
brixta disconnect
brixta doctor
brixta connect chatgpt --local --tenant demo
```

The command:

1. validates configuration, PostgreSQL, knowledge bases and semantic search;
2. starts a Cloudflare Quick Tunnel;
3. starts the shared MCP gateway on `127.0.0.1:8001` with local OAuth;
4. verifies OAuth discovery, dynamic registration, PKCE, MCP initialization and tool listing through the public URL;
5. stores process/state metadata in `.brixta/connection.json`;
6. opens ChatGPT's plugin page unless `--no-browser` is passed.

If the new hostname has not propagated, the CLI preserves both processes, records a degraded/starting state, and asks you to rerun the same command. It reuses the existing connection instead of leaking more processes.

In ChatGPT:

1. enable Developer mode if your plan/workspace allows it;
2. open Settings → Plugins;
3. create a developer-mode BRIXTA app;
4. paste the printed HTTPS URL ending in `/mcp`;
5. complete ChatGPT's one-time OAuth/consent screen;
6. start a chat and invoke/list BRIXTA knowledge.

OpenAI's current official developer-mode and publishing flow is documented in [Connect from ChatGPT](https://developers.openai.com/apps-sdk/deploy/connect-chatgpt), [Authentication](https://developers.openai.com/apps-sdk/build/auth), and [Deploy your app](https://developers.openai.com/apps-sdk/deploy).

BRIXTA cannot silently sign in to a user's ChatGPT account, create the developer app on their behalf, or demand an approval email from ChatGPT. An IdP may send its own verification email, but ChatGPT connection consent occurs in ChatGPT/OAuth. Public one-click product discovery requires publishing/submitting the plugin according to OpenAI's current process.

### Local generic MCP client flow

```bash
brixta disconnect
brixta connect client --local --tenant demo
```

It prints:

```json
{
  "mcpServers": {
    "brixta": {
      "url": "http://127.0.0.1:8001/mcp"
    }
  }
}
```

Only software that implements MCP over streamable HTTP can use that configuration. Ollama is a model server, not automatically an MCP host; connect BRIXTA to an MCP-capable UI/agent that calls an Ollama model. The model must support tool calling. A model such as a tiny `smollm:135m` build that reports “does not support tools” cannot drive MCP tools.

Raw MCP HTTP clients must send:

```http
Accept: application/json, text/event-stream
Content-Type: application/json
```

Otherwise FastMCP returns `406 Not Acceptable: Client must accept text/event-stream`.

### Production ChatGPT flow

```mermaid
sequenceDiagram
    participant U as User
    participant D as BRIXTA Dashboard
    participant C as ChatGPT
    participant I as Identity Provider
    participant M as BRIXTA MCP
    U->>D: Enable knowledge bases
    U->>C: Add/pick published BRIXTA app
    C->>I: OAuth authorization
    U->>I: Sign in and consent
    I-->>C: Tenant-scoped token
    C->>M: MCP tools with bearer token
    M-->>C: Scoped search and citations
```

Production requires:

- stable `https://mcp.your-domain.example/mcp`;
- public OAuth protected-resource/authorization-server discovery;
- an IdP that issues short-lived JWT access tokens for the MCP audience;
- JWKS rotation, issuer/audience validation, tenant membership/claim validation;
- rate limits, audit logs, revocation/refresh policy;
- one continuously deployed MCP service;
- a published plugin or a supported developer/workspace connection flow.

Set production MCP variables, deploy it, then verify from an operator environment:

```bash
export BRIXTA_MCP_PUBLIC_URL=https://mcp.example.com/mcp
brixta connect chatgpt --no-browser
```

This command verifies/prints the already deployed endpoint. It does not deploy the server or bypass user approval.

### Add or remove MCP tools

To add a tool:

1. place domain logic in a runtime service, not directly in the transport layer;
2. add a typed tool in `brixta_mcp/tools/`;
3. register it from `brixta_mcp/server.py`;
4. decide read/write scope and enforce tenant from access token context;
5. bound inputs/results and prevent arbitrary file/SQL/shell access;
6. add it to CLI gateway verification's expected tool set;
7. add protocol, auth, cross-tenant-denial, and failure tests;
8. update docs and client metadata;
9. restart/redeploy MCP.

To remove a tool, deprecate it first, remove callers/verification expectations, publish a version/changelog, then unregister and delete it. Tool names and schemas are client contracts.

### MCP process management

```bash
brixta connection status
brixta disconnect
tail -f .brixta/mcp.log
tail -f .brixta/tunnel.log
lsof -nP -iTCP:8001 -sTCP:LISTEN
pgrep -fl 'cloudflared|api.mcp_server|brixta_mcp'
```

Do not start a second gateway on port 8001. `brixta disconnect` should terminate only the recorded MCP/tunnel processes and clear local state. If state is stale, inspect the exact PID before sending `TERM`.

### Quick Tunnel warning

Cloudflare Quick Tunnels use random hostnames, provide no uptime SLA, and are explicitly for testing/development. See Cloudflare's [Quick Tunnels documentation](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/). A quick tunnel can temporarily return 502 while the local origin starts, can wait on public hostname propagation, and dies when the local process/machine/network stops. Production must use Kubernetes ingress or a named managed tunnel with a stable hostname—not the CLI quick-tunnel lifecycle.

---

## CLI reference

The package name/version is defined in `pyproject.toml`; the console entry point maps `brixta` to `brixta_cli.main:main`.

```text
brixta doctor [--skip-semantic]
brixta serve mcp
brixta connect chatgpt [--local] [--tenant TENANT] [--no-browser]
brixta connect client --local [--tenant TENANT]
brixta connection status
brixta disconnect
brixta knowledge list [--tenant TENANT]
brixta knowledge search HANDLE "QUERY" [--tenant TENANT] [--limit N]
```

If `brixta: command not found`:

```bash
source Resea/bin/activate
python -m pip install -e .
rehash 2>/dev/null || true
which brixta
brixta --help
```

The editable install is for developers. End users should eventually install a signed/versioned package or use the hosted dashboard; they should not have to clone the repository to connect to BRIXTA Cloud.

---

## Simulation Lab

Simulation packs are deterministic integrations around approved solvers. The user chooses a Case Card, enters bounded values, reviews preflight, and runs a preview or solver job. The LLM is not allowed to paste arbitrary code into a solver.

```mermaid
flowchart TD
    A[Case Card form] --> B[Typed SimulationSpec]
    B --> C[Validation and preflight]
    C --> D[Deterministic compiler]
    D --> E[CalculiX or OpenFOAM worker]
    E --> F[Postprocessor]
    F --> G[PostgreSQL metadata]
    F --> H[MinIO artifacts]
    G --> I[Dashboard and MCP]
```

### Current packs

#### Structural coupon tension — `structural_coupon_tension_v1`

- Solver: CalculiX.
- Problem: static linear-elastic rectangular tension coupon.
- Inputs include geometry, elastic modulus, Poisson ratio, density, load, optional yield strength, and mesh divisions.
- Preview produces analytical stress, strain, displacement, optional factor of safety, validated case metadata, and visualization data.
- Solver mode writes CalculiX input, runs `ccx`, and preserves DAT/FRD/native outputs.
- Current browser visualization is an analytical/geometry preview. It does not parse every solver field/extremum from FRD into a certified result viewer.

#### OpenFOAM channel flow — `openfoam_channel_flow_v1`

- Solver: OpenFOAM Foundation v13.
- Problem: transient laminar incompressible flow through a straight rectangular channel.
- Inputs include dimensions, inlet/flow values, viscosity, mesh counts, time controls, and numerics.
- Validation checks bounds, cells/time-step/Courant-related constraints, and approved template compatibility.
- Compiler generates `simulation-spec.json`, `0/U`, `0/p`, `constant/physicalProperties`, `system/*`, `Allrun`, a case README, visualization JSON, and a case ZIP.
- Solver mode runs fixed commands such as `blockMesh`, `checkMesh`, `foamRun`, and optional `foamToVTK` through the dedicated image.
- The browser scene is a boundary/setup preview, not a fully parsed CFD field viewer.

### Important JSON/OpenFOAM truth

OpenFOAM does **not** open BRIXTA's JSON directly. BRIXTA validates the JSON and deterministically compiles it into a standard OpenFOAM case directory/ZIP. An engineer can extract and inspect/edit dictionaries, but manual edits after compilation are outside the original validated spec/provenance unless re-imported and reviewed.

### Preview versus solver mode

| Mode | Requires solver binary | Result |
|---|---:|---|
| `preview` | No | Validated spec, compiled case artifacts, analytical/preflight summary, preview visualization. |
| `solver` | Yes | Everything above plus native solver execution logs/artifacts and postprocessing. |

Preview runs still travel through the case's solver-specific Celery queue, so the corresponding worker must be running under the current routing design.

### Local CalculiX worker

Install `ccx` or run the dedicated container image, then:

```bash
source Resea/bin/activate
CALCULIX_EXECUTABLE=ccx python -m celery -A runtime.celery_app.celery worker \
  --loglevel=info \
  --queues=simulations.calculix \
  --concurrency=1 \
  --hostname=calculix@%h
```

### Local OpenFOAM worker

OpenFOAM is easiest inside the dedicated image:

```bash
docker build -f Dockerfile.openfoam -t brixta-openfoam:local .
docker run --rm --env-file .env --network host brixta-openfoam:local
```

Docker Desktop on macOS does not provide Linux `--network host` behavior identical to native Linux. Point `DATABASE_URL`, `REDIS_URL`, and `MINIO_ENDPOINT` at host-reachable names such as `host.docker.internal`, or attach all services to one Compose network.

### Use the Simulation Lab

1. Start API, Redis, PostgreSQL, artifact backend, and the selected simulation worker.
2. Open `/simulations` in the dashboard.
3. Select a Case Card.
4. Choose preview or solver execution.
5. Enter values within displayed bounds.
6. Run preflight and review warnings/derived values.
7. Submit the run and watch status.
8. Download spec, case ZIP/input, logs, visualization/report, and native solver artifacts.
9. Compare results only within the assumptions of the selected Case Card.

API example — preflight a structural coupon:

```bash
curl -X POST http://127.0.0.1:8000/prod/simulations/preflight \
  -H 'Content-Type: application/json' \
  -d '{
    "tenant_id": "demo",
    "case_card_id": "structural_coupon_tension_v1",
    "parameters": {
      "length_mm": 100,
      "width_mm": 10,
      "thickness_mm": 2,
      "youngs_modulus_mpa": 70000,
      "poisson_ratio": 0.33,
      "density_kg_m3": 2700,
      "load_n": 1000,
      "yield_strength_mpa": 250,
      "mesh_divisions_length": 10
    },
    "knowledge_base_ids": [],
    "evidence_query": null
  }'
```

API example — queue an OpenFOAM preview:

```bash
curl -X POST http://127.0.0.1:8000/prod/simulations/runs \
  -H 'Content-Type: application/json' \
  -d '{
    "tenant_id": "demo",
    "case_card_id": "openfoam_channel_flow_v1",
    "execution_mode": "preview",
    "label": "baseline channel",
    "parameters": {
      "length_m": 1.0,
      "width_m": 0.1,
      "height_m": 0.05,
      "inlet_velocity_m_s": 0.25,
      "kinematic_viscosity_m2_s": 0.000015,
      "density_kg_m3": 1.225,
      "end_time_s": 3.0,
      "time_step_s": 0.002,
      "write_interval_steps": 100,
      "cells_length": 40,
      "cells_width": 10,
      "cells_height": 6
    },
    "knowledge_base_ids": [],
    "evidence_query": null
  }'
```

`knowledge_base_ids` and `evidence_query` optionally attach retrieved BRIXTA evidence to a run. They do not override Case Card validation or prove the engineering assumptions.

### What simulations cannot claim

- They are not certification, regulatory approval, medical advice, structural sign-off, or manufacturing release.
- They do not validate arbitrary geometries/materials/physics.
- They do not currently generate new C++ solvers.
- They do not currently provide automated mesh independence, calibration, uncertainty quantification, sensitivity analysis, or experimental validation.
- They do not currently parse all solver-native result fields into an interactive scientific viewer.
- Cancelling a Celery task sends termination, but robust subprocess-tree cleanup and simulation orphan recovery need further hardening.

### Add a simulation pack

1. Define a narrow physical problem and assumptions.
2. Create a typed, bounded Pydantic parameter model and Case Card in `runtime/simulations/case_cards.py`.
3. Add deterministic compiler, runner, and postprocessor implementations under `plugins/simulation/`.
4. Register all three stages in `runtime/simulations/registry.py`.
5. Pin solver/version/image and commands; never interpolate untrusted shell fragments.
6. Add a dedicated queue and worker image/manifests if resource/runtime isolation differs.
7. Store structured spec, compiler version, solver version, inputs, evidence, logs, hashes, and outputs.
8. Add golden-case, invalid-range, timeout, cancellation, artifact, solver-version, and regression tests.
9. Add dashboard form/result views and MCP report metadata.
10. Have a qualified domain engineer review assumptions and reference results.

Deprecate packs before removal. Existing simulation rows/artifacts retain the Case Card ID, so deletion without a compatibility reader destroys reproducibility.

### Future simulation capability

An approved future workflow can let an AI client propose `SimulationSpec` values using BRIXTA evidence. Deterministic validation/compiler software must remain the authority. Custom C++ development belongs in a separate engineer-reviewed build pipeline: retrieve references, draft a patch, compile/test in a disposable image, review diff, release a versioned solver image, then expose it through a bounded Case Card.

---

## Docker images

### Root `Dockerfile`

Multi-stage Python 3.12 slim image:

- builds `/opt/venv` with worker + RAG requirements;
- copies API, core, plugins, runtime, SDK, MCP, CLI source, and infra;
- installs Node/npm in the runner for Drizzle operations;
- runs as non-root `appuser`;
- defaults to Uvicorn on port 8000.

Build and run the API:

```bash
docker build -f Dockerfile -t brixta-core:2.1.0 .
docker run --rm --env-file .env -p 8000:8000 brixta-core:2.1.0
```

The image copies CLI source but does not install the project through `pip install .`; do not assume the `brixta` console script exists inside it. Use module entry points in manifests or change the image build deliberately.

The same image can run alternate commands:

```bash
docker run --rm --env-file .env brixta-core:2.1.0 \
  python -m celery -A runtime.celery_app.celery worker --loglevel=info --queues=downloader,parser,chunker

docker run --rm --env-file .env -p 8001:8001 brixta-core:2.1.0 \
  python -m api.mcp_server
```

### `Dockerfile.openfoam`

Ubuntu 24.04 + OpenFOAM 13 + BRIXTA API/runtime code. It sources OpenFOAM and starts a concurrency-1 worker on `simulations.openfoam`.

```bash
docker build -f Dockerfile.openfoam -t brixta-openfoam:2.1.0 .
```

Review the upstream repository/key/version and build reproducibility before production. Pin the base image by digest and scan the result.

### `Dockerfile.simulations`

Python 3.12 slim + `calculix-ccx`; starts a concurrency-1 worker on `simulations.calculix`.

```bash
docker build -f Dockerfile.simulations -t brixta-calculix:2.1.0 .
```

### `brixta-dashboard/Dockerfile`

Node 20 Alpine multi-stage Next.js build/runner.

```bash
docker build -f brixta-dashboard/Dockerfile -t brixta-dashboard:2.1.0 brixta-dashboard
docker run --rm -p 3000:3000 \
  -e PYTHON_BACKEND_URL=http://host.docker.internal:8000 \
  brixta-dashboard:2.1.0
```

### Image release rules

- Tag with semantic version and immutable Git SHA; deploy SHA/digest, not only mutable `v5`/`latest`.
- Generate SBOM, sign images, scan OS/Python/npm dependencies.
- Keep API/light/embedding/solver dependency surfaces separated as the project grows.
- Do not bake `.env`, uploads, connection state, secrets, caches, or developer databases into images.

---

## Kubernetes deployment

The `k8s/` folder is a deployment foundation, not a turnkey secure cloud. It assumes an external PostgreSQL service such as Neon and creates in-cluster Redis/MinIO unless you replace them.

### Manifest inventory

| File | Purpose | Current caveat |
|---|---|---|
| `pvc.yaml` | 10 Gi local-path RWO storage | Not shared multi-node storage. |
| `redis.yaml` | Redis service/deployment | No auth, TLS, persistence, probes, or production tuning. |
| `minio.yaml` | MinIO + console services | Hardcoded development credentials/NodePorts; not production-safe. |
| `infisical-secret.yaml` | Syncs Infisical into `app-secrets` | Requires Infisical Operator/CRDs and correct project access. |
| `drizzle-job.yaml` | Schema push Job | Uses `drizzle-kit push`; replace with reviewed migrations for production. |
| `gateway.yaml` | FastAPI deployment/service | Two replicas share RWO assumptions; image tag must be updated. |
| `workers-light.yaml` | downloader/parser/chunker workers | Ensure `REDIS_URL` exists; manifest's `CELERY_BROKER_URL` alone is ignored. |
| `worker-embeddings.yaml` | embeddings/storage worker | Same Redis variable issue; model cache/resources need planning. |
| `scheduler.yaml` | Celery Beat | Apply exactly one unless distributed locking is added. |
| `dashboard.yaml` | Next.js deployment/NodePort | Add stable HTTPS ingress and auth. |
| `mcp-deployment.yaml` | shared MCP gateway | One replica by design until auth/session state is externalized. |
| `mcp-service.yaml` | MCP ClusterIP | Port 80 to gateway. |
| `mcp-ingress.yaml` | MCP HTTPS ingress | Replace host/class/TLS secret; route root so OAuth discovery endpoints work. |
| `mcp-secrets.yaml` | MCP secret template | Do not commit real secrets; prefer Infisical/External Secrets. |
| `worker-simulations.yaml` | CalculiX worker | Replace placeholder registry image/tag. |
| `worker-openfoam.yaml` | OpenFOAM worker | Replace placeholder registry image/tag. |
| `hpa.yaml` | gateway HPA | Requires metrics-server. |
| `vpa-embeddings.yaml` | embedding VPA | Requires VPA CRDs/controller; verify policy before enabling. |

### Prerequisites

- Kubernetes 1.28+ recommended.
- `kubectl` context pointing at the intended cluster.
- DNS zone and TLS issuer/certificate.
- ingress controller matching the manifest class.
- metrics-server for HPA.
- Infisical Operator if using the included CRD; [Infisical's operator](https://infisical.com/docs/integrations/platforms/kubernetes/infisical-secret-crd) materializes a Kubernetes Secret from managed secrets.
- VPA controller only if applying the VPA manifest.
- published core/dashboard/CalculiX/OpenFOAM images.
- external pgvector PostgreSQL.
- a production Redis/MinIO plan or reviewed replacements.

### Preflight

```bash
kubectl config current-context
kubectl cluster-info
kubectl get nodes -o wide
kubectl api-resources | grep -E 'infisical|verticalpodautoscaler'
kubectl get storageclass
kubectl get ingressclass
```

Review every manifest and replace:

- image repository/tags with immutable digests;
- namespaces;
- hostnames/TLS secret names/ingress class;
- storage class/capacity/access mode;
- resource requests/limits;
- development credentials;
- public NodePorts;
- Infisical project/environment/path;
- environment names and service DNS.

### Production secret set

The `app-secrets` Kubernetes Secret should contain at least the variables each workload needs, commonly:

```text
DATABASE_URL
REDIS_URL=redis://redis-service:6379/0
ARTIFACT_BACKEND=minio
MINIO_ENDPOINT=minio-service:9000
MINIO_ACCESS_KEY
MINIO_SECRET_KEY
MINIO_BUCKET
MINIO_SECURE
EMBEDDING_PLUGIN
EMBEDDING_MODEL
BRIXTA_API_PUBLIC_URL
BRIXTA_DASHBOARD_PUBLIC_URL
BRIXTA_MCP_PUBLIC_URL
BRIXTA_MCP_AUTH_MODE=jwt
BRIXTA_MCP_JWKS_URI
BRIXTA_MCP_JWT_ISSUER
BRIXTA_MCP_JWT_AUDIENCE
BRIXTA_MCP_JWT_ALGORITHM
BRIXTA_MCP_TENANT_CLAIM
```

Do not place Infisical client credentials in the synced application Secret unless an application actually needs to call Infisical.

### Explicit apply order

After the readiness gates and migration fix:

```bash
# 1. Secret synchronization and storage/services
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/minio.yaml
kubectl apply -f k8s/infisical-secret.yaml
kubectl wait --for=create secret/app-secrets --timeout=120s

# 2. Reviewed migration job (replace schema push for real production)
kubectl delete job brixta-drizzle-migrate --ignore-not-found
kubectl apply -f k8s/drizzle-job.yaml
kubectl wait --for=condition=complete job/brixta-drizzle-migrate --timeout=300s
kubectl logs job/brixta-drizzle-migrate

# 3. API and ingestion runtime
kubectl apply -f k8s/gateway.yaml
kubectl apply -f k8s/workers-light.yaml
kubectl apply -f k8s/worker-embeddings.yaml
kubectl apply -f k8s/scheduler.yaml

# 4. Dashboard
kubectl apply -f k8s/dashboard.yaml

# 5. Shared MCP
kubectl apply -f k8s/mcp-service.yaml
kubectl apply -f k8s/mcp-deployment.yaml
kubectl apply -f k8s/mcp-ingress.yaml

# 6. Simulation workers
kubectl apply -f k8s/worker-simulations.yaml
kubectl apply -f k8s/worker-openfoam.yaml

# 7. Autoscaling only after prerequisites/policies are verified
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/vpa-embeddings.yaml
```

### Verify

```bash
kubectl get deploy,sts,job,pod,svc,ingress,pvc
kubectl get events --sort-by=.lastTimestamp | tail -n 50
kubectl logs deploy/gateway --tail=200
kubectl logs deploy/mcp-gateway --tail=200
kubectl logs deploy/worker-embeddings --tail=200
kubectl logs deploy/scheduler --tail=200
kubectl rollout status deploy/gateway --timeout=180s
kubectl rollout status deploy/mcp-gateway --timeout=180s
curl -fsS https://api.example.com/health
curl -i https://mcp.example.com/.well-known/oauth-protected-resource/mcp
```

Resource names may differ; use `kubectl get` to confirm names declared by the manifests.

### Production MCP on Kubernetes

Use `BRIXTA_MCP_AUTH_MODE=jwt`, a stable public URL, valid TLS, and IdP discovery/JWKS. The ingress must route both `/mcp` and OAuth metadata endpoints at `/.well-known/...`; the current host-wide `/` prefix is intended to allow that. Configure long-lived stream timeouts and disable proxy buffering if required by your ingress controller.

The current one-replica MCP deployment avoids in-memory session/registration split. Before scaling it horizontally, externalize session/authorization state or prove the chosen FastMCP transport is stateless/sticky enough, then add readiness, PDB and load tests.

### Upgrade and rollback

1. Back up database/object storage and test restore.
2. Run forward migrations separately and observe.
3. Deploy by immutable image digest.
4. Watch rollout, queue depths, error rates, DB connections, MCP tool calls, and semantic canaries.
5. Roll back application image with `kubectl rollout undo deployment/<name>` only if the database change remains backward compatible.
6. Prefer roll-forward database fixes; destructive schema rollback is unsafe.

### Kubernetes production hardening backlog

- Namespaces, service accounts and least-privilege RBAC per workload.
- NetworkPolicies between ingress/API/MCP/workers/Redis/MinIO/egress.
- Pod security contexts, read-only roots where possible, seccomp, dropped capabilities.
- PDBs, topology spread/anti-affinity and disruption strategy.
- Managed PostgreSQL/Redis/object store or HA operators.
- External secret rotation and workload identity rather than long-lived client secrets.
- API/dashboard ingress with TLS, WAF/rate limiting and auth.
- Central logs, OpenTelemetry traces, Prometheus metrics, alerts and SLOs.
- Queue autoscaling based on depth (for example KEDA), not only CPU.
- Model cache strategy and GPU scheduling where needed.
- Simulation sandbox/resource quotas and artifact size limits.
- Backup/PITR/restore drills.
- Egress allowlists for source downloads/Hugging Face.
- Signed images/admission policy and vulnerability gates.

---

## Infisical and `start.sh`

`start.sh` is a convenience bootstrap for an already prepared Kubernetes cluster. It is not a full production installer.

### What it currently does

1. Reads `.env` using a simple shell export expression.
2. verifies `INFISICAL_CLIENT_ID` and `INFISICAL_CLIENT_SECRET`;
3. creates/updates the `universal-auth-credentials` Kubernetes Secret;
4. applies PVC and `k8s/infisical-secret.yaml`;
5. waits for synced `app-secrets`;
6. starts Redis and MinIO;
7. applies/waits for the Drizzle Job;
8. applies gateway, light workers, embedding worker, dashboard, HPA and VPA.

It does **not** currently apply scheduler, MCP manifests, or simulation workers. Apply those explicitly after reviewing them.

### Use it

Install the Infisical Operator and configure a Universal Auth machine identity with access to the project/environment/path referenced by the CRD. Then:

```bash
chmod +x start.sh
./start.sh
```

The `.env` parser in `start.sh` is fragile for values containing spaces, shell metacharacters, `#`, or complex quoting. Prefer passing environment variables from a secure shell/CI secret store, or replace the parser with a robust dotenv loader before relying on it.

After it succeeds:

```bash
kubectl apply -f k8s/scheduler.yaml
kubectl apply -f k8s/mcp-service.yaml
kubectl apply -f k8s/mcp-deployment.yaml
kubectl apply -f k8s/mcp-ingress.yaml
kubectl apply -f k8s/worker-simulations.yaml
kubectl apply -f k8s/worker-openfoam.yaml
```

The Infisical Operator watches its CRD and creates/updates `app-secrets`; inspect status without printing secret values:

```bash
kubectl get infisicalsecret
kubectl describe infisicalsecret app-secrets
kubectl get secret app-secrets
```

Never run `kubectl get secret ... -o yaml` into CI/public logs.

---

## GitHub Actions and releases

### Current workflow

`.github/workflows/docker-image.yml` runs on pushes to `main`, configures Buildx, logs into Docker Hub, obtains Infisical secrets, and builds/pushes core and dashboard images.

Current release inconsistencies:

- core is tagged with a mutable `v5`-style tag;
- dashboard is pushed with a different `v1` tag while Kubernetes expects another tag;
- CalculiX/OpenFOAM images are not built;
- package version is `2.1.0` while some simulation manifest placeholders refer to another version;
- workflow does not run unit tests, type/lint/build checks, migration-from-zero, semantic/MCP smoke tests, scans, SBOM/signing, or package publication.

### Minimum CI pipeline before production

1. Secret scan and dependency lock validation.
2. Python compile/lint/type checks and unit tests on 3.11–3.13.
3. Dashboard lint/type/build.
4. Fresh pgvector database migration test and target-schema comparison.
5. Redis/Celery ingestion integration test with a small deterministic fixture.
6. Knowledge search and MCP auth/tenant isolation tests.
7. Simulation golden preflight/compiler tests; solver smoke tests in dedicated jobs.
8. Build all four images.
9. Generate SBOM, scan and sign.
10. Push semantic version + Git SHA tags/digests.
11. Deploy to staging, run canaries, then gated production promotion.

### Python package release

The BRIXTA package is defined by `pyproject.toml`. Update version deliberately and ensure generated `brixta.egg-info` is not committed.

Build locally:

```bash
source Resea/bin/activate
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
python -m venv /tmp/brixta-release-test
/tmp/brixta-release-test/bin/python -m pip install \
  -r requirements-api.txt -r requirements-rag.txt dist/*.whl
/tmp/brixta-release-test/bin/brixta --help
```

Recommended release sequence:

1. update `pyproject.toml` version and changelog/release notes;
2. run full CI and build artifacts from a clean checkout;
3. create an annotated signed Git tag such as `v2.1.0`;
4. push the tag and create a GitHub Release with checksums/SBOM;
5. publish to PyPI using Trusted Publishing from a protected GitHub environment if public package distribution is intended;
6. build/publish matching container images and update manifests by digest;
7. never publish a package containing `.env`, runtime state, uploads, caches, or secrets.

The current workflow does not implement GitHub Release or PyPI publication; adding it is future work.

---

## Testing

### Fast static checks

```bash
python -m compileall -q api brixta_cli brixta_mcp brixta_sdk core plugins runtime tests
python -m unittest discover -s tests -v
```

Current tests cover plugin defaults/duplicates/overrides/unknown IDs, source repository behavior, knowledge-service behavior, and task recovery. They are a foundation, not production coverage.

### Registry smoke tests

```bash
python -c "from core.plugin_loader import registry; print(registry.validate_selection({}))"
python -c "from core.plugin_loader import registry; from pprint import pprint; pprint(registry.list())"
```

### Dashboard checks

```bash
cd brixta-dashboard
npm ci
npm run lint
npm run build
```

### Operational smoke test

1. Run a small text/file ingestion.
2. Observe every job state through `completed`.
3. Confirm `document_chunks` model/dimension match actual vectors.
4. Search from the knowledge page and via API.
5. Run `brixta doctor`.
6. Start local generic MCP and verify all seven tools.
7. Run both simulation preflights.
8. If solver images are available, run one golden solver case for each.

### Tests still needed

- clean database migration from zero and upgrade from the current production shape;
- tenant authorization/RLS and object-prefix isolation;
- OAuth/JWT/JWKS rotation and denial cases;
- source scheduling idempotency/timezone/DST;
- recursive crawler once implemented;
- crash/restart/orphan recovery across every stage and simulations;
- large-file/zip-bomb/malicious document handling;
- model revision/dimension drift and semantic quality evaluation;
- MinIO failure/resume/retention;
- Kubernetes probes/rollouts/chaos and restore drills;
- load/cost tests for API, queues, pgvector and MCP streaming.

---

## Troubleshooting

### Diagnostic order

Always identify which boundary failed:

```text
browser -> Next proxy -> FastAPI -> PostgreSQL/Redis/MinIO
                                     -> Celery queue -> worker -> plugin
ChatGPT -> public DNS/TLS/ingress/tunnel -> MCP -> auth -> knowledge service
Simulation API -> Redis -> solver worker -> executable -> artifact backend
```

Preserve the first meaningful error. Repeated restarts can hide the cause.

### Python and dependencies

| Symptom | Cause | Fix |
|---|---|---|
| `unsupported operand type(s) for |` on `Path | None` | Python 3.9 launched instead of the venv. | `source Resea/bin/activate`; verify `python --version` and `which python`; recreate with 3.11. |
| Package requires `<3.14` | Environment was built with Python 3.14. | Recreate `Resea` with 3.11–3.13. |
| `brixta: command not found` | Project not installed/editable in active venv. | `python -m pip install -e .`; `rehash`; verify `which brixta`. |
| `numpy==2.5.0` unavailable | Historical freeze/platform/Python mismatch. | Use maintained requirement groups and supported Python. |
| Transformers/Docling conflict | Unreviewed freeze selected incompatible versions. | Install `requirements-workers.txt`/`requirements-rag.txt`; keep solver images pinned/tested. |
| Nomic asks for `trust_remote_code=True` | Model has custom code. | Use the reviewed/pinned model profile; never globally trust arbitrary models. |
| Missing `einops` | Nomic remote model dependency absent. | Install `requirements-rag.txt`/workers group in the process doing embeddings. |
| Metal `MTLCompilerService` crash | macOS MPS/Metal process instability, often amplified by forked workers. | Use CPU profile, concurrency 1, restart worker; do not fork multiple heavy models. |
| Worker killed/SIGABRT/OOM | Model/parser memory multiplied by concurrency. | Reduce concurrency, split queues, increase memory, use dedicated worker, inspect OS/container OOM events. |

### Database

| Symptom | Cause | Fix |
|---|---|---|
| `column embedding_model does not exist` | Database predates multi-model schema. | Back up, run reviewed forward migration, verify dimensions; do not patch ad hoc repeatedly. |
| `column context_json does not exist` | Database predates recovery schema. | Reconcile migration history with `schema.ts` and migrate. |
| `relation ... does not exist` | Wrong database/schema/migrations. | Print safe DB host/name, check search path and `BrResearch`, run reviewed migrations. |
| Vector dimension error | Query and stored embeddings are incompatible or a bounded legacy vector column remains. | Inspect `vector_dims`, model/dimension fields; re-embed or migrate safely. |
| Semantic search is slow | Exact scan/no ANN index. | Measure; partition/index by profile, limit scope, add evaluated ANN/hybrid retrieval. |

### API/dashboard

| Symptom | Cause | Fix |
|---|---|---|
| Next `fetch failed`, `ECONNREFUSED 127.0.0.1:8000` | API is stopped or `PYTHON_BACKEND_URL` is wrong. | Start Uvicorn or correct the server-side URL. |
| Knowledge toggle returns 405 | Next proxy lacks PUT export. | Add/redeploy PUT forwarding. |
| Plugin selectors are empty | `/plugins` unreachable/error or stale dashboard build. | Check API registry response, proxy, browser network log; rebuild dashboard. |
| Kubernetes page shows 500 | No cluster credentials/connectivity. | That UI was removed; operate Kubernetes through deployment tooling, not anonymous dashboard controls. |
| Docker operations fail in K8s | Pod cannot/should not access host Docker socket. | Do not mount the socket in production; remove/protect the feature. |

### Jobs and Celery

| Symptom | Cause | Fix |
|---|---|---|
| Job stays `queued` | No worker consumes `downloader`, wrong Redis URL, or task not published. | Inspect workers/queues/API logs and `REDIS_URL`. |
| Job stays `embedding` | Embedding worker crashed/was killed or Beat/reconciler is absent. | Inspect worker/OOM; start Beat; after timeout reconciler marks failed. |
| Old jobs never change | They predate recovery metadata or reconciler cannot correlate them. | Preserve history, migrate schema, mark truly orphaned jobs through an audited operator action; do not falsely mark completed. |
| Repeats forever | Retry settings/multiple Beat instances/custom task behavior. | Confirm attempt/run limits and run exactly one Beat. |
| Scheduled sources do not run | Beat stopped, invalid cron/timezone, source disabled, JSON state not shared. | Check Beat log, source record and timezone; move to shared DB for multi-pod. |

### MCP and Cloudflare

| Symptom | Meaning | Action |
|---|---|---|
| Public 502 | Edge/tunnel cannot reach the local MCP origin, or the origin is starting/stale. | `brixta connection status`; inspect both logs/PIDs/port; rerun same connect command to recheck/reuse. |
| `Errno 8 nodename nor servname provided` | macOS resolver cannot resolve the newly created quick-tunnel hostname yet, sometimes after a negative DNS cache. | Compare `dig @1.1.1.1` with Python resolver; flush caches or use stable production DNS. |
| CLI waits for public hostname | Quick-tunnel DNS/edge propagation is incomplete. | Leave recorded processes running; rerun same command. Do not create many tunnels. |
| Local generic client gets 401 | A stale OAuth-mode gateway occupies port 8001. | `brixta disconnect`; verify no listener; reconnect with `client --local`. |
| 406 Accept error | Raw MCP client omitted SSE media type. | Send `Accept: application/json, text/event-stream`. |
| FastMCP `AccessToken` type mismatch | Dependency SDK token class differs from provider return type. | Use repository compatibility provider and one pinned dependency set; rebuild/restart every MCP runtime. |
| `ClientRegistrationOptions` private import warning | Imported from old FastMCP location. | Use `mcp.server.auth.settings`. |
| `authorization_servers` expects `AnyHttpUrl` | Pydantic type requires URL objects. | Construct validated `AnyHttpUrl` values, not plain strings. |
| Tools missing | Old editable install/process/image. | Reinstall/rebuild, restart, compare expected seven tools. |
| ChatGPT works then fails | Local machine slept, network changed, quick tunnel/process died, or URL changed. | Local quick tunnel is disposable. Reconnect developer app to the new URL, or deploy stable production MCP. |

Useful commands:

```bash
brixta connection status
tail -n 200 .brixta/mcp.log
tail -n 200 .brixta/tunnel.log
lsof -nP -iTCP:8001 -sTCP:LISTEN
pgrep -fl 'cloudflared|api.mcp_server|brixta_mcp'
dig +short YOUR_HOST.trycloudflare.com @1.1.1.1
python -c 'import socket; print(socket.getaddrinfo("YOUR_HOST.trycloudflare.com", 443))'
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
networksetup -getdnsservers Wi-Fi
```

If you intentionally changed macOS Wi-Fi DNS to `1.1.1.1`/`8.8.8.8`, restore automatic/default DNS with:

```bash
sudo networksetup -setdnsservers Wi-Fi empty
```

Do not use a fabricated hostname such as `something.trycloudflare.com` to test existence; random Quick Tunnel names only exist after Cloudflare creates them.

### MinIO/Redis

| Symptom | Cause | Fix |
|---|---|---|
| MinIO access denied | Wrong credential precedence/policy/bucket. | Remove root vars from app, validate limited key and bucket policy, check endpoint/TLS. |
| Objects local but missing in another pod | Local backend/RWO filesystem. | Use shared MinIO/S3 and consistent configuration. |
| Redis page unavailable | Redis unreachable or URL points to localhost inside container. | Use service DNS (`redis-service`) in K8s and inspect NetworkPolicy/auth. |
| Celery online but no tasks | Wrong queues/routing/Redis DB. | Inspect worker queue list and shared `REDIS_URL`. |

### Simulations

| Symptom | Cause | Fix |
|---|---|---|
| Run stays queued | No worker consumes its solver queue. | Start/publish the dedicated worker and verify Redis URL. |
| Executable not found | Solver absent or command env wrong. | Use the dedicated image or set executable variable. |
| Preview queued unexpectedly | Current routing sends all runs to solver-specific queue. | Keep worker running; future improvement can execute preflight previews on a light queue. |
| VTK/FRD not visualized | Current UI stores native results but only renders preview schema. | Download native artifact/use ParaView/solver tooling; implement a validated parser later. |

---

## How to extend or remove components

### Add a runtime task

1. Put domain logic in `runtime/<domain>/service.py`.
2. Put a thin Celery wrapper in `runtime/tasks/`.
3. Define stable task name, queue, serialization contract, timeouts and retry classification.
4. Add route configuration in `runtime/celery_app.py`.
5. Update worker commands/manifests and observability.
6. Add idempotency/correlation and durable status updates.
7. Test duplicate delivery, crash, retry, cancellation and deployment-version overlap.

### Delete a runtime task

Stop producers first, wait for/handle queued messages, deploy workers that can recognize old task names, migrate persisted state, then remove routing/code in a later release. Deleting task code while old messages exist produces “unregistered task” failures.

### Add a source connector

Prefer a downloader plugin if it maps naturally to the ingestion contract. For stateful incremental SaaS connectors, add a connector service with credential references, cursor/checkpoint storage, rate-limit handling, webhooks/polling, deletion semantics and audit. Do not store OAuth refresh tokens in `sources.json`.

### Add a storage backend

Implement the SDK storage contract, define how chunks/model metadata/citations/deletion/replay work, register it, add health/migration/export tests, and ensure retrieval has a matching adapter. A write-only storage plugin does not automatically create ready RAG.

### Add a dashboard page

1. add an App Router page under `brixta-dashboard/app/(dashboard)/`;
2. keep privileged data access server-side or through the same-origin proxy;
3. add typed API models/hooks and loading/empty/error states;
4. add navigation only when the page is operational;
5. add auth/role gating and tests;
6. never expose raw secrets or unbounded logs.

### Change the fixed pipeline

Adding a new stage is an architecture migration. Update SDK context/contracts, registry stage enumeration, API schemas, Celery routes/tasks, recovery state machine, persisted contexts, dashboard selection, tests and old-job replay compatibility. Do not make arbitrary user-controlled ordering until stage input/output types and a validated DAG compiler exist.

---

## Strengths, weaknesses, and roadmap

### Architectural strengths

- Integration-first boundaries minimize reinvention.
- Registry validation gives controlled modularity.
- Durable PostgreSQL job state survives queue/UI restarts.
- Model-aware vector storage avoids silent cross-model comparison.
- Shared MCP eliminates per-knowledge-base processes/reconnections.
- Separate workers isolate lightweight, ML and solver workloads.
- Deterministic Case Cards constrain simulation automation.
- Self-hostable surfaces exist for Docker and Kubernetes.

### Current weaknesses

- Authentication/tenant authorization is unfinished.
- Database migration history and Compose init need reconciliation.
- Source/settings control-plane files are not multi-replica safe.
- Single-page HTTP fetch is not a crawler.
- Exact vector scan lacks large-scale indexing/hybrid retrieval/evaluation.
- Infrastructure manifests are development-biased and version-inconsistent.
- Local Quick Tunnel availability is inherently unstable.
- Simulation result parsing/recovery/validation breadth is early.
- No complete observability, quotas, billing, audit or policy plane.
- CLI package/container release automation is incomplete.

### Prioritized roadmap

#### Phase 0 — safe deployment

- Rotate secrets and clean repository artifacts/history.
- Reconcile migrations and add fresh/upgrade tests.
- Implement dashboard/API OIDC, RBAC, tenant derivation and RLS.
- Fix proxy PUT, image/tag mismatches, Redis env and missing Compose init.
- Replace production Redis/MinIO/storage assumptions.
- Stable HTTPS API/dashboard/MCP ingress with JWT auth.
- CI release gates, backups and observability.

#### Phase 1 — ingestion quality

- PostgreSQL source/settings repositories.
- Recursive/sitemap/Git/Drive/SharePoint/Slack connector plugins.
- Incremental sync, hashes, versions, deletion/tombstone semantics.
- Rich chunk/page/section/citation metadata.
- Evaluation sets, hybrid search, reranking and model migration tools.
- Per-tenant quotas, cost and lineage dashboards.

#### Phase 2 — client/product experience

- Published ChatGPT plugin and hosted “Use with ChatGPT” flow.
- Stable generic-client connection instructions/discovery.
- Durable notifications and audit/event inbox.
- Access grants per user/group/knowledge base.
- API keys/service accounts and self-service tenant administration.

#### Phase 3 — Simulation Lab platform

- Simulation run recovery/retry/idempotency.
- Result-field parsers and scientific viewers.
- Mesh/convergence checks, parameter sweeps and uncertainty analysis.
- Versioned Case Card marketplace with domain review/signatures.
- More solvers through isolated integration packs.
- Evidence-to-spec assistance that never bypasses deterministic validation.

#### Phase 4 — operating system for AI integrations

- Plugin SDK/CLI scaffolding, signing, compatibility and marketplace.
- Declarative typed pipeline DAGs.
- Multi-region control/data planes.
- Policy, billing, licensing, update channels and enterprise audit.
- Managed cloud plus production-grade self-hosted Helm distribution.

---

## When to split the monorepo

Keep the monorepo while contracts change quickly and one team benefits from atomic updates. Split only when ownership, release cadence, security boundary, dependency weight, or deployment independence is real.

### Likely future repositories

| Future repository | Split trigger | Contract with core |
|---|---|---|
| `brixta-core` | API/runtime/control-plane has stable domain ownership | Versioned REST/events/database migrations. |
| `brixta-sdk` | External plugin authors need a small dependency | Semantic-versioned Python interfaces and compatibility matrix. |
| `brixta-plugins` or per-plugin repos | Plugins have independent owners/heavy dependencies/licenses | Signed manifests, SDK range, capability/health contract. |
| `brixta-mcp` | MCP security/release cadence becomes independent | Versioned runtime service APIs, token/audit contract. |
| `brixta-dashboard` | Frontend team/release pipeline is independent | Published OpenAPI/typed client and auth contract. |
| `brixta-simulation-packs` | Solver packs require domain governance/licensing/images | Case Card schema, artifact/run event contract. |
| `brixta-deploy` | Helm/Terraform/operator evolves separately | Immutable image versions and configuration schema. |

### Communication model after a split

- API-to-database changes use owned forward migrations.
- API-to-workers use versioned task/event envelopes; support rolling overlap.
- Core-to-plugins use SDK version ranges and capability discovery.
- Dashboard-to-core uses versioned OpenAPI and generated types.
- MCP-to-core uses authenticated internal service APIs or a read-optimized repository—not shared undocumented internals.
- Simulation workers consume immutable specs and emit immutable artifact manifests/events.
- Every contract has compatibility tests and deprecation windows.

Do not split only because the folder tree is large. A premature multi-repo architecture makes atomic security/schema/runtime changes harder.

---

## Contributing

### Development rules

- Preserve tenant/model/dimension/provenance on every data path.
- Keep transport handlers thin; put domain logic in services.
- Make Celery work idempotent and status updates durable.
- Pin/review remote code and solver versions.
- Never add a dashboard control before its authorization model.
- Add migrations rather than editing applied migrations.
- Avoid heavyweight imports in processes that do not need them.
- Treat plugin IDs, task names, API paths, MCP tools and Case Card IDs as versioned contracts.
- Add documentation and tests in the same change.

### Definition of done

A change is done only when:

1. behavior and failure modes are specified;
2. tenant/security boundaries are enforced;
3. data/schema/backward compatibility is addressed;
4. dependencies and images are updated deliberately;
5. unit/integration tests cover success, invalid input and failure/retry;
6. metrics/logs/audit are useful;
7. local and Kubernetes instructions are current;
8. rollback/deprecation is defined;
9. no secrets/generated artifacts are included;
10. README/API/schema versions agree.

---

## Glossary

| Term | Meaning in BRIXTA |
|---|---|
| Artifact | Uploaded, intermediate, generated, log, report or solver file stored locally/MinIO. |
| Case Card | Versioned bounded simulation problem with typed parameters and approved compiler/solver/postprocessor. |
| Chunk | Searchable text unit plus embedding and provenance. |
| Control plane | APIs/state that define sources, jobs, access, settings and runs. |
| Embedding profile | Model plus dimension, prefixes, normalization, revision/trust and device rules. |
| Job | Durable ingestion attempt. A retry creates a linked new job. |
| Knowledge base | Completed ingestion job with at least one persisted searchable chunk. |
| MCP | Model Context Protocol transport/tools used by compatible AI clients. |
| `brixta://knowledge/...` | Stable internal handle, not a network endpoint. |
| Plugin | Registered implementation of a stable SDK stage contract. |
| Quick Tunnel | Ephemeral development-only Cloudflare URL created by the local CLI. |
| RAG | Retrieval-augmented generation: BRIXTA retrieves evidence; the connected model generates the answer. |
| SimulationSpec | Validated structured input compiled deterministically into a solver case. |
| Tenant | Logical customer/workspace scope that production identity and data policies must enforce. |

---

## Final operator checklist

### Local development

- [ ] Python 3.11–3.13 venv active.
- [ ] Maintained requirements + editable package installed.
- [ ] `.env` contains rotated/local values.
- [ ] PostgreSQL/pgvector, Redis and MinIO reachable.
- [ ] Reconciled migrations applied.
- [ ] API, correct queue workers, Beat and dashboard running.
- [ ] `brixta doctor` passes.
- [ ] One ingestion, search, MCP tool list and simulation preflight pass.

### Production

- [ ] All [Production readiness gates](#production-readiness-gates) closed.
- [ ] Fresh and upgrade database migrations pass.
- [ ] OIDC/RBAC/tenant enforcement/RLS tested.
- [ ] Stable TLS API/dashboard/MCP domains configured.
- [ ] JWT discovery/JWKS/issuer/audience/tenant claims verified.
- [ ] Managed/HA PostgreSQL, Redis and object storage selected and restored from backup in a drill.
- [ ] Immutable signed/scanned images published for core, dashboard and both solvers.
- [ ] Kubernetes secrets, RBAC, policies, resources, probes, PDBs and ingress reviewed.
- [ ] Scheduler exactly once; all required queues have workers.
- [ ] Logs/metrics/traces/alerts/audit and SLOs active.
- [ ] ChatGPT developer/published connection tested without Quick Tunnel.
- [ ] Rollback and incident runbooks exercised.

BRIXTA becomes powerful by preserving these boundaries: **integrations are replaceable, contracts are stable, state is durable, tenant access is explicit, and automation never bypasses validation.**
