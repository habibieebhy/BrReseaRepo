from brixta_sdk.context import PipelineContext
from core.database import get_connection
from core.enums import JobStatus


class JobRepository:

    @staticmethod
    def list(limit: int = 100, tenant_id: str | None = None):
        query = 'SELECT id, source_type, source_target, tenant_id, status, error_log FROM "BrResearch".ingestion_jobs'
        params = []
        if tenant_id:
            query += " WHERE tenant_id = %s"
            params.append(tenant_id)
        query += " ORDER BY id DESC LIMIT %s"
        params.append(limit)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return [{"id": str(row[0]), "source_type": row[1], "source_target": row[2], "tenant_id": row[3], "status": row[4], "error": row[5]} for row in cur.fetchall()]

    @staticmethod
    def create(context: PipelineContext):

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
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        context.job_id,
                        context.source_type,
                        context.source_target,
                        context.tenant_id,
                        JobStatus.QUEUED.value,
                    ),
                )

    @staticmethod
    def update_status(
        job_id: str,
        status: JobStatus,
    ):

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE "BrResearch".ingestion_jobs
                    SET status = %s
                    WHERE id = %s
                    """,
                    (
                        status.value,
                        job_id,
                    ),
                )

    @staticmethod
    def mark_failed(job_id: str):

        JobRepository.update_status(
            job_id,
            JobStatus.FAILED,
        )

    @staticmethod
    def record_failure(job_id: str, error: str):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('UPDATE "BrResearch".ingestion_jobs SET status = %s, error_log = %s WHERE id = %s', (JobStatus.FAILED.value, error[:4000], job_id))
