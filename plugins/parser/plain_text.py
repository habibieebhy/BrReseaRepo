"""Lightweight parser for engineering source, solver, and configuration files."""

from __future__ import annotations

import json
from pathlib import Path

from brixta_sdk.context import PipelineContext
from brixta_sdk.parser import ParserPlugin
from runtime.artifacts.repository import ArtifactRepository


class PlainTextParserPlugin(ParserPlugin):
    def parse(self, context: PipelineContext) -> PipelineContext:
        if ArtifactRepository.markdown_exists(context.job_id):
            context.parsed_path = Path(f"markdown/{context.job_id}.md")
            return context
        source = Path(context.source_target)
        if context.source_type != "local_file" or not source.is_file():
            raise FileNotFoundError("Plain-text parser requires an uploaded local file.")
        text = source.read_text(encoding="utf-8", errors="replace")
        ArtifactRepository.save_markdown(context.job_id, text)
        ArtifactRepository.save_docling(
            context.job_id,
            json.dumps(
                {
                    "kind": "plain_text",
                    "filename": context.metadata.get("filename") or source.name,
                    "characters": len(text),
                },
                indent=2,
            ),
        )
        context.parsed_path = Path(f"markdown/{context.job_id}.md")
        return context

