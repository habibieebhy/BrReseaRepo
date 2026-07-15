"""Deterministic OpenFOAM v13 case compiler.

Normal OpenFOAM simulations are configured through case dictionaries.  This
compiler turns the validated BRIXTA JSON contract into those dictionaries; it
never writes or compiles C++ solver source.
"""

from __future__ import annotations

import json
from string import Template

from brixta_sdk.simulation import CompiledCase, OpenFoamChannelParameters
from runtime.simulations.case_cards import OPENFOAM_CHANNEL_CASE_CARD_ID
from runtime.simulations.visualization import openfoam_channel_scene


HEADER = """/*--------------------------------*- C++ -*----------------------------------*\\
  =========                 | OpenFOAM: The Open Source CFD Toolbox
  \\      /  F ield         | Website:  https://openfoam.org
   \\    /   O peration     | Version:  13
    \\  /    A nd           |
     \\/     M anipulation  |
\\*---------------------------------------------------------------------------*/
"""


def _foam_file(*, object_name: str, class_name: str = "dictionary", location: str | None = None) -> str:
    location_line = f'    location    "{location}";\n' if location else ""
    return (
        HEADER
        + "FoamFile\n{\n"
        + "    format      ascii;\n"
        + f"    class       {class_name};\n"
        + location_line
        + f"    object      {object_name};\n"
        + "}\n\n"
    )


BLOCK_MESH = Template(
    """convertToMeters 1;

vertices
(
    (0 0 0)
    ($length 0 0)
    ($length $width 0)
    (0 $width 0)
    (0 0 $height)
    ($length 0 $height)
    ($length $width $height)
    (0 $width $height)
);

blocks
(
    hex (0 1 2 3 4 5 6 7) ($cells_length $cells_width $cells_height) simpleGrading (1 1 1)
);

edges ();

boundary
(
    inlet
    {
        type patch;
        faces ((0 4 7 3));
    }
    outlet
    {
        type patch;
        faces ((1 2 6 5));
    }
    walls
    {
        type wall;
        faces
        (
            (0 1 5 4)
            (3 7 6 2)
            (0 3 2 1)
            (4 5 6 7)
        );
    }
);
"""
)


VELOCITY = Template(
    """dimensions      [0 1 -1 0 0 0 0];

internalField   uniform (0 0 0);

boundaryField
{
    inlet
    {
        type            fixedValue;
        value           uniform ($velocity 0 0);
    }
    outlet
    {
        type            zeroGradient;
    }
    walls
    {
        type            noSlip;
    }
}
"""
)


PRESSURE = """dimensions      [0 2 -2 0 0 0 0];

internalField   uniform 0;

boundaryField
{
    inlet
    {
        type            zeroGradient;
    }
    outlet
    {
        type            fixedValue;
        value           uniform 0;
    }
    walls
    {
        type            zeroGradient;
    }
}
"""


CONTROL = Template(
    """solver          incompressibleFluid;

startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         $end_time;
deltaT          $time_step;
writeControl    timeStep;
writeInterval   $write_interval;
purgeWrite      0;
writeFormat     ascii;
writePrecision  8;
writeCompression off;
timeFormat      general;
timePrecision   8;
runTimeModifiable true;
"""
)


FV_SCHEMES = """ddtSchemes
{
    default         Euler;
}

gradSchemes
{
    default         Gauss linear;
}

divSchemes
{
    default                         none;
    div(phi,U)                      Gauss limitedLinearV 1;
    div((nuEff*dev2(T(grad(U)))))   Gauss linear;
}

laplacianSchemes
{
    default         Gauss linear corrected;
}

interpolationSchemes
{
    default         linear;
}

snGradSchemes
{
    default         corrected;
}
"""


FV_SOLUTION = """solvers
{
    p
    {
        solver          GAMG;
        tolerance       1e-7;
        relTol          0.05;
        smoother        GaussSeidel;
    }
    pFinal
    {
        $p;
        tolerance       1e-8;
        relTol          0;
    }
    U
    {
        solver          smoothSolver;
        smoother        GaussSeidel;
        tolerance       1e-7;
        relTol          0.05;
    }
    UFinal
    {
        $U;
        tolerance       1e-8;
        relTol          0;
    }
}

PIMPLE
{
    nCorrectors                 2;
    nNonOrthogonalCorrectors    0;
}
"""


