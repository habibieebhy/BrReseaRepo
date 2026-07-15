"""Public contracts for BRIXTA simulation packs."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SimulationStatus(str, Enum):
    QUEUED = "queued"
    COMPILING = "compiling"
    RUNNING = "running"
    POSTPROCESSING = "postprocessing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StructuralCouponParameters(BaseModel):
    """Approved inputs for the first deterministic material Case Card.

    Units are deliberately explicit at the API boundary. CalculiX receives a
    consistent N-mm-MPa unit system after validation.
    """

    model_config = ConfigDict(extra="forbid")

    length_mm: float = Field(default=100.0, gt=0, le=10_000, title="Coupon length", json_schema_extra={"unit": "mm", "group": "Geometry"})
    width_mm: float = Field(default=10.0, gt=0, le=2_000, title="Coupon width", json_schema_extra={"unit": "mm", "group": "Geometry"})
    thickness_mm: float = Field(default=2.0, gt=0, le=2_000, title="Coupon thickness", json_schema_extra={"unit": "mm", "group": "Geometry"})
    youngs_modulus_mpa: float = Field(default=70_000.0, gt=0, le=2_000_000, title="Young's modulus", json_schema_extra={"unit": "MPa", "group": "Material"})
    poisson_ratio: float = Field(default=0.33, ge=0, lt=0.5, title="Poisson ratio", json_schema_extra={"unit": "", "group": "Material"})
    density_kg_m3: float = Field(default=2_700.0, gt=0, le=100_000, title="Density", json_schema_extra={"unit": "kg/m³", "group": "Material"})
    load_n: float = Field(default=1_000.0, gt=0, le=100_000_000, title="Axial load", json_schema_extra={"unit": "N", "group": "Loading"})
    yield_strength_mpa: float | None = Field(default=250.0, gt=0, le=100_000, title="Yield strength", json_schema_extra={"unit": "MPa", "group": "Material"})
    mesh_divisions_length: int = Field(default=10, ge=1, le=200, title="Mesh divisions", json_schema_extra={"unit": "cells", "group": "Mesh"})

    @model_validator(mode="after")
    def validate_slenderness(self) -> "StructuralCouponParameters":
        if self.length_mm <= max(self.width_mm, self.thickness_mm):
            raise ValueError("Coupon length must exceed both cross-section dimensions.")
        return self


class OpenFoamChannelParameters(BaseModel):
    """Approved inputs for the first OpenFOAM Case Card.

    The public contract is intentionally solver-neutral JSON.  BRIXTA compiles
    these values into a complete OpenFOAM v13 case directory; users do not
    provide shell commands, dictionary fragments, or C++ source code.
    """

    model_config = ConfigDict(extra="forbid")

    length_m: float = Field(
        default=1.0,
        gt=0,
        le=100,
        title="Channel length",
        description="Internal flow length in metres.",
        json_schema_extra={"unit": "m", "group": "Geometry"},
    )
    width_m: float = Field(
        default=0.1,
        gt=0,
        le=20,
        title="Channel width",
        description="Internal channel width in metres.",
        json_schema_extra={"unit": "m", "group": "Geometry"},
    )
    height_m: float = Field(
        default=0.05,
        gt=0,
        le=20,
        title="Channel height",
        description="Internal channel height in metres.",
        json_schema_extra={"unit": "m", "group": "Geometry"},
    )
    inlet_velocity_m_s: float = Field(
        default=0.25,
        gt=0,
        le=200,
        title="Inlet velocity",
        description="Uniform inlet velocity along the channel axis.",
        json_schema_extra={"unit": "m/s", "group": "Flow"},
    )
    kinematic_viscosity_m2_s: float = Field(
        default=1.5e-5,
        gt=0,
        le=10,
        title="Kinematic viscosity",
        description="Constant kinematic viscosity used by the laminar model.",
        json_schema_extra={"unit": "m²/s", "group": "Flow"},
    )
    density_kg_m3: float = Field(
        default=1.225,
        gt=0,
        le=100_000,
        title="Density",
        description="Recorded for engineering provenance and derived quantities.",
        json_schema_extra={"unit": "kg/m³", "group": "Flow"},
    )
    end_time_s: float = Field(
        default=3.0,
        gt=0,
        le=86_400,
        title="Simulation duration",
        json_schema_extra={"unit": "s", "group": "Numerics"},
    )
    time_step_s: float = Field(
        default=0.002,
        gt=0,
        le=60,
        title="Time step",
        json_schema_extra={"unit": "s", "group": "Numerics"},
    )
    write_interval_steps: int = Field(
        default=100,
        ge=1,
        le=1_000_000,
        title="Write interval",
        description="Number of solver time steps between result writes.",
        json_schema_extra={"unit": "steps", "group": "Numerics"},
    )
    cells_length: int = Field(
        default=40,
        ge=2,
        le=500,
        title="Cells along length",
        json_schema_extra={"unit": "cells", "group": "Mesh"},
    )
    cells_width: int = Field(
        default=10,
        ge=2,
        le=200,
        title="Cells across width",
        json_schema_extra={"unit": "cells", "group": "Mesh"},
    )
    cells_height: int = Field(
        default=6,
        ge=2,
        le=200,
        title="Cells across height",
        json_schema_extra={"unit": "cells", "group": "Mesh"},
    )

    @model_validator(mode="after")
    def validate_case_bounds(self) -> "OpenFoamChannelParameters":
        total_cells = self.cells_length * self.cells_width * self.cells_height
        if total_cells > 2_000_000:
            raise ValueError("The starter OpenFOAM Case Card is limited to 2,000,000 cells.")
        cell_length = self.length_m / self.cells_length
        courant_estimate = self.inlet_velocity_m_s * self.time_step_s / cell_length
        if courant_estimate > 1:
            raise ValueError(
                "Estimated inlet Courant number exceeds 1. Reduce the time step "
                "or inlet velocity, or increase the cells along the length."
            )
        if self.end_time_s / self.time_step_s > 2_000_000:
            raise ValueError("The starter Case Card is limited to 2,000,000 time steps.")
        return self


class SimulationRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str = Field(min_length=1, max_length=200)
    case_card_id: str = Field(default="structural_coupon_tension_v1")
    execution_mode: Literal["preview", "solver"] = "preview"
    parameters: dict[str, Any]
    knowledge_base_ids: list[str] = Field(default_factory=list, max_length=20)
    evidence_query: str | None = Field(default=None, max_length=2_000)
    label: str | None = Field(default=None, max_length=200)


class SimulationPreflightRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str = Field(min_length=1, max_length=200)
    case_card_id: str = Field(default="structural_coupon_tension_v1")
    parameters: dict[str, Any]
    knowledge_base_ids: list[str] = Field(default_factory=list, max_length=20)
    evidence_query: str | None = Field(default=None, max_length=2_000)


class CompiledCase(BaseModel):
    case_name: str
    solver: str
    entry_file: str
    files: dict[str, str]
    analytical_reference: dict[str, Any]


class RunnerResult(BaseModel):
    return_code: int
    stdout: str
    stderr: str
    files: dict[str, bytes] = Field(default_factory=dict)
