"""Deterministic CalculiX input compiler for approved Case Cards."""

from __future__ import annotations

import json
from string import Template

from brixta_sdk.simulation import CompiledCase, StructuralCouponParameters
from runtime.simulations.case_cards import CASE_CARD_ID
from runtime.simulations.visualization import structural_coupon_scene


INPUT_TEMPLATE = Template(
    """** BRIXTA Structural & Material Lab
** Case Card: $case_card_id
** Generated deterministically. Values are validated before rendering.
*HEADING
$case_name
*NODE
$nodes
*ELEMENT, TYPE=C3D8, ELSET=EALL
$elements
*NSET, NSET=FIXED
$fixed_nodes
*NSET, NSET=LOADED
$loaded_nodes
*MATERIAL, NAME=MATERIAL_1
*ELASTIC
$youngs_modulus_mpa, $poisson_ratio
*DENSITY
$density_tonne_mm3
*SOLID SECTION, ELSET=EALL, MATERIAL=MATERIAL_1
*STEP
*STATIC
*BOUNDARY
FIXED, 1, 3, 0.
*CLOAD
$loads
*NODE PRINT, NSET=LOADED
U, RF
*EL PRINT, ELSET=EALL
S, E
*NODE FILE
U, RF
*EL FILE
S, E
*END STEP
"""
)


class CalculixCaseCompiler:
    def compile(self, case_card_id: str, parameters: dict) -> CompiledCase:
        if case_card_id != CASE_CARD_ID:
            raise ValueError(f"CalculiX compiler does not support '{case_card_id}'.")
        values = StructuralCouponParameters.model_validate(parameters)
        divisions = values.mesh_divisions_length

        nodes: list[str] = []
        for index in range(divisions + 1):
            x = values.length_mm * index / divisions
            coordinates = (
                (x, 0.0, 0.0),
                (x, values.width_mm, 0.0),
                (x, values.width_mm, values.thickness_mm),
                (x, 0.0, values.thickness_mm),
            )
            for offset, (cx, cy, cz) in enumerate(coordinates, start=1):
                node_id = index * 4 + offset
                nodes.append(f"{node_id}, {cx:.9g}, {cy:.9g}, {cz:.9g}")

        elements: list[str] = []
        for index in range(divisions):
            left = index * 4
            right = (index + 1) * 4
            connectivity = (
                left + 1,
                right + 1,
                right + 2,
                left + 2,
                left + 4,
                right + 4,
                right + 3,
                left + 3,
            )
            elements.append(
                f"{index + 1}, " + ", ".join(str(node) for node in connectivity)
            )

        fixed_nodes = ", ".join(str(index) for index in range(1, 5))
        loaded_ids = [divisions * 4 + index for index in range(1, 5)]
        loaded_nodes = ", ".join(str(index) for index in loaded_ids)
        nodal_load = values.load_n / 4.0
        loads = "\n".join(f"{node_id}, 1, {nodal_load:.12g}" for node_id in loaded_ids)

        area = values.width_mm * values.thickness_mm
        stress = values.load_n / area
        strain = stress / values.youngs_modulus_mpa
        displacement = strain * values.length_mm
        factor_of_safety = (
            values.yield_strength_mpa / stress if values.yield_strength_mpa else None
        )
        case_name = "brixta_structural_coupon"
        input_text = INPUT_TEMPLATE.substitute(
            case_card_id=case_card_id,
            case_name=case_name,
            nodes="\n".join(nodes),
            elements="\n".join(elements),
            fixed_nodes=fixed_nodes,
            loaded_nodes=loaded_nodes,
            youngs_modulus_mpa=f"{values.youngs_modulus_mpa:.12g}",
            poisson_ratio=f"{values.poisson_ratio:.12g}",
            density_tonne_mm3=f"{values.density_kg_m3 * 1e-12:.12g}",
            loads=loads,
        )

        analytical_reference = {
            "axial_stress_mpa": stress,
            "axial_strain": strain,
            "axial_displacement_mm": displacement,
            "factor_of_safety": factor_of_safety,
            "cross_section_area_mm2": area,
            "method": "closed-form linear-elastic axial bar reference",
        }
        simulation_spec = {
            "schema_version": "1.0",
            "case_card_id": case_card_id,
            "solver": "calculix",
            "parameters": values.model_dump(),
        }
        scene = structural_coupon_scene(values, analytical_reference)

        return CompiledCase(
            case_name=case_name,
            solver="calculix",
            entry_file=f"{case_name}.inp",
            files={
                f"{case_name}.inp": input_text,
                "simulation-spec.json": json.dumps(simulation_spec, indent=2),
                "visualization.json": json.dumps(scene, indent=2),
            },
            analytical_reference=analytical_reference,
        )
