"""CLI access to BRIXTA knowledge discovery and retrieval."""

from __future__ import annotations

import json


def parse_handle(value: str) -> str:
    prefix = "brixta://knowledge/"
    return value[len(prefix):] if value.startswith(prefix) else value


def list_command(tenant_id: str | None) -> int:
    from runtime.knowledge import list_knowledge_bases

    print(json.dumps(list_knowledge_bases(tenant_id=tenant_id), indent=2))
    return 0


def search_command(handle: str, query: str, tenant_id: str | None, limit: int) -> int:
    from runtime.knowledge import describe_knowledge_base, search_knowledge_base

    job_id = parse_handle(handle)
    resolved_tenant = tenant_id or describe_knowledge_base(job_id)["tenant_id"]
    results = search_knowledge_base(
        job_id,
        query,
        tenant_id=resolved_tenant,
        limit=limit,
    )
    print(json.dumps(results, indent=2))
    return 0
