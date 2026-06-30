from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

CapabilityProfile = Literal["safe", "trusted-local", "unrestricted"]


@dataclass(frozen=True)
class VivadoInstallation:
    executable: Path
    version: str | None


@dataclass
class TclCommandResult:
    command_id: str
    code: int
    result: str
    started: str | None
    finished: str | None
    result_path: Path | None
    command_path: Path | None
    errorinfo: str | None = None

    @property
    def ok(self) -> bool:
        return self.code == 0


@dataclass
class SessionRecord:
    session_ref: str
    vivado_path: Path
    session_dir: Path
    workspace_dir: Path
    open_gui: bool
    capability_profile: CapabilityProfile
    log_path: Path
    current_project_path: Path | None = None
