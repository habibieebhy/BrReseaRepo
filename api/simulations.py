"""Structural & Material Lab HTTP API."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Response, status

from api.auth import CurrentPrincipal
from brixta_sdk.simulations import SimulationPreflightRequest, SimulationRunRequest
from runtime.artifacts.repository import ArtifactRepository
from runtime.celery_app import celery
from runtime.simulations.case_cards import case_cards
from runtime.simulations.registry import simulation_registry
from runtime.simulations.repository import SimulationRunRepository
from runtime.simulations.service import SimulationError, build_preflight, create_simulation_run


router = APIRouter()


@router.get("/case-cards")
def list_case_cards(principal: CurrentPrincipal):
    return {"case_cards": case_cards(), "plugins": simulation_registry.list()}


@router.post("/preflight")
def simulation_preflight(payload: SimulationPreflightRequest, principal: CurrentPrincipal):
    try:
        scoped = payload.model_copy(
            update={"tenant_id": principal.tenant_for(payload.tenant_id)}
        )
        return build_preflight(scoped)
    except (SimulationError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/runs", status_code=status.HTTP_202_ACCEPTED)
def create_run(payload: SimulationRunRequest, principal: CurrentPrincipal):
    try:
        scoped = payload.model_copy(
            update={"tenant_id": principal.tenant_for(payload.tenant_id)}
        )
        run = create_simulation_run(scoped)
    except (SimulationError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    try:
        task = celery.send_task(
            "runtime.tasks.simulations.execute_simulation_run",
            args=[run["id"]],
            queue=f"simulations.{run['solver']}",
        )
        SimulationRunRepository.mark_dispatched(run["id"], task.id)
    except Exception as exc:
        SimulationRunRepository.fail(run["id"], f"Celery dispatch failed: {exc}")
        raise HTTPException(status_code=503, detail=f"Could not queue simulation: {exc}") from exc
    return {"run": SimulationRunRepository.get(run["id"]), "task_id": task.id}


@router.get("/runs")
def list_runs(principal: CurrentPrincipal, tenant_id: str | None = None, limit: int = 100):
    return {
        "runs": SimulationRunRepository.list(
            tenant_id=principal.tenant_for(tenant_id),
            limit=limit,
        )
    }


@router.get("/runs/{run_id}")
def get_run(run_id: str, principal: CurrentPrincipal, tenant_id: str | None = None):
    run = SimulationRunRepository.get(
        run_id,
        tenant_id=principal.tenant_for(tenant_id),
    )
    if run is None:
        raise HTTPException(status_code=404, detail="Simulation run not found.")
    return {"run": run}


@router.post("/runs/{run_id}/cancel")
def cancel_run(run_id: str, principal: CurrentPrincipal, tenant_id: str | None = None):
    scoped_tenant = principal.tenant_for(tenant_id)
    run = SimulationRunRepository.get(run_id, tenant_id=scoped_tenant)
    if run is None:
        raise HTTPException(status_code=404, detail="Simulation run not found.")
    if run["terminal"]:
        raise HTTPException(status_code=409, detail="Simulation run is already terminal.")
    if run.get("celery_task_id"):
        celery.control.revoke(run["celery_task_id"], terminate=True, signal="SIGTERM")
    cancelled = SimulationRunRepository.cancel(run_id, tenant_id=scoped_tenant)
    return {"run": cancelled}


@router.get("/runs/{run_id}/artifacts/{filename:path}")
def get_artifact(
    run_id: str,
    filename: str,
    principal: CurrentPrincipal,
    tenant_id: str | None = None,
):
    run = SimulationRunRepository.get(
        run_id,
        tenant_id=principal.tenant_for(tenant_id),
    )
    if run is None:
        raise HTTPException(status_code=404, detail="Simulation run not found.")
    match = next((item for item in run["artifacts"] if item["name"] == filename), None)
    if match is None or not ArtifactRepository.object_exists(match["object_name"]):
        raise HTTPException(status_code=404, detail="Simulation artifact not found.")
    return Response(
        content=ArtifactRepository.load_object(match["object_name"]),
        media_type=match.get("content_type") or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{Path(filename).name}"'},
    )
