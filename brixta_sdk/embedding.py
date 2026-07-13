from abc import ABC, abstractmethod

from typing import Any
from .context import PipelineContext


class EmbeddingPlugin(ABC):
    name: str
    version: str

    @abstractmethod
    def embed(
        self,
        context: PipelineContext,
        model: str,
        profile: dict[str, Any],
    ) -> PipelineContext:
        """
        Generate embeddings using the selected model.
        """
        ...
