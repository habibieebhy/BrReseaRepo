"""Tenant-safe source discovery and synchronization tools."""

from __future__ import annotations

from fastmcp import FastMCP
from pydantic import BaseModel

from brixta_mcp.auth import READ_SCOPE, WRITE_SCOPE, current_access_context
from runtime.sources import SourceRepository
from runtime.sources.service import enqueue_source


class SourceSummary(BaseModel):
    id: str
    name: str
    start_url: str
    enabled: bool
    last_status: str
    last_job_id: str | None = None


class SourceListOutput(BaseModel):
    sources: list[SourceSummary]


class SyncOutput(BaseModel):
    source_id: str
    job_id: str
    task_id: str
    status: str


READ_SECURITY = {"securitySchemes": [{"type": "oauth2", "scopes": [READ_SCOPE]}]}
WRITE_SECURITY = {
    "securitySchemes": [
        {"type": "oauth2", "scopes": [READ_SCOPE, WRITE_SCOPE]},
    ]
}
READ_ONLY_ANNOTATIONS = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}
SYNC_ANNOTATIONS = {
    "readOnlyHint": False,
    "destructiveHint": False,
    "idempotentHint": False,
    "openWorldHint": True,
}


def register_source_tools(mcp: FastMCP) -> None:
    @mcp.tool(
        output_schema=SourceListOutput.model_json_schema(),
        annotations=READ_ONLY_ANNOTATIONS,
        meta=READ_SECURITY,
    )
    def brixta_list_sources() -> SourceListOutput:
        """List configured sources available to the authenticated tenant."""
        access = current_access_context()
        access.require(READ_SCOPE)
        return SourceListOutput(
            sources=[
                SourceSummary(**source)
                for source in SourceRepository.list(access.tenant_id)
            ]
        )

    @mcp.tool(
        output_schema=SyncOutput.model_json_schema(),
        annotations=SYNC_ANNOTATIONS,
        meta=WRITE_SECURITY,
    )
    def brixta_sync_source(source_id: str) -> SyncOutput:
        """Queue an authorized source for ingestion and indexing."""
        access = current_access_context()
        access.require(WRITE_SCOPE)
        source = SourceRepository.get(source_id)
        if source is None or source.get("tenant_id") != access.tenant_id:
            raise ValueError("Source not found.")
        if not source.get("enabled", False):
            raise ValueError("Source is disabled.")
        return SyncOutput(**enqueue_source(source))
