"""Tenant-safe Structural & Material Lab result tools."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from pydantic import BaseModel

from brixta_mcp.auth import READ_SCOPE, current_access_context
from runtime.simulations.repository import SimulationRunRepository


READ_SECURITY = {"securitySchemes": [{"type": "oauth2", "scopes": [READ_SCOPE]}]}
READ_ONLY_ANNOTATIONS = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}


class SimulationRunSummary(BaseModel):
    id: str
    label: str | None = None
    case_card_id: str
    solver: str
    execution_mode: str
    status: str
    created_at: str | None = None
    completed_at: str | None = None


class SimulationRunListOutput(BaseModel):
    runs: list[SimulationRunSummary]


class SimulationReportOutput(BaseModel):
    id: str
    case_card_id: str
    status: str
    summary: dict[str, Any] | None = None
    evidence: list[dict[str, Any]]
    artifacts: list[dict[str, Any]]
    error: str | None = None


def register_simulation_tools(mcp: FastMCP) -> None:
    @mcp.tool(
        output_schema=SimulationRunListOutput.model_json_schema(),
        annotations=READ_ONLY_ANNOTATIONS,
        meta=READ_SECURITY,
    )
    def brixta_list_simulation_runs(limit: int = 50) -> SimulationRunListOutput:
        """List structural/material simulation runs for the authenticated tenant."""
        access = current_access_context()
        access.require(READ_SCOPE)
        runs = SimulationRunRepository.list(
            tenant_id=access.tenant_id,
            limit=min(max(limit, 1), 200),
        )
        return SimulationRunListOutput(
            runs=[SimulationRunSummary(**run) for run in runs]
        )

    @mcp.tool(
        output_schema=SimulationReportOutput.model_json_schema(),
        annotations=READ_ONLY_ANNOTATIONS,
        meta=READ_SECURITY,
    )
    def brixta_get_simulation_report(run_id: str) -> SimulationReportOutput:
        """Fetch one completed or failed simulation record with evidence and artifacts."""
        access = current_access_context()
        access.require(READ_SCOPE)
        run = SimulationRunRepository.get(run_id, tenant_id=access.tenant_id)
        if run is None:
            raise ValueError("Simulation run not found.")
        return SimulationReportOutput(**run)
