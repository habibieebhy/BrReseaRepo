from __future__ import annotations

from uuid import uuid4

from brixta_sdk.context import PipelineContext
from core.config import MAX_JOB_RUNS
from runtime.celery_app import celery
from runtime.jobs.repository import JobRepository
from runtime.sources.repository import SourceRepository


class JobRetryError(RuntimeError):
    pass


def retry_failed_job(job_id: str) -> dict:
    previous = JobRepository.get(job_id)
    if previous is None:
        raise JobRetryError("Job not found.")
    if previous["status"] != "failed" or not previous["terminal"]:
        raise JobRetryError("Only terminal failed jobs can be retried.")
    if not previous["retryable"]:
        raise JobRetryError(
            "This is a permanent failure. Correct the input, schema, plugin, or "
            "configuration and submit a new job instead of repeating it unchanged."
        )
    if previous["context"] is None:
        raise JobRetryError(
            "This legacy job has no saved PipelineContext and cannot be replayed safely."
        )
    if previous["retry_count"] >= MAX_JOB_RUNS - 1:
        raise JobRetryError(
            f"Retry chain exhausted. BRIXTA permits at most {MAX_JOB_RUNS} total runs."
        )

    context = PipelineContext.from_dict(previous["context"])
    new_job_id = str(uuid4())
    context.job_id = new_job_id
    context.raw_path = None
    context.parsed_path = None
    context.chunks_path = None
    context.embeddings_path = None
    context.metadata = {
        **context.metadata,
        "retried_from_job_id": job_id,
        "retry_run": previous["retry_count"] + 2,
    }

    retry_count = previous["retry_count"] + 1
    JobRepository.create(
        context,
        parent_job_id=job_id,
        retry_count=retry_count,
    )
    try:
        result = celery.send_task(
            "runtime.tasks.ingestion.test_ingestion",
            args=[context.to_dict()],
            queue="downloader",
        )
        JobRepository.mark_dispatched(new_job_id, result.id, "downloader")
        source_id = context.metadata.get("source_id")
        if source_id:
            SourceRepository.update(
                source_id,
                {
                    "last_job_id": new_job_id,
                    "last_status": "queued",
                },
            )
    except Exception as exc:
        JobRepository.record_failure(
            new_job_id,
            f"Retry dispatch failed: {exc}",
            retryable=True,
        )
        raise JobRetryError(f"Retry dispatch failed: {exc}") from exc

    return {
        "message": "Failed job queued as a new run.",
        "previous_job_id": job_id,
        "job_id": new_job_id,
        "task_id": result.id,
        "run": retry_count + 1,
        "max_runs": MAX_JOB_RUNS,
        "status": "queued",
    }
