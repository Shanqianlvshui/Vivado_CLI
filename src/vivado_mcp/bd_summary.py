from __future__ import annotations

from pathlib import Path
import re


def parse_bd_summary(path: Path) -> dict[str, object]:
    summary: dict[str, object] = {
        "has_block_design": False,
        "current_bd_design": None,
        "block_designs": [],
        "cells": [],
        "ports": [],
        "interface_ports": [],
        "nets": [],
        "interface_nets": [],
        "validation": None,
    }
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        key, *values = line.split("\t")
        if key == "has_block_design":
            summary["has_block_design"] = values[:1] == ["1"]
        elif key == "current_bd_design":
            summary["current_bd_design"] = values[0] if values else None
        elif key == "block_design":
            summary["block_designs"].append(values[0] if values else "")
        elif key == "cell":
            name, cell_type, vlnv = _pad(values, 3)
            summary["cells"].append({"name": name, "type": cell_type, "vlnv": vlnv})
        elif key == "port":
            name, direction, port_type, left, right = _pad(values, 5)
            summary["ports"].append({"name": name, "direction": direction, "type": port_type, "left": left, "right": right})
        elif key == "interface_port":
            name, mode, vlnv = _pad(values, 3)
            summary["interface_ports"].append({"name": name, "mode": mode, "vlnv": vlnv})
        elif key == "net":
            name, endpoints = _pad(values, 2)
            summary["nets"].append({"name": name, "endpoints": _split_endpoints(endpoints)})
        elif key == "interface_net":
            name, endpoints = _pad(values, 2)
            summary["interface_nets"].append({"name": name, "endpoints": _split_endpoints(endpoints)})
        elif key == "validation":
            code, message = _pad(values, 2)
            validation = {"code": int(code or "1"), "message": message}
            validation.update(parse_bd_validate_result(message))
            summary["validation"] = validation
    return summary


def analyze_bd_audit(summary: dict[str, object]) -> dict[str, object]:
    issues: list[dict[str, object]] = []
    if not summary.get("has_block_design"):
        issues.append({"issue_id": "bd.not_open", "severity": "high"})
        return _audit_result(summary, issues)

    validation = summary.get("validation") if isinstance(summary.get("validation"), dict) else None
    if validation and int(validation.get("code") or 0) != 0:
        parsed_validation = parse_bd_validate_result(str(validation.get("message") or ""))
        issues.append(
            {
                "issue_id": "bd.validation_failed",
                "severity": "high",
                "message": str(validation.get("message") or ""),
            }
        )
        issues.extend(_list_dicts(validation.get("issues")) or _list_dicts(parsed_validation.get("issues")))

    for row in _list_dicts(summary.get("ports")):
        name = str(row.get("name") or "")
        if name and not _endpoint_connected(name, summary):
            issues.append({"issue_id": "bd.port_unconnected", "severity": "medium", "port": name})
    for row in _list_dicts(summary.get("interface_ports")):
        name = str(row.get("name") or "")
        if name and not _interface_endpoint_connected(name, summary):
            issues.append({"issue_id": "bd.interface_port_unconnected", "severity": "medium", "interface_port": name})
    for row in _list_dicts(summary.get("nets")):
        endpoints = row.get("endpoints") if isinstance(row.get("endpoints"), list) else []
        if len(endpoints) < 2:
            issues.append({"issue_id": "bd.net_has_single_endpoint", "severity": "medium", "net": row.get("name", "")})
    for row in _list_dicts(summary.get("interface_nets")):
        endpoints = row.get("endpoints") if isinstance(row.get("endpoints"), list) else []
        if len(endpoints) < 2:
            issues.append({"issue_id": "bd.interface_net_has_single_endpoint", "severity": "medium", "interface_net": row.get("name", "")})

    return _audit_result(summary, _dedupe_issues(issues))


def parse_bd_validate_result(text: str) -> dict[str, object]:
    issues: list[dict[str, object]] = []
    for index, line in enumerate(str(text or "").splitlines(), start=1):
        severity = _line_severity(line)
        if severity is None:
            continue
        issue = {
            "issue_id": _bd_issue_id(line),
            "severity": severity,
            "line": index,
            "message": line.strip(),
        }
        code = _message_code(line)
        if code:
            issue["code"] = code
        issues.append(issue)
    return {
        "ok": not any(issue["severity"] in {"high", "error", "fatal"} for issue in issues),
        "issue_count": len(issues),
        "issues": issues,
        "recommendations": _bd_recommendations(issues),
        "suggested_next_tools": ["vivado_bd_audit", "vivado_bd_apply", "vivado_bd_summary", "vivado_search_official_docs"],
    }


