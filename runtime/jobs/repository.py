from brixta_sdk.context import PipelineContext
from core.database import get_connection
from core.enums import JobStatus


class JobRepository:

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