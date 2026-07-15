"""Deterministic overlapping chunker for source/configuration text."""

from __future__ import annotations

import json
from pathlib import Path

from brixta_sdk.chunker import ChunkerPlugin
from brixta_sdk.context import PipelineContext
from runtime.artifacts.repository import ArtifactRepository


class TextWindowChunkerPlugin(ChunkerPlugin):
    def chunk(self, context: PipelineContext) -> PipelineContext:
        if ArtifactRepository.chunks_exists(context.job_id):
            context.chunks_path = Path(f"chunks/{context.job_id}.json")
            return context
        if not ArtifactRepository.markdown_exists(context.job_id):
            raise FileNotFoundError("Parsed text artifact not found.")
        text = ArtifactRepository.load_markdown(context.job_id)
        chunk_size = min(max(int(context.config.get("text_chunk_size", 1_800)), 400), 8_000)
        overlap = min(max(int(context.config.get("text_chunk_overlap", 200)), 0), chunk_size // 2)
        step = chunk_size - overlap
        chunks = []
        for index, start in enumerate(range(0, len(text), step), start=1):
            value = text[start : start + chunk_size].strip()
            if value:
                chunks.append({"chunk_id": index, "text": value})
        if not chunks:
            raise ValueError("Uploaded engineering text file is empty.")
        ArtifactRepository.save_chunks(
            context.job_id,
            json.dumps(chunks, indent=2, ensure_ascii=False),
        )
        context.chunks_path = Path(f"chunks/{context.job_id}.json")
        return context

