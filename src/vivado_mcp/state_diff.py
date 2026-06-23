from __future__ import annotations

import hashlib
import json
from typing import Any


State = dict[str, Any]


def state_digest(state: State) -> str:
    """Return a stable digest for a captured Vivado state payload."""
    normalized = _normalize(_digest_payload(state))
    body = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def diff_states(before: State, after: State) -> dict[str, Any]:
    """Compare two captured Vivado state payloads.

    The diff is intentionally shallow and keyed by the stable identifiers that
    matter most when recovering a long Vivado task: file paths, fileset names,
    run names, IP names, constraint path/order, and BD object names.
    """
    diff: dict[str, Any] = {
        "version": 2,
        "changed": False,
        "before_digest": state_digest(before),
        "after_digest": state_digest(after),
        "project": {
            "properties": _dict_diff(_project_properties(before), _project_properties(after)),
            "files": _list_dict_diff(_project_list(before, "files"), _project_list(after, "files"), "path"),
            "runs": _list_dict_diff(_project_list(before, "runs"), _project_list(after, "runs"), "name"),
            "ips": _list_scalar_diff(_project_list(before, "ips"), _project_list(after, "ips")),
            "block_designs": _list_scalar_diff(_project_list(before, "block_designs"), _project_list(after, "block_designs")),
        },
        "filesets": {
            "filesets": _list_dict_diff(_fileset_list(before), _fileset_list(after), "name"),
        },
        "runs": {
            "runs": _list_dict_diff(_project_list(before, "runs"), _project_list(after, "runs"), "name"),
        },
        "ip": {
            "ips": _list_dict_diff(_ip_list(before), _ip_list(after), "name"),
        },
        "constraints": {
            "constraint_files": _list_dict_diff(_constraint_files(before), _constraint_files(after), "path"),
            "constrs_filesets": _list_dict_diff(_constraint_filesets(before), _constraint_filesets(after), "name"),
            "xdc_markers": _dict_diff(_constraint_markers(before), _constraint_markers(after)),
            "warnings": _list_scalar_diff(_constraint_warnings(before), _constraint_warnings(after)),
        },
        "block_design": {
            "properties": _dict_diff(_bd_properties(before), _bd_properties(after)),
            "block_designs": _list_scalar_diff(_bd_list(before, "block_designs"), _bd_list(after, "block_designs")),
            "cells": _list_dict_diff(_bd_list(before, "cells"), _bd_list(after, "cells"), "name"),
            "ports": _list_dict_diff(_bd_list(before, "ports"), _bd_list(after, "ports"), "name"),
            "interface_ports": _list_dict_diff(_bd_list(before, "interface_ports"), _bd_list(after, "interface_ports"), "name"),
            "nets": _list_dict_diff(_bd_list(before, "nets"), _bd_list(after, "nets"), "name"),
            "interface_nets": _list_dict_diff(_bd_list(before, "interface_nets"), _bd_list(after, "interface_nets"), "name"),
        },
        "reports": {
            "artifacts": _list_dict_diff(_report_artifacts(before), _report_artifacts(after), "artifact_id"),
        },
        "hardware": {
            "servers": _list_dict_diff(_hardware_list(before, "servers"), _hardware_list(after, "servers"), "url"),
            "targets": _list_dict_diff(_hardware_list(before, "targets"), _hardware_list(after, "targets"), "name"),
            "devices": _list_dict_diff(_hardware_list(before, "devices"), _hardware_list(after, "devices"), "name"),
        },
    }
    diff["changed"] = diff["before_digest"] != diff["after_digest"]
    diff["changes"] = _flatten_changes(diff)
    diff["summary"] = _summary(diff)
    diff["recommendations"] = _recommendations(diff["changes"])
    return diff


def _project_properties(state: State) -> dict[str, Any]:
    project = _mapping(state.get("project"))
    return {key: project.get(key) for key in ("has_project", "current_project", "project_file", "part", "board_part", "top") if key in project}


def _project_list(state: State, key: str) -> list[Any]:
    return _list(_mapping(state.get("project")).get(key))


def _fileset_list(state: State) -> list[dict[str, Any]]:
    return _list_dicts(_mapping(state.get("filesets")).get("filesets"))


