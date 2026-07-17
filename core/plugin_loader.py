"""Plugin registry and lazy runtime loader.

Plugins are addressed by stable IDs rather than imported as global singletons.
This keeps discovery cheap, allows per-pipeline selection, and avoids loading
large ML dependencies in the API process until a worker actually needs them.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from importlib import import_module
from importlib.metadata import entry_points
from threading import Lock
from typing import Any, Iterable, Mapping

from core.exceptions import ValidationError


PLUGIN_STAGES = ("downloader", "parser", "chunker", "embedding", "storage")


@dataclass(frozen=True)
class ModelSpec:
    id: str
    dimensions: int
    document_prefix: str = ""
    query_prefix: str = ""
    normalize: bool = True
    trust_remote_code: bool = False
    revision: str | None = None
    device: str = "cpu"
    default: bool = False

    def public_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("trust_remote_code")
        return data


@dataclass(frozen=True)
class PluginSpec:
    id: str
    stage: str
    name: str
    version: str
    entrypoint: str
    capabilities: tuple[str, ...] = ()
    models: tuple[ModelSpec, ...] = ()
    default: bool = False

    def public_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("entrypoint")
        data["capabilities"] = list(self.capabilities)
        data["models"] = [model.public_dict() for model in self.models]
        return data


class PluginRegistry:
    def __init__(self) -> None:
        self._specs: dict[str, dict[str, PluginSpec]] = {
            stage: {} for stage in PLUGIN_STAGES
        }
        self._instances: dict[tuple[str, str], Any] = {}
        self._lock = Lock()

    def register(self, spec: PluginSpec) -> None:
        if spec.stage not in self._specs:
            raise ValidationError(f"Unknown plugin stage '{spec.stage}'.")
        if spec.id in self._specs[spec.stage]:
            raise ValidationError(
                f"Plugin '{spec.id}' is already registered for '{spec.stage}'."
            )
        if spec.default and any(item.default for item in self._specs[spec.stage].values()):
            raise ValidationError(f"Stage '{spec.stage}' already has a default plugin.")
        self._specs[spec.stage][spec.id] = spec

    def list(self, stage: str | None = None) -> list[dict[str, Any]]:
        stages = (stage,) if stage else PLUGIN_STAGES
        if stage and stage not in self._specs:
            raise ValidationError(f"Unknown plugin stage '{stage}'.")
        return [
            spec.public_dict()
            for current_stage in stages
            for spec in self._specs[current_stage].values()
        ]

    def resolve_id(self, stage: str, plugin_id: str | None = None) -> str:
        if stage not in self._specs:
            raise ValidationError(f"Unknown plugin stage '{stage}'.")
        if plugin_id:
            if plugin_id not in self._specs[stage]:
                raise ValidationError(
                    f"Plugin '{plugin_id}' is not registered for stage '{stage}'."
                )
            return plugin_id
        for spec in self._specs[stage].values():
            if spec.default:
                return spec.id
        raise ValidationError(f"Stage '{stage}' has no default plugin.")

    def load(self, stage: str, plugin_id: str | None = None) -> Any:
        resolved = self.resolve_id(stage, plugin_id)
        key = (stage, resolved)
        with self._lock:
            if key not in self._instances:
                spec = self._specs[stage][resolved]
                module_name, class_name = spec.entrypoint.split(":", 1)
                plugin_class = getattr(import_module(module_name), class_name)
                self._instances[key] = plugin_class()
        return self._instances[key]

    def validate_selection(self, selection: dict[str, str]) -> dict[str, str]:
        unknown = set(selection) - set(PLUGIN_STAGES)
        if unknown:
            raise ValidationError(f"Unknown pipeline stages: {sorted(unknown)}")
        return {
            stage: self.resolve_id(stage, selection.get(stage))
            for stage in PLUGIN_STAGES
        }

    def resolve_model(self, plugin_id: str, model_id: str | None = None) -> ModelSpec:
        if plugin_id not in self._specs["embedding"]:
            raise ValidationError(f"Embedding plugin '{plugin_id}' is not registered.")
        models = self._specs["embedding"][plugin_id].models
        if model_id:
            for model in models:
                if model.id == model_id:
                    return model
            raise ValidationError(f"Model '{model_id}' is not approved for plugin '{plugin_id}'.")
        for model in models:
            if model.default:
                return model
        if models:
            return models[0]
        raise ValidationError(f"Embedding plugin '{plugin_id}' declares no model profiles.")


def _model_spec(value: ModelSpec | Mapping[str, Any]) -> ModelSpec:
    if isinstance(value, ModelSpec):
        return value
    payload = dict(value)
    return ModelSpec(**payload)


def _plugin_spec(value: PluginSpec | Mapping[str, Any]) -> PluginSpec:
    if isinstance(value, PluginSpec):
        return value
    payload = dict(value)
    payload["capabilities"] = tuple(payload.get("capabilities", ()))
    payload["models"] = tuple(_model_spec(model) for model in payload.get("models", ()))
    return PluginSpec(**payload)


def discover_entrypoint_plugins(target: PluginRegistry) -> None:
    """Register plugins supplied by installed Python distributions.

    A distribution exposes one or more entry points in the ``brixta.plugins``
    group.  Each entry point returns a PluginSpec, a compatible mapping, or an
    iterable of either.  Discovery happens once at process startup, so API and
    worker images must contain the exact same pinned plugin distributions.
    """

    for entrypoint in entry_points(group="brixta.plugins"):
        loaded = entrypoint.load()
        supplied = loaded() if callable(loaded) and not isinstance(loaded, PluginSpec) else loaded
        values: Iterable[PluginSpec | Mapping[str, Any]]
        if isinstance(supplied, (PluginSpec, Mapping)):
            values = (supplied,)
        elif isinstance(supplied, Iterable) and not isinstance(supplied, (str, bytes)):
            values = supplied
        else:
            raise ValidationError(
                f"Entry point '{entrypoint.name}' did not return BRIXTA plugin metadata."
            )
        for value in values:
            target.register(_plugin_spec(value))


registry = PluginRegistry()

registry.register(PluginSpec("http", "downloader", "HTTP Downloader", "1.0.0", "plugins.downloader.default:DefaultDownloaderPlugin", ("url",), default=True))
registry.register(PluginSpec("local-file", "downloader", "Local File", "1.0.0", "plugins.downloader.local_file:LocalFileDownloaderPlugin", ("pdf", "office", "html", "markdown", "text")))
registry.register(PluginSpec("docling", "parser", "Docling Parser", "1.0.0", "plugins.parser.docling:DoclingParserPlugin", ("html", "pdf", "office", "ocr"), default=True))
registry.register(PluginSpec("plain-text", "parser", "Engineering Text Parser", "1.0.0", "plugins.parser.plain_text:PlainTextParserPlugin", ("source-code", "solver-input", "csv", "json", "yaml")))
registry.register(PluginSpec("docling-hybrid", "chunker", "Docling Hybrid Chunker", "1.0.0", "plugins.chunker.hybrid:HybridChunkerPlugin", ("structure-aware",), default=True))
registry.register(PluginSpec("text-window", "chunker", "Engineering Text Window", "1.0.0", "plugins.chunker.text_window:TextWindowChunkerPlugin", ("plain-text", "overlap")))
registry.register(PluginSpec(
    "sentence-transformers",
    "embedding",
    "Sentence Transformers",
    "1.0.0",
    "plugins.embedding.nomic:SentenceTransformersEmbeddingPlugin",
    ("local",),
    (
        ModelSpec(
            id="nomic-ai/nomic-embed-text-v1.5",
            dimensions=768,
            document_prefix="search_document: ",
            query_prefix="search_query: ",
            trust_remote_code=True,
            revision="b0753ae76394dd36bcfb912a46018088bca48be0",
            default=True,
        ),
        ModelSpec(id="BAAI/bge-large-en-v1.5", dimensions=1024),
        ModelSpec(id="intfloat/e5-large-v2", dimensions=1024, document_prefix="passage: ", query_prefix="query: "),
    ),
    default=True,
))
registry.register(PluginSpec("pgvector", "storage", "PostgreSQL + pgvector", "1.0.0", "plugins.storage.pgvector:PgVectorStoragePlugin", ("vector", "metadata"), default=True))
discover_entrypoint_plugins(registry)


class PluginLoader:
    """Backward-friendly facade used by Celery tasks."""

    @staticmethod
    def get(stage: str, selection: dict[str, str] | None = None) -> Any:
        selection = selection or {}
        return registry.load(stage, selection.get(stage))

    @staticmethod
    def resolve(selection: dict[str, str] | None = None) -> dict[str, str]:
        return registry.validate_selection(selection or {})
