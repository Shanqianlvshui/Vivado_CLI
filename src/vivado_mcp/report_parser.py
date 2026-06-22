from __future__ import annotations

import re


def parse_report(report_type: str, text: str) -> dict[str, object]:
    if report_type in {"timing_summary", "timing_paths"}:
        return parse_timing(text)
    if report_type == "utilization":
        return parse_utilization(text)
    if report_type in {"drc", "messages"}:
        return parse_messages(text)
    return {"report_type": report_type, "parsed": False}


def parse_timing(text: str) -> dict[str, object]:
    values: dict[str, float] = {}
    for key in ["WNS", "TNS", "WHS", "THS", "WPWS", "TPWS"]:
        match = re.search(rf"\b{key}\b\s*(?:\([^)]+\))?\s*[:=]?\s*(-?\d+(?:\.\d+)?)", text, re.IGNORECASE)
        if match:
            values[key.lower()] = float(match.group(1))
    status = "unknown"
    if "wns" in values:
        status = "pass" if values["wns"] >= 0 else "fail"
    return {"report_type": "timing", "parsed": bool(values), "status": status, **values}


def parse_utilization(text: str) -> dict[str, object]:
    resources: dict[str, dict[str, int | float]] = {}
    for resource in ["CLB LUTs", "LUT", "CLB Registers", "FF", "Block RAM Tile", "DSPs", "URAM"]:
        pattern = rf"\|\s*{re.escape(resource)}\s*\|\s*([0-9,]+)\s*\|\s*([0-9,]+)\s*\|\s*([0-9.]+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            used = int(match.group(1).replace(",", ""))
            available = int(match.group(2).replace(",", ""))
            utilization = float(match.group(3))
            resources[resource.lower().replace(" ", "_")] = {
                "used": used,
                "available": available,
                "utilization_percent": utilization,
            }
    return {"report_type": "utilization", "parsed": bool(resources), "resources": resources}


def parse_messages(text: str) -> dict[str, object]:
    return {
        "report_type": "messages",
        "parsed": True,
        "errors": len(re.findall(r"\bERROR:\s*\[", text)),
        "critical_warnings": len(re.findall(r"\bCRITICAL WARNING:\s*\[", text)),
        "warnings": len(re.findall(r"(?<!CRITICAL )\bWARNING:\s*\[", text)),
    }