def _ip_list(state: State) -> list[dict[str, Any]]:
    ip_state = _mapping(state.get("ip"))
    rows = _list_dicts(ip_state.get("ips"))
    if rows:
        return rows
    return [{"name": str(name)} for name in _project_list(state, "ips")]


def _constraint_files(state: State) -> list[dict[str, Any]]:
    return _list_dicts(_mapping(state.get("constraints")).get("constraint_files"))


def _constraint_filesets(state: State) -> list[dict[str, Any]]:
    return _list_dicts(_mapping(state.get("constraints")).get("constrs_filesets"))


def _constraint_markers(state: State) -> dict[str, Any]:
    return _mapping(_mapping(state.get("constraints")).get("xdc_markers"))


def _constraint_warnings(state: State) -> list[Any]:
    return _list(_mapping(state.get("constraints")).get("warnings"))


def _bd_properties(state: State) -> dict[str, Any]:
    bd = _mapping(state.get("block_design"))
    return {key: bd.get(key) for key in ("has_block_design", "current_bd_design", "validation") if key in bd}


def _bd_list(state: State, key: str) -> list[Any]:
    return _list(_mapping(state.get("block_design")).get(key))


def _report_artifacts(state: State) -> list[dict[str, Any]]:
    return _list_dicts(_mapping(state.get("reports")).get("artifacts"))


def _hardware_list(state: State, key: str) -> list[dict[str, Any]]:
    return _list_dicts(_mapping(state.get("hardware")).get(key))


