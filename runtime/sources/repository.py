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

from core.config import BRIXTA_CONTROL_PLANE_BACKEND


def _get_connection():
    """Import the PostgreSQL driver only when the PostgreSQL backend is used."""

    from core.database import get_connection

    return get_connection()


def _jsonb(value: dict[str, Any]):
    """Keep the lightweight file backend importable without psycopg installed."""

    from psycopg.types.json import Jsonb

    return Jsonb(value)


class _FileSourceRepository:
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


class _PostgresSourceRepository:
    @staticmethod
    def _row(row: tuple[Any, ...]) -> dict[str, Any]:
        return {
            **(row[2] or {}),
            "id": str(row[0]),
            "tenant_id": row[1],
            "created_at": row[3].isoformat(),
            "updated_at": row[4].isoformat(),
        }

    @classmethod
    def list(cls, tenant_id: str | None = None) -> list[dict[str, Any]]:
        query = """
            SELECT id, tenant_id, payload, created_at, updated_at
            FROM "BrResearch".sources
        """
        params: list[Any] = []
        if tenant_id:
            query += " WHERE tenant_id = %s"
            params.append(tenant_id)
        query += " ORDER BY created_at DESC"
        with _get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
        return [cls._row(row) for row in rows]

    @classmethod
    def get(cls, source_id: str) -> dict[str, Any] | None:
        with _get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, tenant_id, payload, created_at, updated_at
                    FROM "BrResearch".sources
                    WHERE id = %s
                    """,
                    (source_id,),
                )
                row = cursor.fetchone()
        return cls._row(row) if row else None

    @classmethod
    def create(cls, payload: dict[str, Any]) -> dict[str, Any]:
        source_id = str(uuid4())
        mutable = {
            **payload,
            "last_run_at": None,
            "last_job_id": None,
            "last_status": "never_run",
        }
        tenant_id = str(mutable.pop("tenant_id"))
        with _get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO "BrResearch".sources (id, tenant_id, payload)
                    VALUES (%s, %s, %s)
                    """,
                    (source_id, tenant_id, _jsonb(mutable)),
                )
        created = cls.get(source_id)
        if created is None:
            raise RuntimeError("Source was not persisted.")
        return created

    @classmethod
    def update(cls, source_id: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        safe_changes = {key: value for key, value in changes.items() if key not in {"id", "tenant_id"}}
        with _get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE "BrResearch".sources
                    SET payload = payload || %s, updated_at = now()
                    WHERE id = %s
                    """,
                    (_jsonb(safe_changes), source_id),
                )
                found = cursor.rowcount == 1
        return cls.get(source_id) if found else None

    @staticmethod
    def delete(source_id: str) -> bool:
        with _get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    'DELETE FROM "BrResearch".sources WHERE id = %s',
                    (source_id,),
                )
                return cursor.rowcount == 1

    @classmethod
    def update_by_job(cls, job_id: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        with _get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id
                    FROM "BrResearch".sources
                    WHERE payload->>'last_job_id' = %s
                    LIMIT 1
                    """,
                    (job_id,),
                )
                row = cursor.fetchone()
        return cls.update(str(row[0]), changes) if row else None


if BRIXTA_CONTROL_PLANE_BACKEND == "postgres":
    SourceRepository = _PostgresSourceRepository
elif BRIXTA_CONTROL_PLANE_BACKEND == "file":
    SourceRepository = _FileSourceRepository
else:
    raise RuntimeError("BRIXTA_CONTROL_PLANE_BACKEND must be 'file' or 'postgres'.")
