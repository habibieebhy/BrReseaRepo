from __future__ import annotations

import traceback
from collections.abc import Callable
from typing import Any, TypeVar

from celery.exceptions import Ignore

from brixta_sdk.context import PipelineContext
from core.config import MAX_TASK_ATTEMPTS, TASK_RETRY_BACKOFF_SECONDS
from core.enums import JobStatus
from core.retry_policy import is_retryable_exception
from runtime.jobs.repository import JobRepository
from runtime.utils.logging import logger


T = TypeVar("T")


def error_details(exc: Exception) -> str:
    trace = traceback.format_exc()
    return f"{exc.__class__.__name__}: {exc}\n{trace}"[:4000]


def execute_stage(
    task: Any,
    context: PipelineContext,
    stage: str,
    status: JobStatus,
    operation: Callable[[], T],
) -> T:
    """Execute one stage with bounded retries and durable attempt state."""

    attempt = int(task.request.retries) + 1
    try:
        if JobRepository.is_terminal(context.job_id):
            logger.warning(
                "Ignoring delivery for terminal job | job=%s stage=%s",
                context.job_id,
                stage,
            )
            raise Ignore()
        claimed = JobRepository.begin_stage(
            context.job_id,
            stage=stage,
            status=status,
            task_id=task.request.id,
            attempt=attempt,
            max_attempts=MAX_TASK_ATTEMPTS,
        )
    except Ignore:
        raise
    except Exception as exc:
        if attempt < MAX_TASK_ATTEMPTS:
            delay = TASK_RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1))
            logger.exception(
                "Could not claim stage; retrying | job=%s stage=%s attempt=%s/%s",
                context.job_id,
                stage,
                attempt,
                MAX_TASK_ATTEMPTS,
            )
            raise task.retry(
                exc=exc,
                countdown=delay,
                max_retries=MAX_TASK_ATTEMPTS - 1,
            )
        raise
    if not claimed:
        logger.warning(
            "Ignoring stale or duplicate delivery | job=%s stage=%s task=%s",
            context.job_id,
            stage,
            task.request.id,
        )
        raise Ignore()

    try:
        return operation()
    except Ignore:
        raise
    except Exception as exc:
        retryable = is_retryable_exception(exc)
        details = error_details(exc)

        if retryable and attempt < MAX_TASK_ATTEMPTS:
            delay = TASK_RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1))
            try:
                JobRepository.record_retry(
                    context.job_id,
                    error=details,
                    attempt=attempt,
                    max_attempts=MAX_TASK_ATTEMPTS,
                    delay_seconds=delay,
                )
            except Exception:
                logger.exception(
                    "Could not persist retry state | job=%s stage=%s",
                    context.job_id,
                    stage,
                )
            logger.warning(
                "Stage failed; retry scheduled | job=%s stage=%s attempt=%s/%s delay=%ss error=%s",
                context.job_id,
                stage,
                attempt,
                MAX_TASK_ATTEMPTS,
                delay,
                exc,
            )
            raise task.retry(
                exc=exc,
                countdown=delay,
                max_retries=MAX_TASK_ATTEMPTS - 1,
            )

        reason = (
            f"Permanent failure; retrying the same input will not help. {details}"
            if not retryable
            else f"Retry budget exhausted after {attempt} attempts. {details}"
        )
        try:
            JobRepository.record_failure(
                context.job_id,
                reason,
                retryable=retryable,
                attempts=attempt,
                terminal=True,
            )
        except Exception:
            logger.exception(
                "Could not persist terminal failure | job=%s stage=%s",
                context.job_id,
                stage,
            )
        logger.error(
            "Stage failed terminally | job=%s stage=%s attempt=%s/%s retryable=%s error=%s",
            context.job_id,
            stage,
            attempt,
            MAX_TASK_ATTEMPTS,
            retryable,
            exc,
        )
        raise
