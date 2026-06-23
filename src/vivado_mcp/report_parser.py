from __future__ import annotations

import re


def parse_report(report_type: str, text: str) -> dict[str, object]:
    if report_type in {"timing_summary", "timing_paths"}:
        return parse_timing(text)
    if report_type == "utilization":
        return parse_utilization(text)
    if report_type in {"drc", "methodology", "messages"}:
        return parse_messages(text, report_type=report_type)
    if report_type == "power":
        return parse_power(text)
    return {"report_type": report_type, "parsed": False}


def parse_timing(text: str) -> dict[str, object]:
    values: dict[str, float] = {}
    for key in ["WNS", "TNS", "WHS", "THS", "WPWS", "TPWS"]:
        match = re.search(rf"\b{key}\b\s*(?:\([^)]+\))?\s*[:=]?\s*(-?\d+(?:\.\d+)?)", text, re.IGNORECASE)
        if match:
            values[key.lower()] = float(match.group(1))
    ints: dict[str, int] = {}
    for label, field in (
        ("Failing Endpoints", "failing_endpoints"),
        ("Total Endpoints", "total_endpoints"),
        ("Timing Errors", "timing_errors"),
    ):
        match = re.search(rf"\b{re.escape(label)}\b\s*[:=]?\s*([0-9,]+)", text, re.IGNORECASE)
        if match:
            ints[field] = int(match.group(1).replace(",", ""))
    status = "unknown"
    if "wns" in values:
        status = "pass" if values["wns"] >= 0 else "fail"
    return {"report_type": "timing", "parsed": bool(values or ints), "status": status, **values, **ints}


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


def parse_messages(text: str, report_type: str = "messages") -> dict[str, object]:
    rules: dict[str, dict[str, int]] = {}
    for severity, field in (
        ("ERROR", "errors"),
        ("CRITICAL WARNING", "critical_warnings"),
        ("WARNING", "warnings"),
    ):
        pattern = r"(?<!CRITICAL )\bWARNING:\s*\[([^\]]+)\]" if severity == "WARNING" else rf"\b{re.escape(severity)}:\s*\[([^\]]+)\]"
        for match in re.finditer(pattern, text):
            rule = match.group(1).strip()
            row = rules.setdefault(rule, {"errors": 0, "critical_warnings": 0, "warnings": 0})
            row[field] += 1
    return {
        "report_type": report_type,
        "parsed": True,
        "errors": len(re.findall(r"\bERROR:\s*\[", text)),
        "critical_warnings": len(re.findall(r"\bCRITICAL WARNING:\s*\[", text)),
        "warnings": len(re.findall(r"(?<!CRITICAL )\bWARNING:\s*\[", text)),
        "rules": rules,
    }


def parse_power(text: str) -> dict[str, object]:
    fields: dict[str, float] = {}
    patterns = {
        "total_on_chip_power_w": r"Total\s+(?:On-Chip\s+)?Power\s*(?:\(W\))?\s*[:=]?\s*(-?\d+(?:\.\d+)?)",
        "dynamic_power_w": r"Dynamic(?:\s+Power)?\s*(?:\(W\))?\s*[:=]?\s*(-?\d+(?:\.\d+)?)",
        "static_power_w": r"(?:Device\s+)?Static(?:\s+Power)?\s*(?:\(W\))?\s*[:=]?\s*(-?\d+(?:\.\d+)?)",
    }
    for field, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            fields[field] = float(match.group(1))
    return {"report_type": "power", "parsed": bool(fields), **fields}


def analyze_report_summaries(summaries: dict[str, dict[str, object]]) -> dict[str, object]:
    issues: list[dict[str, object]] = []
    for report_type, summary in summaries.items():
        if not summary or summary.get("parsed") is False:
            issues.append(
                {
                    "issue_id": "report.unparsed",
                    "severity": "low",
                    "report_type": report_type,
                    "evidence": "Report parser did not find a known summary structure.",
                    "next_step": "Read the report artifact or run a more specific Vivado report.",
                    "official_doc_topic": "reports",
                }
            )
            continue
        if summary.get("report_type") == "timing":
            issues.extend(_analyze_timing(report_type, summary))
        elif summary.get("report_type") == "utilization":
            issues.extend(_analyze_utilization(report_type, summary))
        elif summary.get("report_type") in {"drc", "methodology", "messages"}:
            issues.extend(_analyze_messages(report_type, summary))
        elif summary.get("report_type") == "power":
            issues.extend(_analyze_power(report_type, summary))

    severity_rank = {"high": 0, "medium": 1, "low": 2}
    priority_rank = {
        "drc.error": 0,
        "report.error": 0,
        "timing.setup_failed": 1,
        "timing.hold_failed": 1,
        "utilization.high": 2,
        "power.high_total": 3,
    }
    issues.sort(
        key=lambda issue: (
            severity_rank.get(str(issue.get("severity")), 99),
            priority_rank.get(str(issue.get("issue_id")), 50),
            str(issue.get("issue_id")),
        )
    )
    return {
        "ok": not any(issue.get("severity") == "high" for issue in issues),
        "summary": {
            "report_count": len(summaries),
            "issue_count": len(issues),
            "high_count": sum(1 for issue in issues if issue.get("severity") == "high"),
            "medium_count": sum(1 for issue in issues if issue.get("severity") == "medium"),
            "low_count": sum(1 for issue in issues if issue.get("severity") == "low"),
        },
        "issues": issues,
        "suggested_next_tools": ["vivado_report", "vivado_search_official_docs", "vivado_tcl_command_help"],
        "official_references": _official_references_for_issues(issues),
    }


