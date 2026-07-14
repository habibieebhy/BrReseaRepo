from __future__ import annotations

import json
from typing import Any

from psycopg import sql

from core.config import (
    BRIXTA_API_PUBLIC_URL,
    BRIXTA_DASHBOARD_PUBLIC_URL,
    BRIXTA_MCP_AUTH_MODE,
    BRIXTA_MCP_PUBLIC_URL,
)
from core.database import get_connection
from core.plugin_loader import registry


class KnowledgeBaseError(RuntimeError):
    """Raised when a completed ingestion cannot be used for retrieval."""


def _row_to_manifest(row: tuple[Any, ...]) -> dict[str, Any]:
    job_id = str(row[0])
    source_target = row[2]
    return {
        "id": job_id,
        "uri": f"brixta://knowledge/{job_id}",
        "name": row[8] or source_target.rsplit("/", 1)[-1] or source_target,
        "tenant_id": row[3],
        "source_type": row[1],
        "source_target": source_target,
        "status": row[4],
        "ready": row[4] == "completed" and row[5] > 0,
        "chunk_count": row[5],
        "embedding_model": row[6],
        "embedding_dimension": row[7],
        "completed_at": row[9].isoformat() if row[9] else None,
        "dashboard_url": f"{BRIXTA_DASHBOARD_PUBLIC_URL}/knowledge/{job_id}",
        "manifest_url": f"{BRIXTA_API_PUBLIC_URL}/prod/knowledge/{job_id}",
        "retrieval_url": f"{BRIXTA_API_PUBLIC_URL}/prod/knowledge/{job_id}/search",
        "mcp_url": BRIXTA_MCP_PUBLIC_URL,
        "mcp_scope": {"knowledge_base_id": job_id, "tenant_id": row[3]},
        "mcp_tools": [
            "brixta_list_knowledge_bases",
            "brixta_search",
            "brixta_get_chunk",
            "brixta_list_sources",
            "brixta_sync_source",
        ],
        "chatgpt_ready": (
            BRIXTA_MCP_PUBLIC_URL.startswith("https://")
            and BRIXTA_MCP_AUTH_MODE in {"oauth-local", "jwt"}
        ),
    }


def _knowledge_query(where: sql.Composable | None = None) -> sql.Composed:
    """Build the shared manifest query with Psycopg-safe composition."""
    return sql.SQL(
        """
        SELECT
            j.id,
            j.source_type,
            j.source_target,
            j.tenant_id,
            j.status,
            count(c.id)::integer AS chunk_count,
            min(c.embedding_model) AS embedding_model,
            min(c.embedding_dimension) AS embedding_dimension,
            COALESCE(j.context_json->'metadata'->>'filename', j.source_target) AS name,
            j.completed_at
        FROM "BrResearch".ingestion_jobs j
        LEFT JOIN "BrResearch".document_chunks c ON c.job_id = j.id
        {}
        GROUP BY j.id
        """
    ).format(where or sql.SQL(""))


