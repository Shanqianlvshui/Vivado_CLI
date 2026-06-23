"""Parsers for fileset and constraint diagnostic TSV outputs.

Each parser takes the path to a TSV file written by the corresponding Tcl
helper in :mod:`vivado_mcp.tcl` and returns a structured ``dict`` for the
MCP response payload.
"""
from __future__ import annotations

from pathlib import Path


def _read_tsv(path: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line:
            continue
        rows.append(line.split("\t"))
    return rows


def parse_list_filesets(path: Path) -> dict[str, object]:
    filesets: list[dict[str, object]] = []
    has_project = False
    current_project = ""
    for parts in _read_tsv(path):
        if not parts:
            continue
        key = parts[0]
        if key == "has_project":
            has_project = parts[1] == "1" if len(parts) > 1 else False
        elif key == "current_project":
            current_project = parts[1] if len(parts) > 1 else ""
        elif key == "fileset":
            filesets.append(
                {
                    "name": parts[1] if len(parts) > 1 else "",
                    "type": parts[2] if len(parts) > 2 else "",
                    "file_count": int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0,
                    "is_enabled_synthesis": parts[4] == "1" if len(parts) > 4 else False,
                    "is_enabled_simulation": parts[5] == "1" if len(parts) > 5 else False,
                    "is_enabled_implementation": parts[6] == "1" if len(parts) > 6 else False,
                    "top": parts[7] if len(parts) > 7 else "",
                    "is_default": parts[8] == "1" if len(parts) > 8 else False,
                }
            )
    return {
        "has_project": has_project,
        "current_project": current_project,
        "filesets": filesets,
    }


def parse_describe_fileset(path: Path) -> dict[str, object]:
    fileset_name = ""
    properties: dict[str, str] = {}
    files: list[dict[str, object]] = []
    for parts in _read_tsv(path):
        if not parts:
            continue
        key = parts[0]
        if key == "fileset":
            fileset_name = parts[1] if len(parts) > 1 else ""
        elif key == "property":
            if len(parts) >= 3:
                properties[parts[1]] = parts[2]
        elif key == "file":
            files.append(
                {
                    "path": parts[1] if len(parts) > 1 else "",
                    "file_type": parts[2] if len(parts) > 2 else "",
                    "library": parts[3] if len(parts) > 3 else "",
                    "processing_order": int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0,
                    "is_enabled_synthesis": parts[5] == "1" if len(parts) > 5 else False,
                    "is_enabled_simulation": parts[6] == "1" if len(parts) > 6 else False,
                    "is_enabled_implementation": parts[7] == "1" if len(parts) > 7 else False,
                }
            )
    return {
        "name": fileset_name,
        "properties": properties,
        "files": files,
    }


def parse_constraint_diagnostics(path: Path) -> dict[str, object]:
    has_project = False
    current_project = ""
    filesets: list[dict[str, object]] = []
    constraint_files: list[dict[str, object]] = []
    markers: dict[str, int] = {}
    warnings: list[str] = []
    for parts in _read_tsv(path):
        if not parts:
            continue
        key = parts[0]
        if key == "has_project":
            has_project = parts[1] == "1" if len(parts) > 1 else False
        elif key == "current_project":
            current_project = parts[1] if len(parts) > 1 else ""
        elif key == "fileset":
            filesets.append(
                {
                    "name": parts[1] if len(parts) > 1 else "",
                    "type": parts[2] if len(parts) > 2 else "",
                    "is_default": parts[3] == "1" if len(parts) > 3 else False,
                    "is_enabled_synthesis": parts[4] == "1" if len(parts) > 4 else False,
                    "is_enabled_simulation": parts[5] == "1" if len(parts) > 5 else False,
                    "is_enabled_implementation": parts[6] == "1" if len(parts) > 6 else False,
                    "top": parts[7] if len(parts) > 7 else "",
                }
            )
        elif key == "constraint_file":
            constraint_files.append(
                {
                    "fileset": parts[1] if len(parts) > 1 else "",
                    "order": int(parts[2]) if len(parts) > 2 and parts[2].lstrip("-").isdigit() else 0,
                    "path": parts[3] if len(parts) > 3 else "",
                    "file_type": parts[4] if len(parts) > 4 else "",
                }
            )
        elif key == "marker":
            if len(parts) >= 3:
                markers[parts[1]] = int(parts[2]) if parts[2].isdigit() else 0
        elif key == "warning":
            if len(parts) >= 2:
                warnings.append(parts[1])
    # Stable, methodology-driven ordering of the XDC files so callers can
    # quickly see the global loading sequence (UG903 / UG949).
    constraint_files.sort(key=lambda row: (str(row.get("fileset", "")), int(row.get("order", 0))))
    return {
        "has_project": has_project,
        "current_project": current_project,
        "constrs_filesets": filesets,
        "constraint_files": constraint_files,
        "xdc_markers": markers,
        "warnings": warnings,
    }
