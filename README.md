# BRIXTA Research Pipeline

A modular, event-driven research ingestion pipeline designed for scalable document acquisition, parsing, semantic chunking, embedding generation, and vector storage.

## Architecture

```text
Client
   │
   ▼
FastAPI Gateway
   │
   ▼
Neon PostgreSQL (Job Registration)
   │
   ▼
Celery + Redis
   │
   ▼
Extraction Worker
   │
   ▼
Docling
   │
   ▼
Markdown
   │
   ▼
Chunking Engine
   │
   ▼
Embedding Engine
   │
   ▼
Neon PostgreSQL (pgvector)
```

## Project Structure

```text
BRIXTAresearchPipeline/
├── Resea/                  # Python Virtual Environment
├── infra/                  # Drizzle ORM Schema, Migrations & Infrastructure
│   ├── drizzle/
│   ├── drizzle.config.ts
│   └── schema.ts
│
├── gateway/                # FastAPI REST Gateway
│   └── main.py
│
├── shared/                 # Shared Python Components
│   ├── database.py         # Neon PostgreSQL Connection
│   ├── schemas.py          # Pydantic Models
│   └── config.py
│
├── workers/                # Celery Background Workers
│   ├── celery_app.py
│   ├── tasks/
│   ├── services/
│   └── utils/
│
├── .env
├── requirements.txt
└── README.md
```

## Technology Stack

| Layer             | Technology           |
| ----------------- | -------------------- |
| API               | FastAPI              |
| Validation        | Pydantic             |
| Database          | Neon PostgreSQL      |
| Schema Management | Drizzle ORM          |
| Queue             | Redis                |
| Worker Engine     | Celery               |
| Parsing           | Docling              |
| Embeddings        | OpenAI / HuggingFace |
| Vector Storage    | pgvector             |
| Container Runtime | Docker + Colima      |

## Current Progress

* ✅ FastAPI Gateway
* ✅ Neon PostgreSQL
* ✅ Drizzle ORM Schema
* ✅ pgvector
* ✅ Pydantic Models
* ✅ PostgreSQL Integration
* ✅ Redis Infrastructure

## Roadmap

* [ ] Celery Worker
* [ ] Document Downloader
* [ ] Docling Parser
* [ ] Markdown Cleaner
* [ ] Hybrid Chunking Engine
* [ ] Embedding Generation
* [ ] Vector Storage
* [ ] Semantic Search
* [ ] Research Retrieval API

```
```