README = """# BRIXTA OpenFOAM case

This folder was compiled deterministically from `simulation-spec.json` for
OpenFOAM Foundation version 13. It uses the existing `incompressibleFluid`
solver module; no C++ source was generated.

Run manually in an OpenFOAM v13 environment:

```bash
blockMesh
checkMesh
foamRun
foamToVTK -latestTime
```

Edit `simulation-spec.json` in BRIXTA and recompile to keep validation and
provenance. Direct dictionary editing is possible for experienced users, but
those edits are outside the validated BRIXTA Case Card.
"""


ALLRUN = """#!/bin/sh
cd "${0%/*}" || exit 1
blockMesh || exit 1
checkMesh || exit 1
foamRun || exit 1
foamToVTK -latestTime
"""


class OpenFoamCaseCompiler:
    def compile(self, case_card_id: str, parameters: dict) -> CompiledCase:
        if case_card_id != OPENFOAM_CHANNEL_CASE_CARD_ID:
            raise ValueError(f"OpenFOAM compiler does not support '{case_card_id}'.")
        values = OpenFoamChannelParameters.model_validate(parameters)
        hydraulic_diameter = (
            2 * values.width_m * values.height_m / (values.width_m + values.height_m)
        )
        reynolds = (
            values.inlet_velocity_m_s
            * hydraulic_diameter
            / values.kinematic_viscosity_m2_s
        )
        reference = {
            "hydraulic_diameter_m": hydraulic_diameter,
            "reynolds_number": reynolds,
            "volumetric_flow_rate_m3_s": (
                values.inlet_velocity_m_s * values.width_m * values.height_m
            ),
            "mass_flow_rate_kg_s": (
                values.inlet_velocity_m_s
                * values.width_m
                * values.height_m
                * values.density_kg_m3
            ),
            "estimated_inlet_courant_number": (
                values.inlet_velocity_m_s
                * values.time_step_s
                / (values.length_m / values.cells_length)
            ),
            "mesh_cells": values.cells_length * values.cells_width * values.cells_height,
            "method": "validated geometry and boundary-condition preflight",
        }
        spec = {
            "schema_version": "1.0",
            "case_card_id": case_card_id,
            "solver": {"id": "openfoam", "distribution": "foundation", "version": "13"},
            "parameters": values.model_dump(),
        }
        scene = openfoam_channel_scene(values, reference)
        files = {
            "simulation-spec.json": json.dumps(spec, indent=2),
            "README.md": README,
            "Allrun": ALLRUN,
            "0/U": _foam_file(object_name="U", class_name="volVectorField", location="0")
            + VELOCITY.substitute(velocity=f"{values.inlet_velocity_m_s:.12g}"),
            "0/p": _foam_file(object_name="p", class_name="volScalarField", location="0")
            + PRESSURE,
            "constant/physicalProperties": _foam_file(
                object_name="physicalProperties", location="constant"
            )
            + "viscosityModel  constant;\n"
            + f"nu              {values.kinematic_viscosity_m2_s:.12g} [m^2/s];\n",
            "system/blockMeshDict": _foam_file(object_name="blockMeshDict")
            + BLOCK_MESH.substitute(
                length=f"{values.length_m:.12g}",
                width=f"{values.width_m:.12g}",
                height=f"{values.height_m:.12g}",
                cells_length=values.cells_length,
                cells_width=values.cells_width,
                cells_height=values.cells_height,
            ),
            "system/controlDict": _foam_file(object_name="controlDict", location="system")
            + CONTROL.substitute(
                end_time=f"{values.end_time_s:.12g}",
                time_step=f"{values.time_step_s:.12g}",
                write_interval=values.write_interval_steps,
            ),
            "system/fvSchemes": _foam_file(object_name="fvSchemes", location="system")
            + FV_SCHEMES,
            "system/fvSolution": _foam_file(object_name="fvSolution", location="system")
            + FV_SOLUTION,
            "visualization.json": json.dumps(scene, indent=2),
        }
        return CompiledCase(
            case_name="brixta_openfoam_channel",
            solver="openfoam",
            entry_file="system/controlDict",
            files=files,
            analytical_reference=reference,
        )
