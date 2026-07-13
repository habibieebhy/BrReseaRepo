"""Small self-hosted control-plane repository for source definitions.

The file backend keeps the MVP runnable without provisioning another service.
The interface is intentionally narrow so a PostgreSQL implementation can
replace it for multi-replica cloud deployments.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4


class SourceRepository:
    _path = Path("storage/control-plane/sources.json")
    _lock = Lock()

    @classmethod
    def _read(cls) -> list[dict[str, Any]]:
        if not cls._path.exists():
            return []
        return json.loads(cls._path.read_text(encoding="utf-8"))

    @classmethod
    def _write(cls, sources: list[dict[str, Any]]) -> None:
        cls._path.parent.mkdir(parents=True, exist_ok=True)
        temporary = cls._path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(sources, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        temporary.replace(cls._path)

    @classmethod
    def list(cls, tenant_id: str | None = None) -> list[dict[str, Any]]:
        sources = cls._read()
        if tenant_id:
            sources = [item for item in sources if item["tenant_id"] == tenant_id]
        return sorted(sources, key=lambda item: item["created_at"], reverse=True)

    @classmethod
    def get(cls, source_id: str) -> dict[str, Any] | None:
        return next((item for item in cls._read() if item["id"] == source_id), None)

    @classmethod
    def create(cls, payload: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        source = {
            **payload,
            "id": str(uuid4()),
            "created_at": now,
            "updated_at": now,
            "last_run_at": None,
            "last_job_id": None,
            "last_status": "never_run",
        }
        with cls._lock:
            sources = cls._read()
            sources.append(source)
            cls._write(sources)
        return source

    @classmethod
    def update(cls, source_id: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        with cls._lock:
            sources = cls._read()
            for index, source in enumerate(sources):
                if source["id"] == source_id:
                    updated = {
                        **source,
                        **changes,
                        "id": source_id,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                    sources[index] = updated
                    cls._write(sources)
                    return updated
        return None

    @classmethod
    def delete(cls, source_id: str) -> bool:
        with cls._lock:
            sources = cls._read()
            remaining = [item for item in sources if item["id"] != source_id]
            if len(remaining) == len(sources):
                return False
            cls._write(remaining)
            return True

    @classmethod
    def update_by_job(cls, job_id: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        source = next(
            (item for item in cls._read() if item.get("last_job_id") == job_id),
            None,
        )
        if source is None:
            return None
        return cls.update(source["id"], changes)