def list_knowledge_bases(
    *,
    tenant_id: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    clauses: list[sql.Composable] = [sql.SQL("j.status = 'completed'")]
    params: list[Any] = []
    if tenant_id:
        clauses.append(sql.SQL("j.tenant_id = %s"))
        params.append(tenant_id)
    where = sql.SQL("WHERE ") + sql.SQL(" AND ").join(clauses)
    query = _knowledge_query(where) + sql.SQL(
        " HAVING count(c.id) > 0 ORDER BY j.completed_at DESC LIMIT %s"
    )
    params.append(min(max(limit, 1), 500))
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
    return [_row_to_manifest(row) for row in rows]


def describe_knowledge_base(
    job_id: str,
    *,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    where = sql.SQL("WHERE j.id = %s")
    params: list[Any] = [job_id]
    if tenant_id:
        where += sql.SQL(" AND j.tenant_id = %s")
        params.append(tenant_id)
    query = _knowledge_query(where)
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
    if row is None:
        raise KnowledgeBaseError("Knowledge base not found.")
    manifest = _row_to_manifest(row)
    if not manifest["ready"]:
        raise KnowledgeBaseError(
            "Knowledge base is not ready. The ingestion job must complete and persist at least one chunk."
        )
    return manifest


def _query_vector(model_id: str, plugin_id: str, query: str) -> list[float]:
    # This import is intentionally lazy. The API can run without ML packages;
    # semantic search requires requirements-rag.txt or a retrieval worker image.
    try:
        from plugins.embedding.nomic import load_embedding_model
    except ImportError as exc:
        raise KnowledgeBaseError(
            "Semantic retrieval dependencies are missing. Install requirements-rag.txt."
        ) from exc

    profile = registry.resolve_model(plugin_id, model_id)
    model = load_embedding_model(
        profile.id,
        profile.trust_remote_code,
        profile.revision,
        profile.device,
    )
    vector = model.encode(
        f"{profile.query_prefix}{query}",
        normalize_embeddings=profile.normalize,
    ).tolist()
    if len(vector) != profile.dimensions:
        raise KnowledgeBaseError(
            f"Query model returned {len(vector)} dimensions; expected {profile.dimensions}."
        )
    return vector


def search_knowledge_base(
    job_id: str,
    query: str,
    *,
    limit: int = 5,
    tenant_id: str,
) -> list[dict[str, Any]]:
    if not query.strip():
        return []
    manifest = describe_knowledge_base(job_id, tenant_id=tenant_id)
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT context_json->'plugins'->>'embedding'
                FROM "BrResearch".ingestion_jobs
                WHERE id = %s AND tenant_id = %s
                """,
                (job_id, tenant_id),
            )
            plugin_row = cursor.fetchone()
    plugin_id = (plugin_row[0] if plugin_row else None) or "sentence-transformers"
    vector = _query_vector(manifest["embedding_model"], plugin_id, query)
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    chunk_index,
                    content,
                    1 - (embedding <=> %s::vector) AS score
                FROM "BrResearch".document_chunks
                WHERE job_id = %s
                  AND tenant_id = %s
                  AND embedding_model = %s
                  AND embedding_dimension = %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (
                    json.dumps(vector),
                    job_id,
                    tenant_id,
                    manifest["embedding_model"],
                    manifest["embedding_dimension"],
                    json.dumps(vector),
                    min(max(limit, 1), 20),
                ),
            )
            rows = cursor.fetchall()
    return [
        {
            "id": f"{job_id}:{row[0]}",
            "title": f"{manifest['name']} · chunk {row[0]}",
            "text": row[1],
            "score": float(row[2]),
            "url": f"{BRIXTA_API_PUBLIC_URL}/prod/knowledge/{job_id}/chunks/{row[0]}",
            "metadata": {
                "knowledge_base_id": job_id,
                "chunk_index": row[0],
                "source": manifest["source_target"],
                "embedding_model": manifest["embedding_model"],
            },
        }
        for row in rows
    ]


def fetch_chunk(
    result_id: str,
    *,
    knowledge_base_id: str | None = None,
    tenant_id: str,
) -> dict[str, Any]:
    try:
        job_id, chunk_index_text = result_id.rsplit(":", 1)
        chunk_index = int(chunk_index_text)
    except (ValueError, TypeError) as exc:
        raise KnowledgeBaseError("Invalid BRIXTA result ID.") from exc
    if knowledge_base_id and job_id != knowledge_base_id:
        raise KnowledgeBaseError("The result does not belong to this knowledge base.")
    manifest = describe_knowledge_base(job_id, tenant_id=tenant_id)
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT content, embedding_model, embedding_dimension
                FROM "BrResearch".document_chunks
                WHERE job_id = %s
                  AND chunk_index = %s
                  AND tenant_id = %s
                """,
                (job_id, chunk_index, tenant_id),
            )
            row = cursor.fetchone()
    if row is None:
        raise KnowledgeBaseError("Knowledge result not found.")
    return {
        "id": result_id,
        "title": f"{manifest['name']} · chunk {chunk_index}",
        "text": row[0],
        "url": f"{BRIXTA_API_PUBLIC_URL}/prod/knowledge/{job_id}/chunks/{chunk_index}",
        "metadata": {
            "knowledge_base_id": job_id,
            "chunk_index": chunk_index,
            "source": manifest["source_target"],
            "embedding_model": row[1],
            "embedding_dimension": row[2],
        },
    }
