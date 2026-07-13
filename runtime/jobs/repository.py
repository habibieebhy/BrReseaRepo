from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from psycopg.types.json import Jsonb

from brixta_sdk.context import PipelineContext
from core.config import MAX_JOB_RUNS
from core.database import get_connection
from core.enums import JobStatus


class JobRepository:
    @staticmethod
    def list(limit: int = 100, tenant_id: str | None = None) -> list[dict[str, Any]]:
        query = """
            SELECT
                id, source_type, source_target, tenant_id, status, error_log,
                created_at, updated_at, started_at, completed_at,
                current_stage, celery_task_id, attempt_count, max_attempts,
                terminal, retryable, retry_count, parent_job_id,
                context_json IS NOT NULL
            FROM "BrResearch".ingestion_jobs
        """
        params: list[Any] = []
        if tenant_id:
            query += " WHERE tenant_id = %s"
            params.append(tenant_id)
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

        jobs = []
        for row in rows:
            retry_count = row[16]
            has_context = row[18]
            jobs.append(
                {
                    "id": str(row[0]),
                    "source_type": row[1],
                    "source_target": row[2],
                    "tenant_id": row[3],
                    "status": row[4],
                    "error": row[5],
                    "created_at": row[6].isoformat() if row[6] else None,
                    "updated_at": row[7].isoformat() if row[7] else None,
                    "started_at": row[8].isoformat() if row[8] else None,
                    "completed_at": row[9].isoformat() if row[9] else None,
                    "current_stage": row[10],
                    "celery_task_id": row[11],
                    "attempt_count": row[12],
                    "max_attempts": row[13],
                    "terminal": row[14],
                    "retryable": row[15],
                    "retry_count": retry_count,
                    "max_job_runs": MAX_JOB_RUNS,
                    "parent_job_id": str(row[17]) if row[17] else None,
                    "can_retry": bool(
                        row[4] == JobStatus.FAILED.value
                        and row[14]
                        and row[15]
                        and has_context
                        and retry_count < MAX_JOB_RUNS - 1
                    ),
                }
            )
        return jobs

    @staticmethod
    def get(job_id: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        id, status, error_log, terminal, retryable, retry_count,
                        context_json, parent_job_id, current_stage,
                        attempt_count, max_attempts
                    FROM "BrResearch".ingestion_jobs
                    WHERE id = %s
                    """,
                    (job_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return {
            "id": str(row[0]),
            "status": row[1],
            "error": row[2],
            "terminal": row[3],
            "retryable": row[4],
            "retry_count": row[5],
            "context": row[6],
            "parent_job_id": str(row[7]) if row[7] else None,
            "current_stage": row[8],
            "attempt_count": row[9],
            "max_attempts": row[10],
        }

    @staticmethod
    def create(
        context: PipelineContext,
        *,
        parent_job_id: str | None = None,
        retry_count: int = 0,
    ) -> None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO "BrResearch".ingestion_jobs
                    (
                        id, source_type, source_target, tenant_id, status,
                        context_json, parent_job_id, retry_count,
                        current_stage, terminal, retryable
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, false, true)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        context.job_id,
                        context.source_type,
                        context.source_target,
                        context.tenant_id,
                        JobStatus.QUEUED.value,
                        Jsonb(context.to_dict()),
                        parent_job_id,
                        retry_count,
                        "downloader",
                    ),
                )

    @staticmethod
    def mark_dispatched(job_id: str, task_id: str, stage: str) -> None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE "BrResearch".ingestion_jobs
                    SET status = %s,
                        current_stage = %s,
                        celery_task_id = %s,
                        attempt_count = 0,
                        updated_at = now()
                    WHERE id = %s AND terminal = false
                    """,
                    (JobStatus.QUEUED.value, stage, task_id, job_id),
                )

    @staticmethod
    def begin_stage(
        job_id: str,
        *,
        stage: str,
        status: JobStatus,
        task_id: str,
        attempt: int,
        max_attempts: int,
    ) -> bool:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE "BrResearch".ingestion_jobs
                    SET status = %s,
                        current_stage = %s,
                        celery_task_id = %s,
                        attempt_count = %s,
                        max_attempts = %s,
                        started_at = COALESCE(started_at, now()),
                        updated_at = now(),
                        error_log = NULL
                    WHERE id = %s
                      AND terminal = false
                      AND current_stage = %s
                      AND (
                        celery_task_id IS NULL
                        OR celery_task_id = %s
                        OR status = %s
                      )
                    """,
                    (
                        status.value,
                        stage,
                        task_id,
                        attempt,
                        max_attempts,
                        job_id,
                        stage,
                        task_id,
                        JobStatus.RETRYING.value,
                    ),
                )
                return cur.rowcount == 1

    @staticmethod
    def update_status(job_id: str, status: JobStatus) -> None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE "BrResearch".ingestion_jobs
                    SET status = %s, updated_at = now()
                    WHERE id = %s AND terminal = false
                    """,
                    (status.value, job_id),
                )

    @staticmethod
    def record_retry(
        job_id: str,
        *,
        error: str,
        attempt: int,
        max_attempts: int,
        delay_seconds: int,
    ) -> None:
        message = (
            f"Attempt {attempt}/{max_attempts} failed. "
            f"Retrying in {delay_seconds} seconds.\n{error}"
        )
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE "BrResearch".ingestion_jobs
                    SET status = %s,
                        error_log = %s,
                        attempt_count = %s,
                        max_attempts = %s,
                        retryable = true,
                        updated_at = now()
                    WHERE id = %s AND terminal = false
                    """,
                    (
                        JobStatus.RETRYING.value,
                        message[:4000],
                        attempt,
                        max_attempts,
                        job_id,
                    ),
                )

    @staticmethod
    def record_failure(
        job_id: str,
        error: str,
        *,
        retryable: bool = False,
        attempts: int | None = None,
        terminal: bool = True,
    ) -> None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE "BrResearch".ingestion_jobs
                    SET status = %s,
                        error_log = %s,
                        retryable = %s,
                        terminal = %s,
                        attempt_count = COALESCE(%s, attempt_count),
                        updated_at = now(),
                        completed_at = CASE WHEN %s THEN now() ELSE completed_at END
                    WHERE id = %s
                    """,
                    (
                        JobStatus.FAILED.value,
                        error[:4000],
                        retryable,
                        terminal,
                        attempts,
                        terminal,
                        job_id,
                    ),
                )

    @staticmethod
    def mark_completed(job_id: str) -> None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE "BrResearch".ingestion_jobs
                    SET status = %s,
                        terminal = true,
                        retryable = false,
                        updated_at = now(),
                        completed_at = now(),
                        error_log = NULL
                    WHERE id = %s AND terminal = false
                    """,
                    (JobStatus.COMPLETED.value, job_id),
                )

    @staticmethod
    def is_terminal(job_id: str) -> bool:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT terminal FROM "BrResearch".ingestion_jobs WHERE id = %s',
                    (job_id,),
                )
                row = cur.fetchone()
        return bool(row and row[0])

    @staticmethod
    def stale_candidates(timeout_seconds: int) -> list[dict[str, Any]]:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=timeout_seconds)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, status, current_stage, celery_task_id, updated_at
                    FROM "BrResearch".ingestion_jobs
                    WHERE terminal = false
                      AND status NOT IN (%s, %s, %s)
                      AND updated_at < %s
                    """,
                    (
                        JobStatus.COMPLETED.value,
                        JobStatus.FAILED.value,
                        JobStatus.CANCELLED.value,
                        cutoff,
                    ),
                )
                rows = cur.fetchall()
        return [
            {
                "id": str(row[0]),
                "status": row[1],
                "current_stage": row[2],
                "celery_task_id": row[3],
                "updated_at": row[4],
            }
            for row in rows
        ]

    @staticmethod
    def mark_orphaned(job_id: str, timeout_seconds: int) -> None:
        JobRepository.record_failure(
            job_id,
            (
                "Orphaned job: no active, reserved, or scheduled Celery task "
                f"was found and the job made no progress for {timeout_seconds} seconds. "
                "The job was stopped automatically and may be retried as a new run."
            ),
            retryable=True,
            terminal=True,
        )

    @staticmethod
    def mark_failed(job_id: str) -> None:
        JobRepository.record_failure(job_id, "Job marked failed.")
