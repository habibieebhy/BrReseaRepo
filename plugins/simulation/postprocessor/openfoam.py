"""Conservative OpenFOAM run summary and report generation."""

from __future__ import annotations

from typing import Any

from brixta_sdk.simulation import CompiledCase, RunnerResult


class OpenFoamPostprocessor:
    def process(
        self,
        compiled: CompiledCase,
        runner_result: RunnerResult | None,
        *,
        execution_mode: str,
        evidence: list[dict[str, Any]],
    ) -> tuple[dict[str, Any], str]:
        reference = dict(compiled.analytical_reference)
        solver_executed = runner_result is not None
        if runner_result is not None and runner_result.return_code != 0:
            raise RuntimeError(
                "OpenFOAM command pipeline exited with code "
                f"{runner_result.return_code}: {runner_result.stderr[-4_000:]}"
            )
        if runner_result is not None and "openfoam-case-results.zip" not in runner_result.files:
            raise RuntimeError("OpenFOAM completed without a preserved case result archive.")

        reynolds = float(reference["reynolds_number"])
        laminar_warning = reynolds >= 2_300
        limitations = [
            "Straight rectangular channel with a blockMesh hexahedral mesh",
            "Constant-property incompressible model",
            "The in-browser vectors are a boundary-condition preview, not parsed OpenFOAM fields",
            "Engineering acceptance requires mesh independence and model validation",
        ]
        if laminar_warning:
            limitations.insert(
                0,
                "The estimated Reynolds number is outside this starter card's nominal laminar range.",
            )
        summary = {
            "preflight_reference": reference,
            "execution_mode": execution_mode,
            "solver": "openfoam",
            "solver_version": "13",
            "solver_executed": solver_executed,
            "solver_return_code": runner_result.return_code if runner_result else None,
            "vtk_exported": bool(runner_result and "openfoam-vtk.zip" in runner_result.files),
            "evidence_count": len(evidence),
            "claim_level": (
                "openfoam-run-artifacts-preserved"
                if solver_executed
                else "preview-boundary-conditions-only"
            ),
            "laminar_range_warning": laminar_warning,
            "limitations": limitations,
        }
        report = "\n".join(
            [
                "# BRIXTA Thermal & Fluid Lab report",
                "",
                f"- Case: `{compiled.case_name}`",
                "- OpenFOAM distribution: `Foundation`",
                "- OpenFOAM version: `13`",
                f"- Execution mode: `{execution_mode}`",
                f"- Solver executed: `{str(solver_executed).lower()}`",
                f"- Estimated Reynolds number: `{reynolds:.6g}`",
                f"- Hydraulic diameter: `{reference['hydraulic_diameter_m']:.6g} m`",
                f"- Volumetric flow rate: `{reference['volumetric_flow_rate_m3_s']:.6g} m³/s`",
                f"- Mesh cells: `{reference['mesh_cells']}`",
                f"- Knowledge evidence items: `{len(evidence)}`",
                "",
                "## Generated integration",
                "",
                "BRIXTA compiled the validated JSON specification into the standard OpenFOAM ",
                "`0/`, `constant/`, and `system/` case structure. No C++ solver source was generated.",
                "",
                "## Interpretation boundary",
                "",
                "The browser scene previews the configured domain and inlet vectors. Use the ",
                "preserved OpenFOAM/VTK artifacts for solver-result inspection. This starter ",
                "Case Card is not a certification or substitute for CFD review.",
            ]
        )
        return summary, report
