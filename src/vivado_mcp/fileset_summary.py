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
    file_markers: list[dict[str, object]] = []
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
        elif key == "file_marker":
            if len(parts) >= 4:
                file_markers.append(
                    {
                        "fileset": parts[1],
                        "path": parts[2],
                        "create_clock": _to_int(parts[3] if len(parts) > 3 else "0"),
                        "set_false_path": _to_int(parts[4] if len(parts) > 4 else "0"),
                        "set_input_delay": _to_int(parts[5] if len(parts) > 5 else "0"),
                        "set_output_delay": _to_int(parts[6] if len(parts) > 6 else "0"),
                        "set_clock_groups": _to_int(parts[7] if len(parts) > 7 else "0"),
                    }
                )
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
        "xdc_file_markers": file_markers,
        "warnings": warnings,
    }


def analyze_source_audit(
    project: dict[str, object],
    filesets: dict[str, object],
    described_filesets: list[dict[str, object]],
    constraints: dict[str, object],
) -> dict[str, object]:
    issues: list[dict[str, object]] = []
    project_files = _list_dicts(project.get("files"))
    project_paths = [str(row.get("path") or "") for row in project_files if row.get("path")]
    described_files = [file for desc in described_filesets for file in _list_dicts(desc.get("files"))]
    source_files = [file for file in described_files if _is_source_file(str(file.get("file_type") or ""))]
    xdc_in_source = [
        {"fileset": desc.get("name"), "path": file.get("path")}
        for desc in described_filesets
        if _fileset_type(desc, filesets) != "Constrs"
        for file in _list_dicts(desc.get("files"))
        if _is_xdc_file(str(file.get("file_type") or ""), str(file.get("path") or ""))
    ]

    duplicates = sorted(path for path, count in _counts(project_paths).items() if path and count > 1)
    if duplicates:
        issues.append({"issue_id": "file.duplicate", "severity": "medium", "paths": duplicates})

    top = str(project.get("top") or _first_non_empty(desc.get("properties", {}).get("TOP") for desc in described_filesets) or "")
    if top and source_files and not _top_name_appears_in_sources(top, source_files):
        issues.append(
            {
                "issue_id": "top.not_found_in_files",
                "severity": "high",
                "confidence": "heuristic",
                "top": top,
                "checked_files": [file.get("path") for file in source_files],
                "detail": "No source filename stem matched the top name; this does not parse HDL module declarations.",
            }
        )

    if xdc_in_source:
        issues.append({"issue_id": "constraint.in_source_fileset", "severity": "medium", "files": xdc_in_source})

    disabled_synth = [
        {"path": file.get("path"), "fileset": _fileset_for_file(file, described_filesets)}
        for file in source_files
        if file.get("is_enabled_synthesis") is False
    ]
    if disabled_synth:
        issues.append({"issue_id": "source.disabled_for_synthesis", "severity": "high", "files": disabled_synth})

    markers = constraints.get("xdc_markers") if isinstance(constraints.get("xdc_markers"), dict) else {}
    if constraints.get("has_project") is not False and int(markers.get("create_clock", 0) or 0) == 0:
        issues.append({"issue_id": "constraints.no_create_clock", "severity": "medium"})

    constraint_paths = {str(row.get("path") or "") for row in _list_dicts(constraints.get("constraint_files"))}
    project_xdc_paths = {str(row.get("path") or "") for row in project_files if _is_xdc_file(str(row.get("file_type") or ""), str(row.get("path") or ""))}
    missing_from_constraints = sorted(path for path in project_xdc_paths if path and path not in constraint_paths)
    if missing_from_constraints:
        issues.append({"issue_id": "constraint.not_in_constraint_set", "severity": "medium", "paths": missing_from_constraints})

    return {
        "ok": not any(issue["severity"] in {"high"} for issue in issues),
        "summary": {
            "has_project": bool(project.get("has_project")),
            "fileset_count": len(_list_dicts(filesets.get("filesets"))),
            "project_file_count": len(project_files),
            "described_fileset_count": len(described_filesets),
            "source_file_count": len(source_files),
            "constraint_file_count": len(constraint_paths),
            "top": top,
        },
        "issues": issues,
        "suggested_next_tools": ["vivado_fileset_apply", "vivado_constraint_set_apply", "vivado_xdc_order_check"],
    }


