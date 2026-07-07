from abc import ABC, abstractmethod


class ArtifactBackend(ABC):

    # -------------------------
    # Raw
    # -------------------------

    @abstractmethod
    def save_raw(self, job_id: str, data: str) -> None: ...

    @abstractmethod
    def load_raw(self, job_id: str) -> str: ...

    @abstractmethod
    def raw_exists(self, job_id: str) -> bool: ...

    # -------------------------
    # Docling
    # -------------------------

    @abstractmethod
    def save_docling(self, job_id: str, data: str) -> None: ...

    @abstractmethod
    def load_docling(self, job_id: str) -> str: ...

    @abstractmethod
    def docling_exists(self, job_id: str) -> bool: ...

    # -------------------------
    # Markdown
    # -------------------------

    @abstractmethod
    def save_markdown(self, job_id: str, data: str) -> None: ...

    @abstractmethod
    def load_markdown(self, job_id: str) -> str: ...

    @abstractmethod
    def markdown_exists(self, job_id: str) -> bool: ...

    # -------------------------
    # Chunks
    # -------------------------

    @abstractmethod
    def save_chunks(self, job_id: str, data: str) -> None: ...

    @abstractmethod
    def load_chunks(self, job_id: str) -> str: ...

    @abstractmethod
    def chunks_exists(self, job_id: str) -> bool: ...

    # -------------------------
    # Embeddings
    # -------------------------

    @abstractmethod
    def save_embeddings(self, job_id: str, data: str) -> None: ...

    @abstractmethod
    def load_embeddings(self, job_id: str) -> str: ...

    @abstractmethod
    def embeddings_exists(self, job_id: str) -> bool: ...


    # -------------------------
    # Backend
    # -------------------------

    @abstractmethod
    def provider(self) -> str:
        """
        Returns the backend provider name.

        Examples:
            local
            minio
            s3
            r2
        """
        ...

    @abstractmethod
    def health(self) -> bool:
        """
        Returns whether the backend is healthy.
        """
        ...

    @abstractmethod
    def info(self) -> dict:
        """
        Returns backend-specific information.

        Example:
        {
            "bucket": "brixta",
            "endpoint": "localhost:9000"
        }
        """
        ...