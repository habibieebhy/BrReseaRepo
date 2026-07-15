"""PostgreSQL persistence for simulation runs."""

from __future__ import annotations

import uuid
from typing import Any

from psycopg import sql
from psycopg.types.json import Jsonb

from brixta_sdk.simulation import SimulationStatus
from core.database import get_connection


class SimulationRunRepository:
    @staticmethod
    def create(
        *,
        tenant_id: str,
        case_card_id: str,
        solver: str,
        execution_mode: str,
        spec: dict[str, Any],
        evidence: list[dict[str, Any]],
        label: str | None,
    ) -> dict[str, Any]:
        run_id = str(uuid.uuid4())
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO "BrResearch".simulation_runs
                    (
                        id, tenant_id, label, case_card_id, solver,
                        execution_mode, status, current_stage,
                        spec_json, evidence_json, artifact_prefix
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'compiler', %s, %s, %s)
                    """,
                    (
                        run_id,
                        tenant_id,
                        label,
                        case_card_id,
                        solver,
                        execution_mode,
                        SimulationStatus.QUEUED.value,
                        Jsonb(spec),
                        Jsonb(evidence),
                        f"simulations/{run_id}",
                    ),
                )
        created = SimulationRunRepository.get(run_id, tenant_id=tenant_id)
        if created is None:
            raise RuntimeError("Simulation run was not persisted.")
        return created

    @staticmethod
    def _row(row: tuple[Any, ...]) -> dict[str, Any]:
        return {
            "id": str(row[0]),
            "tenant_id": row[1],
            "label": row[2],
            "case_card_id": row[3],
            "solver": row[4],
            "execution_mode": row[5],
            "status": row[6],
            "current_stage": row[7],
            "spec": row[8] or {},
            "evidence": row[9] or [],
            "summary": row[10],
            "artifacts": row[11] or [],
            "error": row[12],
            "celery_task_id": row[13],
            "created_at": row[14].isoformat() if row[14] else None,
            "updated_at": row[15].isoformat() if row[15] else None,
            "started_at": row[16].isoformat() if row[16] else None,
            "completed_at": row[17].isoformat() if row[17] else None,
            "artifact_prefix": row[18],
            "terminal": row[6]
            in {
                SimulationStatus.COMPLETED.value,
                SimulationStatus.FAILED.value,
                SimulationStatus.CANCELLED.value,
            },
        }

    @staticmethod
    def get(run_id: str, *, tenant_id: str | None = None) -> dict[str, Any] | None:
        query = sql.SQL("""
            SELECT
                id, tenant_id, label, case_card_id, solver, execution_mode,
                status, current_stage, spec_json, evidence_json, summary_json,
                artifacts_json, error_log, celery_task_id, created_at, updated_at,
                started_at, completed_at, artifact_prefix
            FROM "BrResearch".simulation_runs
            WHERE id = %s
        """)
        params: list[Any] = [run_id]
        if tenant_id:
            query += sql.SQL(" AND tenant_id = %s")
            params.append(tenant_id)
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                row = cursor.fetchone()
        return SimulationRunRepository._row(row) if row else None

    @staticmethod
    def list(*, tenant_id: str, limit: int = 100) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id, tenant_id, label, case_card_id, solver, execution_mode,
                        status, current_stage, spec_json, evidence_json, summary_json,
                        artifacts_json, error_log, celery_task_id, created_at, updated_at,
                        started_at, completed_at, artifact_prefix
                    FROM "BrResearch".simulation_runs
                    WHERE tenant_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (tenant_id, min(max(limit, 1), 500)),
                )
                rows = cursor.fetchall()
        return [SimulationRunRepository._row(row) for row in rows]

    @staticmethod
    def mark_dispatched(run_id: str, task_id: str) -> None:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE "BrResearch".simulation_runs
                    SET celery_task_id = %s, updated_at = now()
                    WHERE id = %s AND status = 'queued'
                    """,
                    (task_id, run_id),
                )

    @staticmethod
    def begin_stage(run_id: str, status: SimulationStatus, stage: str) -> None:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE "BrResearch".simulation_runs
                    SET status = %s, current_stage = %s,
                        started_at = COALESCE(started_at, now()), updated_at = now()
                    WHERE id = %s AND status NOT IN ('completed', 'failed', 'cancelled')
                    """,
                    (status.value, stage, run_id),
                )
                if cursor.rowcount != 1:
                    raise RuntimeError("Simulation run is no longer executable.")

    @staticmethod
    def complete(
        run_id: str,
        *,
        summary: dict[str, Any],
        artifacts: list[dict[str, Any]],
    ) -> None:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE "BrResearch".simulation_runs
                    SET status = 'completed', current_stage = 'completed',
                        summary_json = %s, artifacts_json = %s,
                        completed_at = now(), updated_at = now(), error_log = NULL
                    WHERE id = %s AND status != 'cancelled'
                    """,
                    (Jsonb(summary), Jsonb(artifacts), run_id),
                )

    @staticmethod
    def fail(run_id: str, error: str) -> None:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE "BrResearch".simulation_runs
                    SET status = 'failed', current_stage = 'failed',
                        error_log = %s, completed_at = now(), updated_at = now()
                    WHERE id = %s AND status != 'cancelled'
                    """,
                    (error[-20_000:], run_id),
                )

    @staticmethod
    def cancel(run_id: str, *, tenant_id: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE "BrResearch".simulation_runs
                    SET status = 'cancelled', current_stage = 'cancelled',
                        completed_at = now(), updated_at = now()
                    WHERE id = %s AND tenant_id = %s
                      AND status NOT IN ('completed', 'failed', 'cancelled')
                    """,
                    (run_id, tenant_id),
                )
        return SimulationRunRepository.get(run_id, tenant_id=tenant_id)
