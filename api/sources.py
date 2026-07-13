from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl

from core.exceptions import ValidationError
from core.plugin_loader import registry
from runtime.sources import SourceRepository
from runtime.sources.service import enqueue_source
from runtime.settings import RuntimeSettingsRepository


router = APIRouter(prefix="/sources", tags=["Sources"])


class SourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    tenant_id: str = Field(min_length=1, max_length=120)
    start_url: HttpUrl
    crawl_strategy: Literal["single_page", "sitemap", "recursive"] = "single_page"
    max_depth: int = Field(default=1, ge=0, le=10)
    max_pages: int = Field(default=100, ge=1, le=10000)
    include_patterns: list[str] = Field(default_factory=list)
    exclude_patterns: list[str] = Field(default_factory=list)
    schedule_enabled: bool = False
    cron_expression: str = "0 */6 * * *"
    timezone: str = "UTC"
    plugins: dict[str, str] = Field(default_factory=dict)
    config: dict = Field(default_factory=dict)
    enabled: bool = True


class SourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    schedule_enabled: bool | None = None
    cron_expression: str | None = None
    timezone: str | None = None
    enabled: bool | None = None


@router.get("")
def list_sources(tenant_id: str | None = None):
    return {"sources": SourceRepository.list(tenant_id)}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_source(request: SourceCreate):
    try:
        configured = RuntimeSettingsRepository.get().get("default_plugins", {})
        plugins = registry.validate_selection({**configured, **request.plugins})
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    payload = request.model_dump(mode="json")
    payload["plugins"] = plugins
    return SourceRepository.create(payload)


@router.patch("/{source_id}")
def update_source(source_id: str, request: SourceUpdate):
    source = SourceRepository.update(source_id, request.model_dump(exclude_none=True))
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found.")
    return source


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(source_id: str):
    if not SourceRepository.delete(source_id):
        raise HTTPException(status_code=404, detail="Source not found.")


@router.post("/{source_id}/sync", status_code=status.HTTP_202_ACCEPTED)
def sync_source(source_id: str):
    source = SourceRepository.get(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found.")
    if not source["enabled"]:
        raise HTTPException(status_code=409, detail="Source is disabled.")
    try:
        return enqueue_source(source)
    except Exception as exc:
        SourceRepository.update(source_id, {"last_status": "dispatch_failed"})
        raise HTTPException(status_code=503, detail=f"Could not queue source sync: {exc}") from exc