def _pad(values: list[str], count: int) -> list[str]:
    return [*values, *([""] * count)][:count]


def _split_endpoints(value: str) -> list[str]:
    return [item for item in value.split(",") if item]


def _audit_result(summary: dict[str, object], issues: list[dict[str, object]]) -> dict[str, object]:
    return {
        "ok": not issues,
        "current_bd_design": summary.get("current_bd_design"),
        "issue_count": len(issues),
        "issues": issues,
        "recommendations": _bd_recommendations(issues),
        "suggested_next_tools": ["vivado_bd_validate", "vivado_bd_apply", "vivado_bd_summary", "vivado_bd_generate"],
    }


def _line_severity(line: str) -> str | None:
    lowered = line.lower()
    if "error:" in lowered or "critical warning:" in lowered:
        return "high"
    if "warning:" in lowered:
        return "medium"
    return None


def _bd_issue_id(line: str) -> str:
    lowered = line.lower()
    if any(term in lowered for term in ("address", "addrseg", "segment")) and any(
        term in lowered for term in ("assign", "unassigned", "not assigned", "mapped")
    ):
        return "bd.address_unassigned"
    if any(term in lowered for term in ("clock", "clk", "reset", "rst")) and any(
        term in lowered for term in ("not connected", "missing", "unconnected")
    ):
        return "bd.clock_reset_missing"
    if any(term in lowered for term in ("not connected", "unconnected", "no driver", "no load")):
        return "bd.connection_missing"
    if "automation" in lowered:
        return "bd.automation_issue"
    return "bd.validation_issue"


def _message_code(line: str) -> str:
    match = re.search(r"\[([A-Za-z]+ [0-9]+-[0-9]+)\]", line)
    return match.group(1).strip() if match else ""


def _endpoint_connected(name: str, summary: dict[str, object]) -> bool:
    return any(name in row.get("endpoints", []) for row in _list_dicts(summary.get("nets")))


def _interface_endpoint_connected(name: str, summary: dict[str, object]) -> bool:
    return any(name in row.get("endpoints", []) for row in _list_dicts(summary.get("interface_nets")))


def _list_dicts(value: object) -> list[dict[str, object]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _dedupe_issues(issues: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for issue in issues:
        key = (str(issue.get("issue_id") or ""), str(issue.get("message") or issue.get("port") or issue.get("net") or issue.get("interface_port") or ""))
        if key in seen:
            continue
        seen.add(key)
        rows.append(issue)
    return rows


def _bd_recommendations(issues: list[dict[str, object]]) -> list[dict[str, str]]:
    if not issues:
        return [{"tool": "vivado_bd_summary", "why": "No block-design audit issues were detected; refresh summary after changes."}]
    recommendations: list[dict[str, str]] = []

    def add(tool: str, why: str) -> None:
        if not any(row["tool"] == tool for row in recommendations):
            recommendations.append({"tool": tool, "why": why})

    issue_ids = {str(issue.get("issue_id") or "") for issue in issues}
    add("vivado_bd_validate", "Run structured BD validation and inspect parsed BD 41-* diagnostics.")
    if {"bd.connection_missing", "bd.port_unconnected", "bd.interface_port_unconnected", "bd.net_has_single_endpoint", "bd.interface_net_has_single_endpoint"} & issue_ids:
        add("vivado_bd_apply", "Connect missing pins/interfaces or apply BD automation through a structured action plan.")
    if {"bd.address_unassigned"} & issue_ids:
        add("vivado_bd_apply", "Use assign_address or address-related BD automation after confirming address map intent.")
    if {"bd.clock_reset_missing"} & issue_ids:
        add("vivado_search_official_docs", "Review UG994/UG835 clock and reset connection guidance before applying automation.")
    add("vivado_bd_summary", "Refresh cells, ports, nets, interfaces, and validation state after changes.")
    return recommendations
