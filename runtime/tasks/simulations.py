"""Celery task for deterministic structural/material simulations."""

from __future__ import annotations

import json
import io
import mimetypes
import traceback
import zipfile
from pathlib import PurePosixPath

from brixta_sdk.simulations import SimulationStatus
from runtime.artifacts.repository import ArtifactRepository
from runtime.celery_app import celery
from runtime.simulations.registry import simulation_registry
from runtime.simulations.repository import SimulationRunRepository


def _save_artifact(run_id: str, filename: str, data: bytes) -> dict:
    object_name = f"simulations/{run_id}/{filename}"
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    ArtifactRepository.save_object(object_name, data, content_type)
    return {"name": filename, "object_name": object_name, "size": len(data), "content_type": content_type}


def _compiled_case_zip(files: dict[str, str]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for filename, content in sorted(files.items()):
            path = PurePosixPath(filename)
            if path.is_absolute() or ".." in path.parts or not path.parts:
                raise ValueError("Compiled case contains an unsafe artifact path.")
            archive.writestr(path.as_posix(), content)
    return output.getvalue()


@celery.task(name="runtime.tasks.simulations.execute_simulation_run")
def execute_simulation_run(run_id: str) -> dict:
    run = SimulationRunRepository.get(run_id)
    if run is None:
        raise ValueError("Simulation run not found.")
    if run["terminal"]:
        return {"run_id": run_id, "status": run["status"]}

    artifacts: list[dict] = []
    try:
        solver_id = run["solver"]
        compiler = simulation_registry.load("compiler", solver_id)
        postprocessor = simulation_registry.load("postprocessor", solver_id)

        SimulationRunRepository.begin_stage(
            run_id, SimulationStatus.COMPILING, "compiler"
        )
        compiled = compiler.compile(
            run["case_card_id"],
            run["spec"]["parameters"],
        )
        for filename, content in compiled.files.items():
            artifacts.append(_save_artifact(run_id, filename, content.encode("utf-8")))
        artifacts.append(
            _save_artifact(
                run_id,
                f"{compiled.case_name}-case.zip",
                _compiled_case_zip(compiled.files),
            )
        )
        manifest = {
            "run_id": run_id,
            "tenant_id": run["tenant_id"],
            "case_card_id": run["case_card_id"],
            "solver": solver_id,
            "execution_mode": run["execution_mode"],
            "spec": run["spec"],
            "analytical_reference": compiled.analytical_reference,
            "evidence": run["evidence"],
        }
        artifacts.append(
            _save_artifact(
                run_id,
                "manifest.json",
                json.dumps(manifest, indent=2).encode("utf-8"),
            )
        )

        runner_result = None
        if run["execution_mode"] == "solver":
            SimulationRunRepository.begin_stage(
                run_id, SimulationStatus.RUNNING, "runner"
            )
            runner = simulation_registry.load("runner", solver_id)
            runner_result = runner.run(compiled)
            artifacts.append(
                _save_artifact(run_id, "solver.stdout.log", runner_result.stdout.encode("utf-8"))
            )
            artifacts.append(
                _save_artifact(run_id, "solver.stderr.log", runner_result.stderr.encode("utf-8"))
            )
            for filename, data in runner_result.files.items():
                artifacts.append(_save_artifact(run_id, filename, data))

        SimulationRunRepository.begin_stage(
            run_id, SimulationStatus.POSTPROCESSING, "postprocessor"
        )
        summary, report = postprocessor.process(
            compiled,
            runner_result,
            execution_mode=run["execution_mode"],
            evidence=run["evidence"],
        )
        artifacts.append(_save_artifact(run_id, "report.md", report.encode("utf-8")))
        artifacts.append(
            _save_artifact(
                run_id,
                "summary.json",
                json.dumps(summary, indent=2).encode("utf-8"),
            )
        )
        SimulationRunRepository.complete(run_id, summary=summary, artifacts=artifacts)
        return {"run_id": run_id, "status": "completed", "summary": summary}
    except Exception as exc:
        SimulationRunRepository.fail(
            run_id,
            f"{exc.__class__.__name__}: {exc}\n{traceback.format_exc()}",
        )
        raise
