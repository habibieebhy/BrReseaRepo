from __future__ import annotations

from core.config import ORPHAN_TIMEOUT_SECONDS
from runtime.celery_app import celery
from runtime.jobs.repository import JobRepository
from runtime.sources.repository import SourceRepository
from runtime.utils.logging import logger


def _live_task_ids() -> set[str]:
    inspector = celery.control.inspect(timeout=2.0)
    live: set[str] = set()
    for payload in (
        inspector.active() or {},
        inspector.reserved() or {},
        inspector.scheduled() or {},
    ):
        for tasks in payload.values():
            for item in tasks:
                request = item.get("request", item)
                task_id = request.get("id")
                if task_id:
                    live.add(task_id)
    return live


@celery.task(name="runtime.tasks.reconcile.reconcile_orphaned_jobs")
def reconcile_orphaned_jobs() -> dict:
    live_ids = _live_task_ids()
    orphaned: list[str] = []

    for candidate in JobRepository.stale_candidates(ORPHAN_TIMEOUT_SECONDS):
        task_id = candidate.get("celery_task_id")
        if task_id and task_id in live_ids:
            continue
        JobRepository.mark_orphaned(candidate["id"], ORPHAN_TIMEOUT_SECONDS)
        try:
            SourceRepository.update_by_job(
                candidate["id"],
                {"last_status": "failed"},
            )
        except Exception:
            logger.exception(
                "Could not update source for orphaned job | job=%s",
                candidate["id"],
            )
        orphaned.append(candidate["id"])
        logger.error(
            "Orphaned job marked failed | job=%s stage=%s task=%s",
            candidate["id"],
            candidate.get("current_stage"),
            task_id,
        )

    return {"checked_live_tasks": len(live_ids), "orphaned": orphaned}
