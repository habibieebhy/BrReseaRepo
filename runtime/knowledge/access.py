"""Persistent tenant knowledge allowlists shared by API and MCP replicas."""

from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock

from core.database import get_connection


class KnowledgeAccessRepository:
    """Default ready knowledge to enabled and persist explicit access choices."""

    _backend = os.getenv("BRIXTA_KNOWLEDGE_ACCESS_BACKEND", "postgres").lower()
    _path = Path("storage/control-plane/knowledge-access.json")
    _lock = Lock()
    _table_ready = False

    @classmethod
    def _ensure_table(cls) -> None:
        if cls._table_ready:
            return
        with cls._lock:
            if cls._table_ready:
                return
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS "BrResearch".knowledge_access (
                            tenant_id text NOT NULL,
                            knowledge_base_id uuid NOT NULL REFERENCES
                                "BrResearch".ingestion_jobs(id) ON DELETE CASCADE,
                            enabled boolean NOT NULL DEFAULT true,
                            updated_at timestamptz NOT NULL DEFAULT now(),
                            PRIMARY KEY (tenant_id, knowledge_base_id)
                        )
                        """
                    )
            cls._table_ready = True

    @classmethod
    def _read_file(cls) -> dict[str, dict[str, bool]]:
        if not cls._path.exists():
            return {}
        return json.loads(cls._path.read_text(encoding="utf-8"))

    @classmethod
    def _write_file(cls, value: dict[str, dict[str, bool]]) -> None:
        cls._path.parent.mkdir(parents=True, exist_ok=True)
        temporary = cls._path.with_suffix(".tmp")
        temporary.write_text(json.dumps(value, indent=2), encoding="utf-8")
        temporary.replace(cls._path)

    @classmethod
    def is_enabled(cls, tenant_id: str, knowledge_base_id: str) -> bool:
        if cls._backend == "file":
            return cls._read_file().get(tenant_id, {}).get(knowledge_base_id, True)
        cls._ensure_table()
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT enabled
                    FROM "BrResearch".knowledge_access
                    WHERE tenant_id = %s AND knowledge_base_id = %s
                    """,
                    (tenant_id, knowledge_base_id),
                )
                row = cursor.fetchone()
        return bool(row[0]) if row else True

    @classmethod
    def set_enabled(
        cls,
        tenant_id: str,
        knowledge_base_id: str,
        enabled: bool,
    ) -> bool:
        if cls._backend == "file":
            with cls._lock:
                value = cls._read_file()
                value.setdefault(tenant_id, {})[knowledge_base_id] = enabled
                cls._write_file(value)
            return enabled
        cls._ensure_table()
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO "BrResearch".knowledge_access (
                        tenant_id, knowledge_base_id, enabled, updated_at
                    )
                    SELECT tenant_id, id, %s, now()
                    FROM "BrResearch".ingestion_jobs
                    WHERE tenant_id = %s AND id = %s
                    ON CONFLICT (tenant_id, knowledge_base_id)
                    DO UPDATE SET enabled = EXCLUDED.enabled, updated_at = now()
                    """,
                    (enabled, tenant_id, knowledge_base_id),
                )
                if cursor.rowcount != 1:
                    raise ValueError("Knowledge base not found for this tenant.")
        return enabled

    @classmethod
    def filter_enabled(cls, tenant_id: str, items: list[dict]) -> list[dict]:
        if cls._backend == "file":
            disabled = {
                item_id
                for item_id, enabled in cls._read_file().get(tenant_id, {}).items()
                if not enabled
            }
        else:
            cls._ensure_table()
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT knowledge_base_id::text
                        FROM "BrResearch".knowledge_access
                        WHERE tenant_id = %s AND enabled = false
                        """,
                        (tenant_id,),
                    )
                    disabled = {row[0] for row in cursor.fetchall()}
        return [item for item in items if str(item["id"]) not in disabled]
