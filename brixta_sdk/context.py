from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict


class PipelineContext(BaseModel):
    """
    Shared state passed through the entire BRIXTA pipeline.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # --------------------------------------------------
    # Job Information
    # --------------------------------------------------

    job_id: str
    tenant_id: str

    # --------------------------------------------------
    # Source
    # --------------------------------------------------

    source_type: str
    source_target: str

    # --------------------------------------------------
    # Artifacts
    # --------------------------------------------------

    raw_path: Path | None = None
    parsed_path: Path | None = None
    chunks_path: Path | None = None
    embeddings_path: Path | None = None

    # --------------------------------------------------
    # Metadata
    # --------------------------------------------------

    metadata: dict[str, Any] = {}

    # --------------------------------------------------
    # Runtime Configuration
    # --------------------------------------------------

    config: dict[str, Any] = {}

    def to_dict(self) -> dict:
        """
        Serialize the context for Celery.
        """

        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict) -> "PipelineContext":
        """
        Deserialize the context received from Celery.
        """

        return cls.model_validate(data)