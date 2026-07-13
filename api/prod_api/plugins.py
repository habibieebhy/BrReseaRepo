"""Operational plugin discovery backed by the runtime registry."""

from core.plugin_loader import registry


def plugins(stage: str | None = None) -> dict:
    return {"plugins": registry.list(stage)}


def embedding_plugins() -> dict:
    return plugins("embedding")


def downloader_plugins() -> dict:
    return plugins("downloader")


def chunker_plugins() -> dict:
    return plugins("chunker")
