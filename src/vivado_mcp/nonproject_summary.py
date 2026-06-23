from __future__ import annotations

from pathlib import Path


def parse_nonproject_summary(path: Path) -> dict[str, object]:
    summary: dict[str, object] = {
        "files": [],
        "constraints": [],
        "steps": [],
        "checkpoints": [],
        "reports": [],
        "messages": [],
    }
    for parts in _read_tsv(path):
        if not parts:
            continue
        key = parts[0]
        if key == "file":
            _list(summary, "files").append(
                {
                    "kind": parts[1] if len(parts) > 1 else "",
                    "path": parts[2] if len(parts) > 2 else "",
                    "library": parts[3] if len(parts) > 3 else "",
                }
            )
        elif key == "constraint":
            _list(summary, "constraints").append(
                {
                    "path": parts[1] if len(parts) > 1 else "",
                    "scope": parts[2] if len(parts) > 2 else "",
                }
            )
        elif key == "step":
            _list(summary, "steps").append(
                {
                    "name": parts[1] if len(parts) > 1 else "",
                    "status": parts[2] if len(parts) > 2 else "",
                    "detail": parts[3] if len(parts) > 3 else "",
                }
            )
        elif key == "checkpoint":
            _list(summary, "checkpoints").append(
                {
                    "step": parts[1] if len(parts) > 1 else "",
                    "path": parts[2] if len(parts) > 2 else "",
                }
            )
        elif key == "report":
            _list(summary, "reports").append(
                {
                    "type": parts[1] if len(parts) > 1 else "",
                    "path": parts[2] if len(parts) > 2 else "",
                }
            )
        elif key == "message":
            _list(summary, "messages").append(
                {
                    "severity": parts[1] if len(parts) > 1 else "",
                    "text": parts[2] if len(parts) > 2 else "",
                }
            )
        elif key == "part" and len(parts) > 1:
            summary["part"] = parts[1]
        elif key == "top" and len(parts) > 1:
            summary["top"] = parts[1]
    summary["file_count"] = len(summary["files"]) if isinstance(summary["files"], list) else 0
    summary["constraint_count"] = len(summary["constraints"]) if isinstance(summary["constraints"], list) else 0
    summary["step_count"] = len(summary["steps"]) if isinstance(summary["steps"], list) else 0
    return summary


def _read_tsv(path: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip():
            rows.append(line.split("\t"))
    return rows


def _list(container: dict[str, object], key: str) -> list[object]:
    value = container.setdefault(key, [])
    assert isinstance(value, list)
    return value
