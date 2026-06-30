"""Parsers for fileset and constraint diagnostic TSV outputs.

Each parser takes the path to a TSV file written by the corresponding Tcl
helper in :mod:`vivado_cli.tcl` and returns a structured ``dict`` for the
CLI response payload.
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
            fileset_type = parts[2] if len(parts) > 2 else ""
            filesets.append(
                {
                    "name": parts[1] if len(parts) > 1 else "",
                    "type": fileset_type,
                    "category": _fileset_category(fileset_type),
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
            synth_enabled = _optional_bool(parts[5] if len(parts) > 5 else "")
            sim_enabled = _optional_bool(parts[6] if len(parts) > 6 else "")
            impl_enabled = _optional_bool(parts[7] if len(parts) > 7 else "")
            used_in = _parse_used_in(parts[8] if len(parts) > 8 else "")
            if used_in:
                synth_enabled = "synthesis" in used_in
                sim_enabled = "simulation" in used_in
                impl_enabled = "implementation" in used_in
            else:
                used_in = _used_in(synth_enabled, sim_enabled, impl_enabled)
            files.append(
                {
                    "path": parts[1] if len(parts) > 1 else "",
                    "file_type": parts[2] if len(parts) > 2 else "",
                    "library": parts[3] if len(parts) > 3 else "",
                    "processing_order": int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0,
                    "is_enabled_synthesis": synth_enabled,
                    "is_enabled_simulation": sim_enabled,
                    "is_enabled_implementation": impl_enabled,
                    "used_in": used_in,
                    "active_in": {
                        "synthesis": synth_enabled,
                        "simulation": sim_enabled,
                        "implementation": impl_enabled,
                    },
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
                        "create_generated_clock": _to_int(parts[8] if len(parts) > 8 else "0"),
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
    described_files = [
        file
        for desc in described_filesets
        for file in _list_dicts(desc.get("files"))
        if not _is_generated_ip_artifact(str(file.get("path") or ""))
    ]
    source_files = [file for file in described_files if _is_source_file(str(file.get("file_type") or ""))]
    xdc_in_source = [
        {"fileset": desc.get("name"), "path": file.get("path")}
        for desc in described_filesets
        if _fileset_category(_fileset_type(desc, filesets)) not in {"constraint", "block_source"}
        for file in _list_dicts(desc.get("files"))
        if _is_xdc_file(str(file.get("file_type") or ""), str(file.get("path") or ""))
        and not _is_generated_ip_artifact(str(file.get("path") or ""))
    ]

    duplicates = sorted(path for path, count in _counts(project_paths).items() if path and count > 1)
    if duplicates:
        issues.append(_issue("duplicate.source_path", "medium", paths=duplicates, legacy_issue_id="file.duplicate"))

    top = str(project.get("top") or _first_non_empty(desc.get("properties", {}).get("TOP") for desc in described_filesets) or "")
    if top and source_files and not _top_name_appears_in_sources(top, source_files):
        issues.append(
            _issue(
                "top.not_found",
                "high",
                legacy_issue_id="top.not_found_in_files",
                confidence="heuristic",
                top=top,
                checked_files=[file.get("path") for file in source_files],
                detail="No source filename stem matched the top name; this does not parse HDL module declarations.",
            )
        )

    if xdc_in_source:
        issues.append(_issue("xdc.in_wrong_fileset", "medium", legacy_issue_id="constraint.in_source_fileset", files=xdc_in_source))

    disabled_synth = [
        {"path": file.get("path"), "fileset": _fileset_for_file(file, described_filesets)}
        for file in source_files
        if file.get("is_enabled_synthesis") is False
    ]
    if disabled_synth:
        issues.append(_issue("source.disabled_for_synthesis", "high", files=disabled_synth))

    markers = constraints.get("xdc_markers") if isinstance(constraints.get("xdc_markers"), dict) else {}
    if constraints.get("has_project") is not False and int(markers.get("create_clock", 0) or 0) == 0:
        issues.append(_issue("constraint.no_create_clock", "medium", legacy_issue_id="constraints.no_create_clock"))

    constraint_paths = {_path_key(str(row.get("path") or "")) for row in _list_dicts(constraints.get("constraint_files"))}
    project_xdc_paths = {
        str(row.get("path") or "")
        for row in project_files
        if _is_xdc_file(str(row.get("file_type") or ""), str(row.get("path") or ""))
        and not _is_generated_ip_artifact(str(row.get("path") or ""))
    }
    missing_from_constraints = sorted(path for path in project_xdc_paths if path and _path_key(path) not in constraint_paths)
    if missing_from_constraints:
        issues.append(_issue("xdc.not_in_constraint_set", "medium", legacy_issue_id="constraint.not_in_constraint_set", paths=missing_from_constraints))

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
        "issues": _with_legacy_aliases(issues),
        "recommendations": _source_audit_recommendations(issues),
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
            issues.append(
                {
                    "issue_id": "xdc.no_create_clock_in_fileset",
                    "severity": "medium",
                    "fileset": fileset,
                    "suggestion": "Add or move a create_clock constraint before timing exceptions and I/O delays.",
                }
            )
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
                        "suggestion": "Move clock definition XDC files before exception or I/O delay XDC files.",
                    }
                )

    for warning in diagnostics.get("warnings", []) if isinstance(diagnostics.get("warnings"), list) else []:
        issues.append({"issue_id": f"diagnostic.{warning}", "severity": "medium", "warning": warning})
    reorder_plan = _xdc_reorder_plan(by_fileset)
    actions = [
        {
            "tool": "vivado_constraint_set_apply",
            "action": "reorder",
            "fileset": fileset,
            "reorder": paths,
            "why": "Place XDC files with clock definitions before exceptions, I/O delays, and pin-only constraints.",
        }
        for fileset, paths in reorder_plan.items()
        if paths
    ]

    return {
        "ok": not any(issue["severity"] == "high" for issue in issues),
        "filesets": by_fileset,
        "issues": issues,
        "reorder_plan": reorder_plan,
        "actions": actions,
        "suggested_next_tools": ["vivado_constraint_set_apply", "vivado_search_official_docs"],
    }


def _to_int(value: str) -> int:
    return int(value) if str(value).lstrip("-").isdigit() else 0


def _used_in(synthesis: bool, simulation: bool, implementation: bool) -> list[str]:
    scopes = []
    if synthesis is True:
        scopes.append("synthesis")
    if simulation is True:
        scopes.append("simulation")
    if implementation is True:
        scopes.append("implementation")
    return scopes


def _optional_bool(value: str) -> bool | None:
    if value == "":
        return None
    return value == "1"


def _parse_used_in(value: str) -> list[str]:
    normalized = str(value or "").replace("{", " ").replace("}", " ").replace(",", " ")
    scopes = []
    for scope in normalized.split():
        lowered = scope.lower()
        if lowered in {"synthesis", "simulation", "implementation"} and lowered not in scopes:
            scopes.append(lowered)
    return scopes


def _issue(issue_id: str, severity: str, *, legacy_issue_id: str | None = None, **fields: object) -> dict[str, object]:
    row: dict[str, object] = {"issue_id": issue_id, "severity": severity}
    if legacy_issue_id:
        row["legacy_issue_id"] = legacy_issue_id
    row.update(fields)
    return row


def _with_legacy_aliases(issues: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for issue in issues:
        rows.append(issue)
        legacy = issue.get("legacy_issue_id")
        if isinstance(legacy, str) and legacy:
            alias = dict(issue)
            alias["issue_id"] = legacy
            alias["canonical_issue_id"] = issue.get("issue_id")
            rows.append(alias)
    return rows


def _source_audit_recommendations(issues: list[dict[str, object]]) -> list[dict[str, str]]:
    recommendations: list[dict[str, str]] = []

    def add(tool: str, why: str) -> None:
        if not any(row["tool"] == tool for row in recommendations):
            recommendations.append({"tool": tool, "why": why})

    issue_ids = {str(issue.get("issue_id")) for issue in issues}
    if {"top.not_found", "source.disabled_for_synthesis", "duplicate.source_path"} & issue_ids:
        add("vivado_describe_fileset", "Inspect source fileset files, top, library, processing order, and USED_IN flags.")
        add("vivado_fileset_apply", "Fix top, include directories, defines, or fileset properties through a structured tool.")
    if {"xdc.in_wrong_fileset", "xdc.not_in_constraint_set", "constraint.no_create_clock"} & issue_ids:
        add("vivado_constraint_set_apply", "Move XDC files into constraint sets or adjust constraint USED_IN scopes.")
        add("vivado_xdc_order_check", "Check XDC order after constraint set changes.")
    if not recommendations:
        add("vivado_project_summary", "Project source/fileset audit did not find high-priority issues; refresh project state as needed.")
    return recommendations


def _xdc_reorder_plan(by_fileset: dict[str, list[dict[str, object]]]) -> dict[str, list[str]]:
    plan: dict[str, list[str]] = {}
    for fileset, rows in by_fileset.items():
        if not rows:
            continue
        ordered = sorted(rows, key=lambda row: (_xdc_priority(row), int(row.get("order") or 0), str(row.get("path") or "")))
        paths = [str(row.get("path") or "") for row in ordered if row.get("path")]
        original = [str(row.get("path") or "") for row in rows if row.get("path")]
        if paths and paths != original:
            plan[fileset] = paths
    return plan


def _xdc_priority(row: dict[str, object]) -> int:
    if int(row.get("create_clock") or 0):
        return 0
    if int(row.get("create_generated_clock") or 0):
        return 1
    if any(int(row.get(key) or 0) for key in ("set_input_delay", "set_output_delay")):
        return 2
    if any(int(row.get(key) or 0) for key in ("set_false_path", "set_clock_groups")):
        return 3
    return 4


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


def _fileset_category(fileset_type: str) -> str:
    normalized = str(fileset_type or "").lower()
    if normalized in {"source", "designsrcs", "design_sources"}:
        return "source"
    if normalized in {"simulation", "simulationsrcs", "simulation_sources"}:
        return "simulation"
    if normalized in {"constrs", "constraint", "constraints"}:
        return "constraint"
    if normalized in {"blocksrcs", "block_source", "block_sources"}:
        return "block_source"
    if normalized == "utils":
        return "utility"
    return "other"


def _fileset_type(desc: dict[str, object], filesets: dict[str, object]) -> str:
    name = str(desc.get("name") or "")
    for row in _list_dicts(filesets.get("filesets")):
        if row.get("name") == name:
            return str(row.get("type") or "")
    return str(desc.get("properties", {}).get("FILESET_TYPE") if isinstance(desc.get("properties"), dict) else "")


def _path_key(path: str) -> str:
    return str(path or "").replace("\\", "/").lower()


def _is_generated_ip_artifact(path: str) -> bool:
    normalized = _path_key(path)
    return "/.gen/sources_1/ip/" in normalized or ".gen/sources_1/ip/" in normalized


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
