"""Lazy plugin registry for simulation compiler/runner/postprocessor stages."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from importlib import import_module
from importlib.metadata import entry_points
from threading import Lock
from typing import Any, Iterable, Mapping


SIMULATION_STAGES = ("compiler", "runner", "postprocessor")


@dataclass(frozen=True)
class SimulationPluginSpec:
    id: str
    stage: str
    name: str
    version: str
    entrypoint: str
    capabilities: tuple[str, ...] = ()

    def public_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value.pop("entrypoint")
        value["capabilities"] = list(self.capabilities)
        return value


class SimulationPluginRegistry:
    def __init__(self) -> None:
        self._specs: dict[str, dict[str, SimulationPluginSpec]] = {
            stage: {} for stage in SIMULATION_STAGES
        }
        self._instances: dict[tuple[str, str], Any] = {}
        self._lock = Lock()

    def register(self, spec: SimulationPluginSpec) -> None:
        if spec.stage not in self._specs:
            raise ValueError(f"Unknown simulation plugin stage '{spec.stage}'.")
        if spec.id in self._specs[spec.stage]:
            raise ValueError(f"Duplicate simulation plugin '{spec.stage}/{spec.id}'.")
        self._specs[spec.stage][spec.id] = spec

    def load(self, stage: str, plugin_id: str) -> Any:
        if stage not in self._specs or plugin_id not in self._specs[stage]:
            raise ValueError(f"Unknown simulation plugin '{stage}/{plugin_id}'.")
        key = (stage, plugin_id)
        with self._lock:
            if key not in self._instances:
                module_name, class_name = self._specs[stage][plugin_id].entrypoint.split(":", 1)
                self._instances[key] = getattr(import_module(module_name), class_name)()
        return self._instances[key]

    def list(self) -> list[dict[str, Any]]:
        return [
            spec.public_dict()
            for stage in SIMULATION_STAGES
            for spec in self._specs[stage].values()
        ]


def _simulation_spec(
    value: SimulationPluginSpec | Mapping[str, Any],
) -> SimulationPluginSpec:
    if isinstance(value, SimulationPluginSpec):
        return value
    payload = dict(value)
    payload["capabilities"] = tuple(payload.get("capabilities", ()))
    return SimulationPluginSpec(**payload)


def discover_simulation_plugins(target: SimulationPluginRegistry) -> None:
    """Load immutable simulation-pack metadata from installed distributions."""

    for entrypoint in entry_points(group="brixta.simulation_plugins"):
        loaded = entrypoint.load()
        supplied = (
            loaded()
            if callable(loaded) and not isinstance(loaded, SimulationPluginSpec)
            else loaded
        )
        values: Iterable[SimulationPluginSpec | Mapping[str, Any]]
        if isinstance(supplied, (SimulationPluginSpec, Mapping)):
            values = (supplied,)
        elif isinstance(supplied, Iterable) and not isinstance(supplied, (str, bytes)):
            values = supplied
        else:
            raise ValueError(
                f"Entry point '{entrypoint.name}' did not return simulation plugin metadata."
            )
        for value in values:
            target.register(_simulation_spec(value))


simulation_registry = SimulationPluginRegistry()
simulation_registry.register(
    SimulationPluginSpec(
        "calculix",
        "compiler",
        "CalculiX Case Compiler",
        "1.0.0",
        "plugins.simulation.compiler.calculix:CalculixCaseCompiler",
        ("deterministic-template", "structured-hexahedral-mesh"),
    )
)
simulation_registry.register(
    SimulationPluginSpec(
        "openfoam",
        "compiler",
        "OpenFOAM v13 Case Compiler",
        "1.0.0",
        "plugins.simulation.compiler.openfoam:OpenFoamCaseCompiler",
        ("validated-json-spec", "deterministic-case-folder", "blockMesh"),
    )
)
simulation_registry.register(
    SimulationPluginSpec(
        "openfoam",
        "runner",
        "OpenFOAM v13 Runner",
        "1.0.0",
        "plugins.simulation.runner.openfoam:OpenFoamRunner",
        ("fixed-command-pipeline", "timeout", "no-shell", "vtk-export"),
    )
)
simulation_registry.register(
    SimulationPluginSpec(
        "openfoam",
        "postprocessor",
        "OpenFOAM Postprocessor",
        "1.0.0",
        "plugins.simulation.postprocessor.openfoam:OpenFoamPostprocessor",
        ("engineering-summary", "case-archive", "markdown-report"),
    )
)
simulation_registry.register(
    SimulationPluginSpec(
        "calculix",
        "runner",
        "CalculiX Runner",
        "1.0.0",
        "plugins.simulation.runner.calculix:CalculixRunner",
        ("local-worker", "timeout", "no-shell"),
    )
)
simulation_registry.register(
    SimulationPluginSpec(
        "calculix",
        "postprocessor",
        "CalculiX Postprocessor",
        "1.0.0",
        "plugins.simulation.postprocessor.calculix:CalculixPostprocessor",
        ("engineering-summary", "markdown-report"),
    )
)
discover_simulation_plugins(simulation_registry)
