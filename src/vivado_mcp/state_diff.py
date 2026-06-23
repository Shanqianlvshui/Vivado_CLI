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
    }
    diff["changed"] = diff["before_digest"] != diff["after_digest"]
    return diff


def _project_properties(state: State) -> dict[str, Any]:
    project = _mapping(state.get("project"))
    return {key: project.get(key) for key in ("has_project", "current_project", "project_file", "part", "board_part", "top") if key in project}


def _project_list(state: State, key: str) -> list[Any]:
    return _list(_mapping(state.get("project")).get(key))


def _fileset_list(state: State) -> list[dict[str, Any]]:
    return _list_dicts(_mapping(state.get("filesets")).get("filesets"))


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
