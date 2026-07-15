"""Bounded, allowlisted OpenFOAM v13 runner.

The runner executes a fixed command pipeline.  Neither JSON input nor users can
inject executable names, flags, shell syntax, or C++ source.
"""

from __future__ import annotations

import io
import shutil
import subprocess
import time
import zipfile
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory

from brixta_sdk.simulation import CompiledCase, RunnerResult
from core.config import (
    OPENFOAM_BLOCKMESH_EXECUTABLE,
    OPENFOAM_CHECKMESH_EXECUTABLE,
    OPENFOAM_RUN_EXECUTABLE,
    OPENFOAM_VTK_EXECUTABLE,
    SIMULATION_TIMEOUT_SECONDS,
)


def _safe_relative_path(filename: str) -> PurePosixPath:
    path = PurePosixPath(filename)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError("Compiled OpenFOAM case contains an unsafe path.")
    return path


def _zip_tree(root: Path, *, prefix: str | None = None, limit_bytes: int = 200_000_000) -> bytes:
    output = io.BytesIO()
    written = 0
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(root)
            if prefix and (not relative.parts or relative.parts[0] != prefix):
                continue
            size = path.stat().st_size
            if size > 50_000_000 or written + size > limit_bytes:
                continue
            archive.write(path, relative.as_posix())
            written += size
    return output.getvalue()


class OpenFoamRunner:
    def _executable(self, configured: str, label: str) -> str:
        executable = shutil.which(configured)
        if executable is None:
            raise RuntimeError(
                f"OpenFOAM {label} executable '{configured}' was not found. "
                "Use the pinned OpenFOAM worker image or preview mode."
            )
        return executable

    def run(self, compiled: CompiledCase) -> RunnerResult:
        if compiled.solver != "openfoam" or compiled.entry_file != "system/controlDict":
            raise ValueError("Compiled OpenFOAM case has an invalid solver contract.")
        required = {
            "0/U",
            "0/p",
            "constant/physicalProperties",
            "system/blockMeshDict",
            "system/controlDict",
            "system/fvSchemes",
            "system/fvSolution",
        }
        if not required.issubset(compiled.files):
            raise ValueError("Compiled OpenFOAM case is incomplete.")

        block_mesh = self._executable(OPENFOAM_BLOCKMESH_EXECUTABLE, "blockMesh")
        check_mesh = self._executable(OPENFOAM_CHECKMESH_EXECUTABLE, "checkMesh")
        foam_run = self._executable(OPENFOAM_RUN_EXECUTABLE, "foamRun")
        foam_to_vtk = shutil.which(OPENFOAM_VTK_EXECUTABLE)

        with TemporaryDirectory(prefix="brixta-openfoam-") as directory:
            workdir = Path(directory)
            for filename, content in compiled.files.items():
                relative = _safe_relative_path(filename)
                target = workdir.joinpath(*relative.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                if relative.as_posix() == "Allrun":
                    target.chmod(0o755)

            started = time.monotonic()
            logs: list[str] = []
            errors: list[str] = []
            return_code = 0
            commands = [
                ("blockMesh", [block_mesh]),
                ("checkMesh", [check_mesh]),
                ("foamRun", [foam_run]),
            ]
            for label, command in commands:
                remaining = max(1, int(SIMULATION_TIMEOUT_SECONDS - (time.monotonic() - started)))
                result = subprocess.run(
                    command,
                    cwd=workdir,
                    capture_output=True,
                    text=True,
                    timeout=remaining,
                    check=False,
                )
                logs.append(f"===== {label} =====\n{result.stdout[-200_000:]}")
                if result.stderr:
                    errors.append(f"===== {label} =====\n{result.stderr[-100_000:]}")
                if result.returncode != 0:
                    return_code = result.returncode
                    break

            if return_code == 0 and foam_to_vtk:
                remaining = max(1, int(SIMULATION_TIMEOUT_SECONDS - (time.monotonic() - started)))
                vtk = subprocess.run(
                    [foam_to_vtk, "-latestTime"],
                    cwd=workdir,
                    capture_output=True,
                    text=True,
                    timeout=remaining,
                    check=False,
                )
                logs.append(f"===== foamToVTK =====\n{vtk.stdout[-100_000:]}")
                if vtk.stderr:
                    errors.append(f"===== foamToVTK =====\n{vtk.stderr[-100_000:]}")
                if vtk.returncode != 0:
                    errors.append("VTK conversion failed; the OpenFOAM solution archive is still preserved.")
            elif return_code == 0:
                errors.append("foamToVTK is unavailable; no VTK export was produced.")

            files = {"openfoam-case-results.zip": _zip_tree(workdir)}
            vtk_directory = workdir / "VTK"
            if vtk_directory.exists():
                files["openfoam-vtk.zip"] = _zip_tree(workdir, prefix="VTK")
            return RunnerResult(
                return_code=return_code,
                stdout="\n".join(logs)[-500_000:],
                stderr="\n".join(errors)[-300_000:],
                files=files,
            )
