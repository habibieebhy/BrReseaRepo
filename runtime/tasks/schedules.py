from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from celery.schedules import crontab

from runtime.celery_app import celery
from runtime.sources.repository import SourceRepository
from runtime.sources.service import enqueue_source
from runtime.utils.logging import logger


def _schedule_due(source: dict) -> bool:
    expression = source.get("cron_expression", "").split()
    if len(expression) != 5:
        logger.warning("Invalid cron expression | source=%s", source["id"])
        return False
    try:
        zone = ZoneInfo(source.get("timezone", "UTC"))
    except ZoneInfoNotFoundError:
        logger.warning("Invalid timezone | source=%s", source["id"])
        return False
    minute, hour, day_of_month, month_of_year, day_of_week = expression
    schedule = crontab(
        minute=minute,
        hour=hour,
        day_of_week=day_of_week,
        day_of_month=day_of_month,
        month_of_year=month_of_year,
        nowfun=lambda: datetime.now(zone),
    )
    previous = source.get("last_run_at") or source["created_at"]
    last_run = (
        previous
        if isinstance(previous, datetime)
        else datetime.fromisoformat(previous)
    )
    due, _next_check = schedule.is_due(last_run)
    return bool(due)


@celery.task(name="runtime.tasks.schedules.dispatch_due_sources")
def dispatch_due_sources() -> dict:
    dispatched = []
    for source in SourceRepository.list():
        if not source.get("enabled") or not source.get("schedule_enabled"):
            continue
        if _schedule_due(source):
            try:
                dispatched.append(enqueue_source(source))
            except Exception:
                logger.exception("Scheduled source dispatch failed | source=%s", source["id"])
                SourceRepository.update(source["id"], {"last_status": "dispatch_failed"})
    return {"dispatched": len(dispatched), "jobs": dispatched}