def _dict_diff(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    added = {key: after[key] for key in sorted(after.keys() - before.keys())}
    removed = {key: before[key] for key in sorted(before.keys() - after.keys())}
    changed = [
        {"key": key, "before": before[key], "after": after[key]}
        for key in sorted(before.keys() & after.keys())
        if _normalize(before[key]) != _normalize(after[key])
    ]
    return {"added": added, "removed": removed, "changed": changed}


def _list_scalar_diff(before: list[Any], after: list[Any]) -> dict[str, Any]:
    before_map = {json.dumps(_normalize(item), sort_keys=True): item for item in before}
    after_map = {json.dumps(_normalize(item), sort_keys=True): item for item in after}
    added = [after_map[key] for key in sorted(after_map.keys() - before_map.keys())]
    removed = [before_map[key] for key in sorted(before_map.keys() - after_map.keys())]
    return {"added": added, "removed": removed}


def _list_dict_diff(before: list[dict[str, Any]], after: list[dict[str, Any]], key_field: str) -> dict[str, Any]:
    before_map = _keyed_dicts(before, key_field)
    after_map = _keyed_dicts(after, key_field)
    added = [after_map[key] for key in sorted(after_map.keys() - before_map.keys())]
    removed = [before_map[key] for key in sorted(before_map.keys() - after_map.keys())]
    changed = [
        {"key": key, "before": before_map[key], "after": after_map[key]}
        for key in sorted(before_map.keys() & after_map.keys())
        if _normalize(before_map[key]) != _normalize(after_map[key])
    ]
    return {"added": added, "removed": removed, "changed": changed}


def _flatten_changes(diff: dict[str, Any]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    domains = ["project", "filesets", "runs", "ip", "constraints", "block_design", "reports", "hardware"]
    for domain in domains:
        sections = diff.get(domain)
        if not isinstance(sections, dict):
            continue
        for section, section_diff in sections.items():
            if domain == "project" and section in {"runs", "ips"}:
                continue
            if not isinstance(section_diff, dict):
                continue
            for kind in ("added", "removed", "changed"):
                items = section_diff.get(kind)
                if not items:
                    continue
                if isinstance(items, dict):
                    iterable = [{"key": key, "value": value} for key, value in items.items()]
                elif isinstance(items, list):
                    iterable = items
                else:
                    iterable = [items]
                for item in iterable:
                    changes.append(
                        {
                            "domain": _change_domain(domain, section),
                            "section": section,
                            "kind": kind,
                            "key": _change_key(item),
                            "item": item,
                            "explain": _explain_change(domain, section, kind, item),
                        }
                    )
    return changes


def _summary(diff: dict[str, Any]) -> dict[str, Any]:
    changes = diff.get("changes") if isinstance(diff.get("changes"), list) else []
    changed_domains: list[str] = []
    for change in changes:
        if isinstance(change, dict):
            domain = str(change.get("domain") or "")
            if domain and domain not in changed_domains:
                changed_domains.append(domain)
    return {
        "change_count": len(changes),
        "changed_domains": changed_domains,
        "added_count": sum(1 for change in changes if isinstance(change, dict) and change.get("kind") == "added"),
        "removed_count": sum(1 for change in changes if isinstance(change, dict) and change.get("kind") == "removed"),
        "changed_count": sum(1 for change in changes if isinstance(change, dict) and change.get("kind") == "changed"),
    }


def _recommendations(changes: list[dict[str, Any]]) -> list[dict[str, str]]:
    recommendations: list[dict[str, str]] = []

    def add(tool: str, why: str) -> None:
        if not any(row["tool"] == tool for row in recommendations):
            recommendations.append({"tool": tool, "why": why})

    for change in changes:
        domain = str(change.get("domain") or "")
        section = str(change.get("section") or "")
        item = change.get("item")
        text = json.dumps(_normalize(item), sort_keys=True, ensure_ascii=True).lower()
        if domain == "filesets" or "top" in text:
            add("vivado_source_audit", "Project fileset or top-related state changed; audit sources and active filesets.")
        if domain == "constraints":
            add("vivado_xdc_order_check", "Constraint files, XDC markers, or constraint warnings changed; verify XDC order and scope.")
        if domain == "ip":
            add("vivado_describe_ip", "IP lock, upgrade, generation, or XCI state changed; inspect affected IP details.")
        if domain == "runs" or (section == "runs" and any(word in text for word in ("fail", "error", "complete"))):
            add("vivado_analyze_reports", "Run state changed; inspect timing, utilization, DRC, power, and methodology reports.")
        if domain == "reports":
            add("vivado_analyze_reports", "Report artifacts changed; refresh aggregate report diagnostics.")
        if domain == "block_design":
            add("vivado_bd_summary", "Block design objects changed; refresh BD summary or validation state.")
        if domain == "hardware":
            add("vivado_hw_discover", "Hardware discovery state changed; refresh read-only target/device discovery if needed.")
    return recommendations


def _change_domain(domain: str, section: str) -> str:
    if domain == "project" and section == "runs":
        return "runs"
    if domain == "project" and section == "ips":
        return "ip"
    return domain


def _change_key(item: Any) -> str:
    if isinstance(item, dict):
        for key in ("key", "name", "path", "artifact_id", "url"):
            value = item.get(key)
            if value not in (None, ""):
                return str(value)
    return ""


def _explain_change(domain: str, section: str, kind: str, item: Any) -> str:
    key = _change_key(item)
    target = f" {key}" if key else ""
    labels = {
        "properties": "project property",
        "files": "project file",
        "runs": "run",
        "ips": "IP",
        "filesets": "fileset",
        "constraint_files": "constraint file",
        "constrs_filesets": "constraint fileset",
        "xdc_markers": "XDC marker count",
        "warnings": "constraint warning",
        "cells": "BD cell",
        "ports": "BD port",
        "interface_ports": "BD interface port",
        "nets": "BD net",
        "interface_nets": "BD interface net",
        "artifacts": "report artifact",
        "servers": "hardware server",
        "targets": "hardware target",
        "devices": "hardware device",
    }
    label = labels.get(section, section.replace("_", " "))
    verb = {"added": "added", "removed": "removed", "changed": "changed"}.get(kind, kind)
    return f"{label}{target} {verb}."


def _keyed_dicts(rows: list[dict[str, Any]], key_field: str) -> dict[str, dict[str, Any]]:
    keyed: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        key = str(row.get(key_field) or f"__index_{index}")
        if key in keyed:
            key = f"{key}#{index}"
        keyed[key] = row
    return keyed


def _normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _normalize(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        normalized_items = [_normalize(item) for item in value]
        return sorted(normalized_items, key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=True))
    return value


def _digest_payload(state: State) -> State:
    return {key: value for key, value in state.items() if key != "snapshot"}


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _list_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in _list(value) if isinstance(item, dict)]
