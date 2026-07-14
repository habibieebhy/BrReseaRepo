import json
from pathlib import Path
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from brixta_sdk.context import PipelineContext
from typing import Any
from brixta_sdk.embedding import EmbeddingPlugin

from runtime.artifacts.repository import ArtifactRepository


@lru_cache(maxsize=2)
def load_embedding_model(
    model: str,
    trust_remote_code: bool,
    revision: str | None,
    device: str = "cpu",
) -> SentenceTransformer:
    """Load and cache an approved embedding model for a specific device."""
    return SentenceTransformer(
        model,
        trust_remote_code=trust_remote_code,
        revision=revision,
        device=device,
    )


class SentenceTransformersEmbeddingPlugin(EmbeddingPlugin):

    name = "Sentence Transformers"
    version = "1.0.0"

    def embed(
        self,
        context: PipelineContext,
        model: str,
        profile: dict[str, Any],
    ) -> PipelineContext:

        if context.embeddings_path and context.embeddings_path.exists():
            return context

        if not ArtifactRepository.chunks_exists(context.job_id):
            raise FileNotFoundError(
                f"Chunk artifact for '{context.job_id}' not found."
            )

        chunks = json.loads(
            ArtifactRepository.load_chunks(context.job_id)
        )

        embedding_model = load_embedding_model(
        model,
        bool(profile["trust_remote_code"]),
        profile.get("revision"),
        str(profile.get("device", "cpu")),
        )

        embedded_chunks = []

        for chunk in chunks:

            vector = embedding_model.encode(
                f"{profile.get('document_prefix', '')}{chunk['text']}",
                normalize_embeddings=bool(profile.get("normalize", True)),
            ).tolist()

            if len(vector) != int(profile["dimensions"]):
                raise ValueError(
                    f"Model '{model}' returned {len(vector)} dimensions; "
                    f"its approved profile declares {profile['dimensions']}."
                )

            embedded_chunks.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"],
                    "embedding": vector,
                    "embedding_model": model,
                    "embedding_dimension": len(vector),
                }
            )

        ArtifactRepository.save_embeddings(
            context.job_id,
            json.dumps(
                embedded_chunks,
                indent=2,
                ensure_ascii=False,
            ),
        )

        context.embeddings_path = Path(
            f"embeddings/{context.job_id}.json"
        )

        return context
