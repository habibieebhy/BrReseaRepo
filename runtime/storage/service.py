import json

from core.database import get_connection
from runtime.artifacts.repository import ArtifactRepository


def persist_embeddings(job_id: str) -> None:
    """
    Persists generated embeddings into PostgreSQL (pgvector).
    """

    if not ArtifactRepository.embeddings_exists(job_id):
        raise FileNotFoundError(
            f"Embedding artifact for '{job_id}' not found."
        )

    chunks = json.loads(
        ArtifactRepository.load_embeddings(job_id)
    )

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute(
                """
                SELECT tenant_id
                FROM "BrResearch".ingestion_jobs
                WHERE id = %s
                """,
                (job_id,),
            )

            row = cursor.fetchone()

            if row is None:
                raise RuntimeError(
                    f"Ingestion job '{job_id}' not found."
                )

            tenant_id = row[0]

            for chunk in chunks:

                cursor.execute(
                    """
                    INSERT INTO "BrResearch".document_chunks
                    (
                        job_id,
                        tenant_id,
                        chunk_index,
                        content,
                        embedding_model,
                        embedding_dimension,
                        embedding
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        job_id,
                        tenant_id,
                        chunk["chunk_id"],
                        chunk["text"],
                        chunk["embedding_model"],
                        chunk["embedding_dimension"],
                        chunk["embedding"],
                    ),
                )
