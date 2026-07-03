import uuid

from fastapi import FastAPI, HTTPException, status
from pydantic import HttpUrl

from shared.database import get_connection
from workers.celery_app import celery


app = FastAPI(
    title="BRIXTA Research Pipeline Gateway",
    description="High-performance ingestion entry point.",
    version="2.0.0",
)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health():
    return {
        "status": "healthy",
        "database": "Neon PostgreSQL",
        "service": "brixta-gateway",
    }

@app.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest(source_url: HttpUrl, tenant_id: str):

    job_id = str(uuid.uuid4())

    # -------------------------
    # Store ingestion job
    # -------------------------

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO "BrResearch".ingestion_jobs
                    (
                        id,
                        source_type,
                        source_target,
                        tenant_id,
                        status
                    )
                    VALUES
                    (%s, %s, %s, %s, %s)
                    """,
                    (
                        job_id,
                        "url",
                        str(source_url),
                        tenant_id,
                        "queued",
                    ),
                )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {e}",
        )

    # -------------------------
    # Dispatch downloader worker
    # -------------------------

    try:
        result = celery.send_task(
            "workers.tasks.ingestion.test_ingestion",
            args=[job_id],
            queue="downloader",
        )

        print("=" * 60)
        print("TASK ID:", result.id)
        print("TASK NAME:", "workers.tasks.ingestion.test_ingestion")
        print("QUEUE:", "downloader")
        print("BROKER:", celery.connection().as_uri())
        print("DEFAULT QUEUE:", celery.conf.task_default_queue)
        print("ROUTES:", celery.conf.task_routes)
        print("=" * 60)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Celery dispatch failed: {e}",
        )

    return {
        "message": "Ingestion task queued successfully.",
        "job_id": job_id,
        "tenant_id": tenant_id,
        "status": "queued",
    }