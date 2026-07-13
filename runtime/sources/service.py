from __future__ import annotations

import uuid
from datetime import datetime, timezone

from brixta_sdk.context import PipelineContext
from core.plugin_loader import registry
from runtime.celery_app import celery
from runtime.sources.repository import SourceRepository
from runtime.settings import RuntimeSettingsRepository


def enqueue_source(source: dict) -> dict:
    context = PipelineContext(
        job_id=str(uuid.uuid4()),
        tenant_id=source["tenant_id"],
        source_type="url",
        source_target=source["start_url"],
        plugins=registry.validate_selection(source.get("plugins", {})),
        config={"pipeline_order": RuntimeSettingsRepository.get().get("pipeline_order", ["downloader", "parser", "chunker", "embedding", "storage"]), **source.get("config", {})},
        metadata={"source_id": source["id"], "crawl_strategy": source["crawl_strategy"]},
    )
    result = celery.send_task(
        "runtime.tasks.ingestion.test_ingestion",
        args=[context.to_dict()],
        queue="downloader",
    )
    SourceRepository.update(
        source["id"],
        {
            "last_run_at": datetime.now(timezone.utc).isoformat(),
            "last_job_id": context.job_id,
            "last_status": "queued",
        },
    )
    return {"source_id": source["id"], "job_id": context.job_id, "task_id": result.id, "status": "queued"}
