from __future__ import annotations

from pathlib import Path


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
            summary["validation"] = {"code": int(code or "1"), "message": message}
    return summary


def _pad(values: list[str], count: int) -> list[str]:
    return [*values, *([""] * count)][:count]


def _split_endpoints(value: str) -> list[str]:
    return [item for item in value.split(",") if item]
