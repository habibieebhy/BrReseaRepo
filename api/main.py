import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl

from brixta_sdk.context import PipelineContext
from runtime.celery_app import celery
from api.prod_api.router import router as prod_router
from core.exceptions import ValidationError
from core.plugin_loader import PLUGIN_STAGES, registry
from api.sources import router as sources_router
from runtime.settings import RuntimeSettingsRepository
from runtime.jobs.repository import JobRepository


class IngestionRequest(BaseModel):
    source_url: HttpUrl
    tenant_id: str = Field(min_length=1)
    plugins: dict[str, str] = Field(default_factory=dict)
    config: dict = Field(default_factory=dict)


app = FastAPI(
    title="BRIXTA Core API",
    description="High-performance ingestion entry point.",
    version="2.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(
    prod_router,
    prefix="/prod",
    tags=["Production"],
)
app.include_router(sources_router)

@app.get("/health", status_code=status.HTTP_200_OK)
async def health():
    return {
        "status": "healthy",
        "database": "Neon PostgreSQL",
        "service": "brixta-core",
    }


@app.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest(
    request: IngestionRequest,
):

    # ----------------------------------------------------
    # Build Pipeline Context
    # ----------------------------------------------------

    context = PipelineContext(
        job_id=str(uuid.uuid4()),
        tenant_id=request.tenant_id,
        source_type="url",
        source_target=str(request.source_url),
        plugins={**RuntimeSettingsRepository.get().get("default_plugins", {}), **request.plugins},
        config={"embedding_model": RuntimeSettingsRepository.get().get("embedding_model", "nomic-ai/nomic-embed-text-v1.5"), "pipeline_order": RuntimeSettingsRepository.get().get("pipeline_order", list(PLUGIN_STAGES)), **request.config},
    )

    try:
        context.plugins = registry.validate_selection(context.plugins)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # ----------------------------------------------------
    # Dispatch Runtime
    # ----------------------------------------------------

    JobRepository.create(context)

    try:
        result = celery.send_task(
            "runtime.tasks.ingestion.test_ingestion",
            args=[context.to_dict()],
            queue="downloader",
        )
        JobRepository.mark_dispatched(context.job_id, result.id, "downloader")

        print("=" * 60)
        print("TASK ID:", result.id)
        print("TASK:", "runtime.tasks.ingestion.test_ingestion")
        print("QUEUE:", "downloader")
        print("=" * 60)

    except Exception as e:
        JobRepository.record_failure(
            context.job_id,
            f"Celery dispatch failed: {e}",
            retryable=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Celery dispatch failed: {e}",
        )

    return {
        "message": "Pipeline queued successfully.",
        "job_id": context.job_id,
        "tenant_id": context.tenant_id,
        "status": "queued",
        "plugins": context.plugins,
    }


@app.post("/ingest/file", status_code=status.HTTP_202_ACCEPTED)
async def ingest_file(
    file: UploadFile = File(...),
    tenant_id: str = Form(...),
    parser: str = Form("docling"),
    chunker: str = Form("docling-hybrid"),
    embedding: str = Form("sentence-transformers"),
    storage: str = Form("pgvector"),
    embedding_model: str = Form("nomic-ai/nomic-embed-text-v1.5"),
):
    suffix = Path(file.filename or "upload").suffix.lower()
    allowed = {".pdf", ".docx", ".pptx", ".xlsx", ".html", ".htm", ".md", ".txt"}
    if suffix not in allowed:
        raise HTTPException(status_code=415, detail=f"Unsupported file type '{suffix or 'unknown'}'.")
    job_id = str(uuid.uuid4())
    upload_dir = Path("storage/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    upload_path = upload_dir / f"{job_id}{suffix}"
    size = 0
    with upload_path.open("wb") as destination:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > 50 * 1024 * 1024:
                destination.close()
                upload_path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="Maximum upload size is 50 MiB.")
            destination.write(chunk)
    selection = {
        "downloader": "local-file",
        "parser": parser,
        "chunker": chunker,
        "embedding": embedding,
        "storage": storage,
    }
    try:
        selection = registry.validate_selection(selection)
    except ValidationError as exc:
        upload_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    context = PipelineContext(
        job_id=job_id,
        tenant_id=tenant_id,
        source_type="local_file",
        source_target=str(upload_path.resolve()),
        plugins=selection,
        config={"embedding_model": embedding_model},
        metadata={"filename": file.filename, "size_bytes": size},
    )
    JobRepository.create(context)
    try:
        result = celery.send_task("runtime.tasks.ingestion.test_ingestion", args=[context.to_dict()], queue="downloader")
        JobRepository.mark_dispatched(context.job_id, result.id, "downloader")
    except Exception as exc:
        JobRepository.record_failure(
            context.job_id,
            f"Celery dispatch failed: {exc}",
            retryable=True,
        )
        raise HTTPException(status_code=503, detail=f"Could not queue file ingestion: {exc}") from exc
    return {"message": "File pipeline queued successfully.", "job_id": job_id, "tenant_id": tenant_id, "status": "queued", "plugins": selection, "filename": file.filename}


@app.get("/plugins", status_code=status.HTTP_200_OK)
async def list_plugins(stage: str | None = None):
    if stage is not None and stage not in PLUGIN_STAGES:
        raise HTTPException(status_code=422, detail=f"Unknown plugin stage '{stage}'.")
    return {"plugins": registry.list(stage)}
