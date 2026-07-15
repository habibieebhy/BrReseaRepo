"""Solver-neutral browser scene artifacts for BRIXTA simulation packs.

The dashboard consumes this deliberately small JSON contract instead of being
coupled to CalculiX FRD or OpenFOAM VTK formats.  Solver postprocessors can
replace preview values with normalised result fields without changing the UI.
"""

from __future__ import annotations

from typing import Any

from brixta_sdk.simulations import OpenFoamChannelParameters, StructuralCouponParameters


BOX_TRIANGLES = [
    [0, 2, 1], [0, 3, 2],  # bottom
    [4, 5, 6], [4, 6, 7],  # top
    [0, 1, 5], [0, 5, 4],  # side
    [3, 7, 6], [3, 6, 2],  # side
    [0, 4, 7], [0, 7, 3],  # inlet / fixed end
    [1, 2, 6], [1, 6, 5],  # outlet / loaded end
]


def _box_vertices(length: float, width: float, height: float) -> list[list[float]]:
    return [
        [0.0, 0.0, 0.0],
        [length, 0.0, 0.0],
        [length, width, 0.0],
        [0.0, width, 0.0],
        [0.0, 0.0, height],
        [length, 0.0, height],
        [length, width, height],
        [0.0, width, height],
    ]


def structural_coupon_scene(
    values: StructuralCouponParameters,
    reference: dict[str, Any],
) -> dict[str, Any]:
    vertices = _box_vertices(values.length_mm, values.width_mm, values.thickness_mm)
    displacement = float(reference["axial_displacement_mm"])
    displacements = [
        [displacement * vertex[0] / values.length_mm, 0.0, 0.0]
        for vertex in vertices
    ]
    stress = float(reference["axial_stress_mpa"])
    return {
        "schema_version": "1.0",
        "title": "Tensile coupon deformation",
        "kind": "solid",
        "source": "analytical-preview",
        "source_label": "Analytical preview — not parsed solver output",
        "units": "mm",
        "camera": {"position": [140, 90, 110], "target": [values.length_mm / 2, values.width_mm / 2, 0]},
        "meshes": [
            {
                "id": "coupon",
                "name": "Coupon",
                "vertices": vertices,
                "triangles": BOX_TRIANGLES,
                "displacements": displacements,
                "scalar": {
                    "name": "Axial stress",
                    "unit": "MPa",
                    "location": "point",
                    "values": [stress] * len(vertices),
                    "range": [0.0, max(stress, 1.0)],
                },
            }
        ],
        "vectors": [],
        "streamlines": [],
        "annotations": [
            {"label": "Fixed", "position": [0, values.width_mm / 2, values.thickness_mm / 2]},
            {"label": f"{values.load_n:g} N", "position": [values.length_mm, values.width_mm / 2, values.thickness_mm / 2]},
        ],
    }


def openfoam_channel_scene(
    values: OpenFoamChannelParameters,
    reference: dict[str, Any],
) -> dict[str, Any]:
    vertices = _box_vertices(values.length_m, values.width_m, values.height_m)
    vectors: list[dict[str, Any]] = []
    streamlines: list[dict[str, Any]] = []
    for yi in range(1, 5):
        y = values.width_m * yi / 5
        for zi in range(1, 4):
            z = values.height_m * zi / 4
            points = []
            for xi in range(13):
                x = values.length_m * xi / 12
                points.append([x, y, z])
                if xi in {1, 4, 7, 10}:
                    vectors.append(
                        {
                            "position": [x, y, z],
                            "direction": [1.0, 0.0, 0.0],
                            "magnitude": values.inlet_velocity_m_s,
                        }
                    )
            streamlines.append(
                {
                    "points": points,
                    "magnitude": values.inlet_velocity_m_s,
                }
            )
    return {
        "schema_version": "1.0",
        "title": "Rectangular channel flow",
        "kind": "flow",
        "source": "boundary-condition-preview",
        "source_label": "Boundary-condition preview — not OpenFOAM result fields",
        "units": "m",
        "camera": {"position": [1.35 * values.length_m, 1.8 * values.width_m, 2.8 * values.height_m], "target": [values.length_m / 2, values.width_m / 2, values.height_m / 2]},
        "meshes": [
            {
                "id": "channel",
                "name": "Channel domain",
                "vertices": vertices,
                "triangles": BOX_TRIANGLES,
                "displacements": [[0.0, 0.0, 0.0]] * len(vertices),
                "opacity": 0.18,
                "scalar": {
                    "name": "Velocity boundary value",
                    "unit": "m/s",
                    "location": "point",
                    "values": [values.inlet_velocity_m_s] * len(vertices),
                    "range": [0.0, max(values.inlet_velocity_m_s, 1e-9)],
                },
            }
        ],
        "vectors": vectors,
        "streamlines": streamlines,
        "annotations": [
            {"label": "Inlet", "position": [0, values.width_m / 2, values.height_m / 2]},
            {"label": "Outlet", "position": [values.length_m, values.width_m / 2, values.height_m / 2]},
            {"label": f"Re ≈ {reference['reynolds_number']:.0f}", "position": [values.length_m / 2, values.width_m, values.height_m]},
        ],
    }
