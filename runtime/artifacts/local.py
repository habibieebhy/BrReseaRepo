from pathlib import Path

from runtime.artifacts.backend import ArtifactBackend


class LocalFilesystemBackend(ArtifactBackend):

    ROOT = Path("storage")

    def _path(self, folder: str, filename: str) -> Path:
        directory = self.ROOT / folder
        directory.mkdir(parents=True, exist_ok=True)
        return directory / filename

    # --------------------------------------------------
    # Raw
    # --------------------------------------------------

    def save_raw(self, job_id: str, data: str) -> None:
        self._path("raw", f"{job_id}.html").write_text(
            data,
            encoding="utf-8",
        )

    def load_raw(self, job_id: str) -> str:
        return self._path("raw", f"{job_id}.html").read_text(
            encoding="utf-8",
        )

    def raw_exists(self, job_id: str) -> bool:
        return self._path("raw", f"{job_id}.html").exists()

    # --------------------------------------------------
    # Docling
    # --------------------------------------------------

    def save_docling(self, job_id: str, data: str) -> None:
        self._path("docling", f"{job_id}.json").write_text(
            data,
            encoding="utf-8",
        )

    def load_docling(self, job_id: str) -> str:
        return self._path("docling", f"{job_id}.json").read_text(
            encoding="utf-8",
        )

    def docling_exists(self, job_id: str) -> bool:
        return self._path("docling", f"{job_id}.json").exists()

    # --------------------------------------------------
    # Markdown
    # --------------------------------------------------

    def save_markdown(self, job_id: str, data: str) -> None:
        self._path("markdown", f"{job_id}.md").write_text(
            data,
            encoding="utf-8",
        )

    def load_markdown(self, job_id: str) -> str:
        return self._path("markdown", f"{job_id}.md").read_text(
            encoding="utf-8",
        )

    def markdown_exists(self, job_id: str) -> bool:
        return self._path("markdown", f"{job_id}.md").exists()

    # --------------------------------------------------
    # Chunks
    # --------------------------------------------------

    def save_chunks(self, job_id: str, data: str) -> None:
        self._path("chunks", f"{job_id}.json").write_text(
            data,
            encoding="utf-8",
        )

    def load_chunks(self, job_id: str) -> str:
        return self._path("chunks", f"{job_id}.json").read_text(
            encoding="utf-8",
        )

    def chunks_exists(self, job_id: str) -> bool:
        return self._path("chunks", f"{job_id}.json").exists()

    # --------------------------------------------------
    # Embeddings
    # --------------------------------------------------

    def save_embeddings(self, job_id: str, data: str) -> None:
        self._path("embeddings", f"{job_id}.json").write_text(
            data,
            encoding="utf-8",
        )

    def load_embeddings(self, job_id: str) -> str:
        return self._path("embeddings", f"{job_id}.json").read_text(
            encoding="utf-8",
        )

    def embeddings_exists(self, job_id: str) -> bool:
        return self._path("embeddings", f"{job_id}.json").exists()
    
    def provider(self) -> str:
        return "local"


    def health(self) -> bool:
        return self.ROOT.exists()


    def info(self) -> dict:
        return {
            "root": str(self.ROOT.resolve()),
        }