import uuid

from fastapi import FastAPI, HTTPException, status
from pydantic import HttpUrl

from brixta_sdk.context import PipelineContext
from runtime.celery_app import celery


app = FastAPI(
    title="BRIXTA Core API",
    description="High-performance ingestion entry point.",
    version="2.0.0",
)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health():
    return {
        "status": "healthy",
        "database": "Neon PostgreSQL",
        "service": "brixta-core",
    }


@app.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest(
    source_url: HttpUrl,
    tenant_id: str,
):

    # ----------------------------------------------------
    # Build Pipeline Context
    # ----------------------------------------------------

    context = PipelineContext(
        job_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        source_type="url",
        source_target=str(source_url),
    )

    # ----------------------------------------------------
    # Dispatch Runtime
    # ----------------------------------------------------

    try:
        result = celery.send_task(
            "runtime.tasks.ingestion.test_ingestion",
            args=[context.to_dict()],
            queue="downloader",
        )

        print("=" * 60)
        print("TASK ID:", result.id)
        print("TASK:", "runtime.tasks.ingestion.test_ingestion")
        print("QUEUE:", "downloader")
        print("=" * 60)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Celery dispatch failed: {e}",
        )

    return {
        "message": "Pipeline queued successfully.",
        "job_id": context.job_id,
        "tenant_id": context.tenant_id,
        "status": "queued",
    }