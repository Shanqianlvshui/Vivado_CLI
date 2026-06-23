from __future__ import annotations

from pathlib import Path

NONPROJECT_STEPS = ("synth_design", "opt_design", "place_design", "route_design")
NEXT_STEP_BY_STAGE = {
    "read_sources": "synth_design",
    "synth_design": "opt_design",
    "opt_design": "place_design",
    "place_design": "route_design",
    "route_design": None,
}


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
    summary["stage"] = _nonproject_stage(summary)
    summary["next_step"] = _next_step(summary["stage"])
    summary["audit"] = analyze_nonproject_audit(summary)
    return summary


def merge_nonproject_summaries(summaries: list[dict[str, object]]) -> dict[str, object]:
    merged: dict[str, object] = {
        "files": [],
        "constraints": [],
        "steps": [],
        "checkpoints": [],
        "reports": [],
        "messages": [],
    }
    seen: dict[str, set[tuple[object, ...]]] = {
        "files": set(),
        "constraints": set(),
        "steps": set(),
        "checkpoints": set(),
        "reports": set(),
        "messages": set(),
    }
    for summary in summaries:
        for key in seen:
            for row in _dict_rows(summary.get(key)):
                marker = tuple(sorted(row.items()))
                if marker in seen[key]:
                    continue
                seen[key].add(marker)
                _list(merged, key).append(row)
        if summary.get("part"):
            merged["part"] = summary["part"]
        if summary.get("top"):
            merged["top"] = summary["top"]

    merged["file_count"] = len(_dict_rows(merged.get("files")))
    merged["constraint_count"] = len(_dict_rows(merged.get("constraints")))
    merged["step_count"] = len(_dict_rows(merged.get("steps")))
    merged["stage"] = _nonproject_stage(merged)
    merged["next_step"] = _next_step(merged["stage"])
    merged["audit"] = analyze_nonproject_audit(merged)
    return merged


def analyze_nonproject_audit(
    summary: dict[str, object],
    *,
    expected_top: str | None = None,
    expected_part: str | None = None,
) -> dict[str, object]:
    files = _dict_rows(summary.get("files"))
    constraints = _dict_rows(summary.get("constraints"))
    steps = _dict_rows(summary.get("steps"))
    part = str(summary.get("part") or "").strip()
    top = str(summary.get("top") or "").strip()
    stage = _nonproject_stage(summary)
    next_step = _next_step(stage)

    issues: list[dict[str, object]] = []
    if not files:
        issues.append(
            _issue(
                "nonproject.sources_missing",
                "high",
                "No RTL or HDL sources have been recorded for this Non-project session.",
                "Call vivado_nonproject_read_sources with RTL sources before synth_design.",
            )
        )
    if not part:
        issues.append(
            _issue(
                "nonproject.part_missing",
                "high",
                "No target part has been recorded.",
                "Pass part to vivado_nonproject_synth_design.",
            )
        )
    if not top:
        issues.append(
            _issue(
                "nonproject.top_missing",
                "high",
                "No top module/entity has been recorded.",
                "Pass top to vivado_nonproject_synth_design after confirming the source top.",
            )
        )
    if not constraints:
        issues.append(
            _issue(
                "nonproject.constraints_missing",
                "medium",
                "No XDC constraints have been recorded.",
                "Read timing and I/O constraints before relying on timing, DRC, or power reports.",
            )
        )
    for step in steps:
        if str(step.get("status") or "").lower() not in {"ok", "success", "succeeded"}:
            issues.append(
                _issue(
                    "nonproject.step_failed",
                    "high",
                    f"{step.get('name') or 'Non-project step'} did not complete successfully.",
                    "Inspect the command artifact, errorinfo, and any generated reports before running later steps.",
                    evidence=step,
                )
            )

    recommendations = _audit_recommendations(
        files=files,
        part=part,
        top=top,
        constraints=constraints,
        next_step=next_step,
        reports=_dict_rows(summary.get("reports")),
    )
    return {
        "ok": not any(issue["severity"] == "high" for issue in issues),
        "stage": stage,
        "next_step": next_step,
        "counts": {
            "files": len(files),
            "constraints": len(constraints),
            "steps": len(steps),
            "checkpoints": len(_dict_rows(summary.get("checkpoints"))),
            "reports": len(_dict_rows(summary.get("reports"))),
        },
        "part": part,
        "top": top,
        "expected_part": expected_part,
        "expected_top": expected_top,
        "issues": issues,
        "recommendations": recommendations,
        "recommended_docs": [
            {"doc_id": "UG892", "title": "Vivado Design Suite User Guide: Design Flows Overview"},
            {"doc_id": "UG894", "title": "Vivado Design Suite User Guide: Using Tcl Scripting"},
            {"doc_id": "UG901", "title": "Vivado Design Suite User Guide: Synthesis"},
            {"doc_id": "UG904", "title": "Vivado Design Suite User Guide: Implementation"},
            {"doc_id": "UG906", "title": "Vivado Design Suite User Guide: Design Analysis and Closure Techniques"},
        ],
    }


