"""Approved Case Cards exposed by the Structural & Material Lab."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from brixta_sdk.simulation import OpenFoamChannelParameters, StructuralCouponParameters


CASE_CARD_ID = "structural_coupon_tension_v1"
OPENFOAM_CHANNEL_CASE_CARD_ID = "openfoam_channel_flow_v1"


_PARAMETER_MODELS: dict[str, type[BaseModel]] = {
    CASE_CARD_ID: StructuralCouponParameters,
    OPENFOAM_CHANNEL_CASE_CARD_ID: OpenFoamChannelParameters,
}


def case_cards() -> list[dict[str, Any]]:
    return [
        {
            "id": CASE_CARD_ID,
            "name": "Linear-elastic tensile coupon",
            "description": (
                "A deterministic rectangular coupon under axial tension. "
                "Useful for validating the BRIXTA-to-CalculiX workflow and "
                "screening material assumptions before a validated production model."
            ),
            "pack": "structural-material-lab",
            "version": "1.0.0",
            "solver": "calculix",
            "analysis_type": "static-linear-elastic",
            "execution_modes": ["preview", "solver"],
            "parameter_schema": StructuralCouponParameters.model_json_schema(),
            "outputs": [
                "axial_stress_mpa",
                "axial_displacement_mm",
                "strain",
                "factor_of_safety",
                "CalculiX FRD and DAT artifacts when solver mode is enabled",
            ],
            "limitations": [
                "Linear elastic, small displacement model",
                "Rectangular coupon with uniform axial loading",
                "Not a certification, clinical, or final design claim",
            ],
        },
        {
            "id": OPENFOAM_CHANNEL_CASE_CARD_ID,
            "name": "Rectangular channel flow",
            "description": (
                "A validated OpenFOAM v13 starter case for transient, laminar, "
                "incompressible flow through a straight rectangular channel. BRIXTA "
                "turns an editable JSON specification into a complete OpenFOAM case."
            ),
            "pack": "thermal-fluid-lab",
            "pack_name": "Thermal & Fluid Lab",
            "version": "1.0.0",
            "solver": "openfoam",
            "solver_version": "13",
            "analysis_type": "transient-laminar-incompressible-flow",
            "execution_modes": ["preview", "solver"],
            "parameter_schema": OpenFoamChannelParameters.model_json_schema(),
            "outputs": [
                "hydraulic_diameter_m",
                "reynolds_number",
                "volumetric_flow_rate_m3_s",
                "OpenFOAM case ZIP",
                "VTK result ZIP when foamToVTK is available",
            ],
            "limitations": [
                "Straight rectangular channel with a blockMesh hexahedral mesh",
                "Constant-property, laminar, incompressible flow model",
                "The browser flow scene is a boundary-condition preview until solver fields are normalised",
                "Not a certification or replacement for CFD review and mesh-independence studies",
            ],
        },
    ]


def get_case_card(case_card_id: str) -> dict[str, Any]:
    for card in case_cards():
        if card["id"] == case_card_id:
            return card
    raise ValueError(f"Unknown simulation Case Card '{case_card_id}'.")


def validate_case_parameters(case_card_id: str, parameters: dict[str, Any]) -> BaseModel:
    model = _PARAMETER_MODELS.get(case_card_id)
    if model is None:
        raise ValueError(f"Unknown simulation Case Card '{case_card_id}'.")
    return model.model_validate(parameters)