def analyze_xdc_order(diagnostics: dict[str, object]) -> dict[str, object]:
    files = _list_dicts(diagnostics.get("constraint_files"))
    file_markers = {str(row.get("path") or ""): row for row in _list_dicts(diagnostics.get("xdc_file_markers"))}
    by_fileset: dict[str, list[dict[str, object]]] = {}
    issues: list[dict[str, object]] = []
    for row in files:
        enriched = dict(row)
        enriched.update(file_markers.get(str(row.get("path") or ""), {}))
        by_fileset.setdefault(str(row.get("fileset") or ""), []).append(enriched)

    for fileset, rows in by_fileset.items():
        rows.sort(key=lambda row: int(row.get("order") or 0))
        first_clock_order = next((int(row.get("order") or 0) for row in rows if int(row.get("create_clock") or 0)), None)
        if first_clock_order is None and rows:
            issues.append({"issue_id": "xdc.no_create_clock_in_fileset", "severity": "medium", "fileset": fileset})
            continue
        if first_clock_order is None:
            continue
        for row in rows:
            order = int(row.get("order") or 0)
            has_exception = any(int(row.get(key) or 0) for key in ("set_false_path", "set_input_delay", "set_output_delay", "set_clock_groups"))
            if has_exception and order < first_clock_order:
                issues.append(
                    {
                        "issue_id": "xdc.exception_before_clock",
                        "severity": "high",
                        "fileset": fileset,
                        "path": row.get("path"),
                        "order": order,
                        "first_clock_order": first_clock_order,
                    }
                )

    for warning in diagnostics.get("warnings", []) if isinstance(diagnostics.get("warnings"), list) else []:
        issues.append({"issue_id": f"diagnostic.{warning}", "severity": "medium", "warning": warning})

    return {
        "ok": not any(issue["severity"] == "high" for issue in issues),
        "filesets": by_fileset,
        "issues": issues,
        "suggested_next_tools": ["vivado_constraint_set_apply", "vivado_search_official_docs"],
    }


def _to_int(value: str) -> int:
    return int(value) if str(value).lstrip("-").isdigit() else 0


def _list_dicts(value: object) -> list[dict[str, object]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _counts(values: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def _is_xdc_file(file_type: str, path: str) -> bool:
    return file_type.upper() == "XDC" or path.lower().endswith(".xdc")


def _is_source_file(file_type: str) -> bool:
    lowered = file_type.lower()
    return any(term in lowered for term in ("verilog", "vhdl", "systemverilog"))


def _fileset_type(desc: dict[str, object], filesets: dict[str, object]) -> str:
    name = str(desc.get("name") or "")
    for row in _list_dicts(filesets.get("filesets")):
        if row.get("name") == name:
            return str(row.get("type") or "")
    return str(desc.get("properties", {}).get("FILESET_TYPE") if isinstance(desc.get("properties"), dict) else "")


def _first_non_empty(values) -> str:
    for value in values:
        if value:
            return str(value)
    return ""


def _top_name_appears_in_sources(top: str, source_files: list[dict[str, object]]) -> bool:
    top_lower = top.lower()
    for file in source_files:
        path = str(file.get("path") or "").replace("\\", "/").lower()
        stem = Path(path).stem.lower()
        if stem == top_lower:
            return True
    return False


def _fileset_for_file(file: dict[str, object], described_filesets: list[dict[str, object]]) -> str:
    path = file.get("path")
    for desc in described_filesets:
        if any(row.get("path") == path for row in _list_dicts(desc.get("files"))):
            return str(desc.get("name") or "")
    return ""