def nonproject_step_prerequisites(
    step: str,
    summary: dict[str, object],
    *,
    part: str | None = None,
    top: str | None = None,
) -> dict[str, object]:
    normalized = step.strip()
    if normalized not in NONPROJECT_STEPS:
        raise ValueError("Unsupported non-project step")

    files = _dict_rows(summary.get("files"))
    issues: list[dict[str, object]] = []
    if normalized == "synth_design":
        if not files:
            issues.append(
                _issue(
                    "nonproject.sources_missing",
                    "high",
                    "synth_design requires sources to be read first.",
                    "Call vivado_nonproject_read_sources before synthesis.",
                )
            )
        if not (part or summary.get("part")):
            issues.append(
                _issue("nonproject.part_missing", "high", "synth_design requires a target part.", "Pass part explicitly.")
            )
        if not (top or summary.get("top")):
            issues.append(_issue("nonproject.top_missing", "high", "synth_design requires a top.", "Pass top explicitly."))
    else:
        previous = NONPROJECT_STEPS[NONPROJECT_STEPS.index(normalized) - 1]
        if not _step_succeeded(summary, previous):
            issues.append(
                _issue(
                    "nonproject.previous_step_missing",
                    "high",
                    f"{normalized} normally requires a successful {previous} in this managed flow.",
                    f"Run vivado_nonproject_{previous.removesuffix('_design')}_design first or verify the active in-memory design.",
                    evidence={"required_previous_step": previous},
                )
            )

    return {
        "ok": not issues,
        "step": normalized,
        "issues": issues,
        "required_previous_step": None if normalized == "synth_design" else NONPROJECT_STEPS[NONPROJECT_STEPS.index(normalized) - 1],
        "recommendations": _step_recommendations(normalized, issues),
    }


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


def _dict_rows(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict)]


def _nonproject_stage(summary: dict[str, object]) -> str | None:
    last_step = None
    for step in _dict_rows(summary.get("steps")):
        if str(step.get("status") or "").lower() in {"ok", "success", "succeeded"}:
            name = str(step.get("name") or "").strip()
            if name in NONPROJECT_STEPS:
                last_step = name
    if last_step:
        return last_step
    if _dict_rows(summary.get("files")) or _dict_rows(summary.get("constraints")):
        return "read_sources"
    return None


def _next_step(stage: object) -> str | None:
    if not stage:
        return "read_sources"
    return NEXT_STEP_BY_STAGE.get(str(stage))


def _step_succeeded(summary: dict[str, object], step_name: str) -> bool:
    for step in _dict_rows(summary.get("steps")):
        if str(step.get("name") or "") != step_name:
            continue
        if str(step.get("status") or "").lower() in {"ok", "success", "succeeded"}:
            return True
    return False


def _issue(
    issue_id: str,
    severity: str,
    message: str,
    recommendation: str,
    *,
    evidence: dict[str, object] | None = None,
) -> dict[str, object]:
    issue: dict[str, object] = {
        "issue_id": issue_id,
        "severity": severity,
        "message": message,
        "recommendation": recommendation,
    }
    if evidence is not None:
        issue["evidence"] = evidence
    return issue


def _audit_recommendations(
    *,
    files: list[dict[str, object]],
    part: str,
    top: str,
    constraints: list[dict[str, object]],
    next_step: str | None,
    reports: list[dict[str, object]],
) -> list[dict[str, str]]:
    recommendations: list[dict[str, str]] = []
    if not files:
        recommendations.append(
            {"tool": "vivado_nonproject_read_sources", "why": "Read RTL/XDC inputs and record the source summary before synthesis."}
        )
    if files and (not part or not top):
        recommendations.append(
            {"tool": "vivado_nonproject_synth_design", "why": "Provide explicit part/top and run synthesis once inputs are loaded."}
        )
    if files and not constraints:
        recommendations.append(
            {"tool": "vivado_search_official_docs", "why": "Check UG903/UG949 guidance before proceeding without timing or I/O constraints."}
        )
    if next_step and next_step != "read_sources":
        recommendations.append(
            {"tool": _tool_for_step(next_step), "why": f"Continue the managed Non-project flow with {next_step}."}
        )
    if reports:
        recommendations.append({"tool": "vivado_analyze_reports", "why": "Parse generated reports before changing flow settings or rerunning."})
    return recommendations


def _step_recommendations(step: str, issues: list[dict[str, object]]) -> list[dict[str, str]]:
    if not issues:
        return [{"tool": _tool_for_step(step), "why": f"Prerequisites are satisfied for {step}."}]
    if any(issue["issue_id"] == "nonproject.sources_missing" for issue in issues):
        return [{"tool": "vivado_nonproject_read_sources", "why": "Read RTL/XDC sources before the requested step."}]
    previous_issue = next((issue for issue in issues if issue["issue_id"] == "nonproject.previous_step_missing"), None)
    if previous_issue:
        evidence = previous_issue.get("evidence") if isinstance(previous_issue.get("evidence"), dict) else {}
        previous = str(evidence.get("required_previous_step") or "")
        return [{"tool": _tool_for_step(previous), "why": f"Run the missing prerequisite step {previous} first."}]
    return [{"tool": "vivado_nonproject_audit", "why": "Inspect the current Non-project flow state before executing."}]


def _tool_for_step(step: str) -> str:
    tool_names = {
        "read_sources": "vivado_nonproject_read_sources",
        "synth_design": "vivado_nonproject_synth_design",
        "opt_design": "vivado_nonproject_opt_design",
        "place_design": "vivado_nonproject_place_design",
        "route_design": "vivado_nonproject_route_design",
    }
    return tool_names.get(step, "vivado_nonproject_audit")
