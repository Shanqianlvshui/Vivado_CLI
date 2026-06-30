from __future__ import annotations

import os
from pathlib import Path


class PathPolicy:
    def __init__(self, roots: list[Path]) -> None:
        resolved = []
        for root in roots:
            resolved_root = root.resolve()
            if resolved_root not in resolved:
                resolved.append(resolved_root)
        if not resolved:
            raise ValueError("PathPolicy requires at least one root")
        self.roots = resolved

    @classmethod
    def from_environment(cls, default_workspace: Path) -> "PathPolicy":
        roots = [default_workspace]
        env_roots = os.environ.get("VIVADO_CLI_ALLOWED_ROOTS")
        if env_roots:
            roots.extend(Path(item) for item in env_roots.split(os.pathsep) if item.strip())
        return cls(roots)

    def require_under_roots(self, path: str | Path, *, label: str, must_exist: bool | None = None) -> Path:
        resolved = Path(path).resolve()
        if must_exist is True and not resolved.exists():
            raise FileNotFoundError(f"{label} does not exist: {resolved}")
        if must_exist is False and not resolved.parent.exists():
            raise FileNotFoundError(f"{label} parent does not exist: {resolved.parent}")
        if not self.is_allowed(resolved):
            allowed = "; ".join(str(root) for root in self.roots)
            raise PermissionError(f"{label} must be under an allowed workspace root. Path: {resolved}. Roots: {allowed}")
        return resolved

    def require_output_name(self, name: str, *, default_suffix: str = ".rpt") -> str:
        path = Path(name)
        if path.is_absolute() or len(path.parts) != 1:
            raise PermissionError("Output name must be a filename, not a path")
        if not name.strip() or name in {".", ".."}:
            raise ValueError("Output name cannot be empty or relative traversal")
        if default_suffix and not name.lower().endswith(default_suffix.lower()):
            return name + default_suffix
        return name

    def is_allowed(self, path: Path) -> bool:
        resolved = path.resolve()
        return any(root == resolved or root in resolved.parents for root in self.roots)
