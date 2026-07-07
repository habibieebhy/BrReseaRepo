from core.config import ARTIFACT_BACKEND

from runtime.artifacts.local import LocalFilesystemBackend
from runtime.artifacts.minio import MinIOBackend


class ArtifactRepository:

    if ARTIFACT_BACKEND == "minio":
        backend = MinIOBackend()
    else:
        backend = LocalFilesystemBackend()

    # --------------------------------------------------
    # Raw
    # --------------------------------------------------

    @classmethod
    def save_raw(cls, job_id: str, data: str) -> None:
        cls.backend.save_raw(job_id, data)

    @classmethod
    def load_raw(cls, job_id: str) -> str:
        return cls.backend.load_raw(job_id)

    @classmethod
    def raw_exists(cls, job_id: str) -> bool:
        return cls.backend.raw_exists(job_id)

    # --------------------------------------------------
    # Docling
    # --------------------------------------------------

    @classmethod
    def save_docling(cls, job_id: str, data: str) -> None:
        cls.backend.save_docling(job_id, data)

    @classmethod
    def load_docling(cls, job_id: str) -> str:
        return cls.backend.load_docling(job_id)

    @classmethod
    def docling_exists(cls, job_id: str) -> bool:
        return cls.backend.docling_exists(job_id)

    # --------------------------------------------------
    # Markdown
    # --------------------------------------------------

    @classmethod
    def save_markdown(cls, job_id: str, data: str) -> None:
        cls.backend.save_markdown(job_id, data)

    @classmethod
    def load_markdown(cls, job_id: str) -> str:
        return cls.backend.load_markdown(job_id)

    @classmethod
    def markdown_exists(cls, job_id: str) -> bool:
        return cls.backend.markdown_exists(job_id)

    # --------------------------------------------------
    # Chunks
    # --------------------------------------------------

    @classmethod
    def save_chunks(cls, job_id: str, data: str) -> None:
        cls.backend.save_chunks(job_id, data)

    @classmethod
    def load_chunks(cls, job_id: str) -> str:
        return cls.backend.load_chunks(job_id)

    @classmethod
    def chunks_exists(cls, job_id: str) -> bool:
        return cls.backend.chunks_exists(job_id)

    # --------------------------------------------------
    # Embeddings
    # --------------------------------------------------

    @classmethod
    def save_embeddings(cls, job_id: str, data: str) -> None:
        cls.backend.save_embeddings(job_id, data)

    @classmethod
    def load_embeddings(cls, job_id: str) -> str:
        return cls.backend.load_embeddings(job_id)

    @classmethod
    def embeddings_exists(cls, job_id: str) -> bool:
        return cls.backend.embeddings_exists(job_id)
    @classmethod
    def provider(cls) -> str:
        return cls.backend.provider()
    @classmethod
    def health(cls) -> bool:
        return cls.backend.health()


    @classmethod
    def info(cls) -> dict:
        return cls.backend.info()