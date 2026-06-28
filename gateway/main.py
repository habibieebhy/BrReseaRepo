import uuid

from fastapi import FastAPI, HTTPException, status
from pydantic import HttpUrl

from shared.database import get_connection

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

    try:
        conn = get_connection()

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

    return {
        "message": "Ingestion task queued successfully.",
        "job_id": job_id,
        "tenant_id": tenant_id,
        "status": "queued",
    }