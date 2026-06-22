from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from .types import VivadoInstallation


VERSION_RE = re.compile(r"(?:VIVADO_MCP_VERSION=|Vivado v|version=)([0-9]{4}\.[0-9]+)")


def locate_vivado(vivado_path: str | None = None) -> Path:
    candidates: list[Path] = []
    if vivado_path:
        candidates.append(Path(vivado_path))
    if env_path := os.environ.get("VIVADO_BIN"):
        candidates.append(Path(env_path))
    if path_hit := shutil.which("vivado"):
        candidates.append(Path(path_hit))
    candidates.extend(_common_windows_paths())

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()
    searched = ", ".join(str(path) for path in candidates) or "PATH and common install directories"
    raise FileNotFoundError(f"Vivado executable not found. Searched: {searched}")


def check_vivado(vivado_path: str | None = None, timeout_seconds: int = 60) -> VivadoInstallation:
    executable = locate_vivado(vivado_path)
    version = probe_vivado_version(executable, timeout_seconds=timeout_seconds)
    return VivadoInstallation(executable=executable, version=version)


def probe_vivado_version(executable: Path, timeout_seconds: int = 60) -> str | None:
    with tempfile.TemporaryDirectory(prefix="vivado_mcp_probe_") as tmp:
        script = Path(tmp) / "version_probe.tcl"
        script.write_text(
            "\n".join(
                [
                    'puts "VIVADO_MCP_VERSION=[version -short]"',
                    "exit",
                ]
            ),
            encoding="utf-8",
        )
        completed = subprocess.run(
            _vivado_command(executable, ["-mode", "batch", "-nolog", "-nojournal", "-source", str(script)]),
            cwd=tmp,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout_seconds,
        )
    output = completed.stdout or ""
    match = VERSION_RE.search(output)
    if match:
        return match.group(1)
    if completed.returncode != 0:
        raise RuntimeError(f"Vivado version probe failed with exit code {completed.returncode}: {output[-2000:]}")
    return None


def _vivado_command(executable: Path, args: list[str]) -> list[str]:
    if executable.suffix.lower() in {".bat", ".cmd"}:
        return ["cmd", "/c", str(executable), *args]
    return [str(executable), *args]


def _common_windows_paths() -> list[Path]:
    roots = [Path("C:/Xilinx/Vivado"), Path("C:/AMD/Vivado")]
    candidates: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for child in sorted(root.iterdir(), reverse=True):
            candidates.append(child / "bin" / "vivado.bat")
            candidates.append(child / "bin" / "vivado.exe")
    return candidates