def _analyze_timing(report_type: str, summary: dict[str, object]) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    wns = _float_value(summary.get("wns"))
    tns = _float_value(summary.get("tns"))
    whs = _float_value(summary.get("whs"))
    ths = _float_value(summary.get("ths"))
    failing = _int_value(summary.get("failing_endpoints"))
    if wns is not None and wns < 0:
        issues.append(
            {
                "issue_id": "timing.setup_failed",
                "severity": "high",
                "report_type": report_type,
                "evidence": f"WNS={wns} ns, TNS={tns if tns is not None else 'unknown'}, failing_endpoints={failing if failing is not None else 'unknown'}",
                "next_step": "Run timing paths and inspect the worst setup paths before changing constraints or implementation strategy.",
                "official_doc_topic": "timing",
                "official_references": ["UG906", "UG949", "UG1292"],
            }
        )
    if whs is not None and whs < 0:
        issues.append(
            {
                "issue_id": "timing.hold_failed",
                "severity": "high",
                "report_type": report_type,
                "evidence": f"WHS={whs} ns, THS={ths if ths is not None else 'unknown'}",
                "next_step": "Inspect hold timing paths and confirm clocks/IO delays before rerunning implementation.",
                "official_doc_topic": "timing",
                "official_references": ["UG906", "UG949"],
            }
        )
    if summary.get("status") == "pass":
        issues.append(
            {
                "issue_id": "timing.pass",
                "severity": "low",
                "report_type": report_type,
                "evidence": f"WNS={wns} ns",
                "next_step": "Continue with utilization, DRC, power, and methodology checks.",
                "official_doc_topic": "reports",
                "official_references": ["UG906"],
            }
        )
    return issues


def _analyze_utilization(report_type: str, summary: dict[str, object]) -> list[dict[str, object]]:
    resources = summary.get("resources")
    if not isinstance(resources, dict):
        return []
    issues: list[dict[str, object]] = []
    for name, row in resources.items():
        if not isinstance(row, dict):
            continue
        pct = _float_value(row.get("utilization_percent"))
        if pct is None:
            continue
        severity = "high" if pct >= 95 else "medium" if pct >= 80 else None
        if severity:
            issues.append(
                {
                    "issue_id": "utilization.high",
                    "severity": severity,
                    "report_type": report_type,
                    "resource": name,
                    "evidence": f"{name} utilization is {pct}%",
                    "next_step": "Inspect hierarchical utilization and consider resource sharing, retiming, or device/strategy changes.",
                    "official_doc_topic": "reports",
                    "official_references": ["UG906", "UG949"],
                }
            )
    return issues


def _analyze_messages(report_type: str, summary: dict[str, object]) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    errors = _int_value(summary.get("errors")) or 0
    critical = _int_value(summary.get("critical_warnings")) or 0
    if errors:
        issues.append(
            {
                "issue_id": "drc.error" if report_type == "drc" else "report.error",
                "severity": "high",
                "report_type": report_type,
                "evidence": f"{errors} errors reported",
                "rules": _top_rules(summary, "errors"),
                "next_step": "Fix error rules before rerunning implementation or timing closure.",
                "official_doc_topic": "reports",
                "official_references": ["UG906", "UG949"],
            }
        )
    if critical:
        issues.append(
            {
                "issue_id": "methodology.critical_warning" if report_type == "methodology" else "report.critical_warning",
                "severity": "medium",
                "report_type": report_type,
                "evidence": f"{critical} critical warnings reported",
                "rules": _top_rules(summary, "critical_warnings"),
                "next_step": "Group warnings by rule ID and resolve methodology or constraint issues before closure attempts.",
                "official_doc_topic": "methodology",
                "official_references": ["UG906", "UG949", "UG1292"],
            }
        )
    return issues


def _analyze_power(report_type: str, summary: dict[str, object]) -> list[dict[str, object]]:
    total = _float_value(summary.get("total_on_chip_power_w"))
    dynamic = _float_value(summary.get("dynamic_power_w"))
    if total is None:
        return []
    severity = "high" if total >= 7.0 else "medium" if total >= 5.0 else None
    if not severity:
        return []
    return [
        {
            "issue_id": "power.high_total",
            "severity": severity,
            "report_type": report_type,
            "evidence": f"Total on-chip power is {total} W" + (f", dynamic={dynamic} W" if dynamic is not None else ""),
            "next_step": "Check activity assumptions and run power optimization or hierarchical power analysis.",
            "official_doc_topic": "power",
            "official_references": ["UG907", "UG906"],
        }
    ]


def _top_rules(summary: dict[str, object], field: str) -> list[dict[str, object]]:
    rules = summary.get("rules")
    if not isinstance(rules, dict):
        return []
    rows = []
    for rule, counts in rules.items():
        if isinstance(counts, dict) and _int_value(counts.get(field)):
            rows.append({"rule": rule, "count": _int_value(counts.get(field)) or 0})
    rows.sort(key=lambda row: row["count"], reverse=True)
    return rows[:5]


def _official_references_for_issues(issues: list[dict[str, object]]) -> list[str]:
    docs: list[str] = []
    for issue in issues:
        refs = issue.get("official_references")
        if isinstance(refs, list):
            for ref in refs:
                if isinstance(ref, str) and ref not in docs:
                    docs.append(ref)
    return docs


def _float_value(value: object) -> float | None:
    return float(value) if isinstance(value, int | float) else None


def _int_value(value: object) -> int | None:
    return int(value) if isinstance(value, int | float) else None
