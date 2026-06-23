from __future__ import annotations

import re
from pathlib import Path


SEVERITY_ORDER = {"info": 0, "warning": 1, "critical_warning": 2, "error": 3, "fatal": 4}


def parse_simulation_launch(path: Path) -> dict[str, object]:
    detail: dict[str, object] = {
        "simset": "",
        "mode": "",
        "type": "",
        "scripts_only": False,
        "log_paths": [],
        "warnings": [],
    }
    for parts in _read_tsv(path):
        if not parts:
            continue
        key = parts[0]
        if key == "simulation":
            detail["simset"] = parts[1] if len(parts) > 1 else ""
            detail["mode"] = parts[2] if len(parts) > 2 else ""
            if len(parts) == 4 and _looks_bool(parts[3]):
                detail["type"] = ""
                detail["scripts_only"] = _bool(parts[3])
            else:
                detail["type"] = parts[3] if len(parts) > 3 else ""
                detail["scripts_only"] = _bool(parts[4] if len(parts) > 4 else "0")
        elif key == "log" and len(parts) >= 3:
            _list(detail, "log_paths").append({"kind": parts[1], "path": parts[2]})
        elif key == "warning" and len(parts) >= 2:
            _list(detail, "warnings").append(parts[1])
        elif key == "error" and len(parts) >= 2:
            detail["error"] = parts[1]
    return detail


def analyze_xsim_logs(paths: list[Path]) -> dict[str, object]:
    logs: list[dict[str, object]] = []
    aggregate: dict[str, int] = {"fatal": 0, "error": 0, "critical_warning": 0, "warning": 0, "info": 0}
    issues: list[dict[str, object]] = []
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        parsed = _analyze_one_log(path, text)
        logs.append(parsed)
        for key in aggregate:
            aggregate[key] += int(parsed.get("counts", {}).get(key, 0)) if isinstance(parsed.get("counts"), dict) else 0
        issues.extend(parsed["issues"] if isinstance(parsed.get("issues"), list) else [])

    worst = "info"
    for issue in issues:
        severity = str(issue.get("severity") or "info")
        if SEVERITY_ORDER.get(severity, 0) > SEVERITY_ORDER.get(worst, 0):
            worst = severity
    return {
        "ok": aggregate["fatal"] == 0 and aggregate["error"] == 0,
        "worst_severity": worst,
        "counts": aggregate,
        "logs": logs,
        "issues": issues,
        "suggested_next_tools": ["vivado_prepare_simulation", "vivado_launch_simulation", "vivado_search_official_docs"],
    }


def _analyze_one_log(path: Path, text: str) -> dict[str, object]:
    counts: dict[str, int] = {"fatal": 0, "error": 0, "critical_warning": 0, "warning": 0, "info": 0}
    issues: list[dict[str, object]] = []
    lines = text.splitlines()
    for index, line in enumerate(lines, start=1):
        severity = _line_severity(line)
        if severity is None:
            continue
        counts[severity] += 1
        if severity == "info":
            continue
        issue = {
            "severity": severity,
            "path": str(path),
            "line": index,
            "message": line.strip(),
            "category": _classify_message(line),
        }
        code = _message_code(line)
        if code:
            issue["code"] = code
        issues.append(issue)
    return {
        "path": str(path),
        "line_count": len(lines),
        "counts": counts,
        "issues": issues[:50],
    }


def _line_severity(line: str) -> str | None:
    lowered = line.lower()
    prefix = re.match(r"^\s*(?:#\s*)?(?:\*\*\s*)?(critical warning|fatal|error|warning|info)\s*:", lowered)
    if not prefix:
        return None
    label = prefix.group(1)
    if label == "fatal":
        return "fatal"
    if label == "critical warning":
        return "critical_warning"
    if label == "error":
        return "error"
    if label == "warning":
        return "warning"
    if label == "info":
        return "info"
    return None


def _classify_message(line: str) -> str:
    lowered = line.lower()
    if any(term in lowered for term in ("syntax error", "parse error", "near")):
        return "syntax"
    if any(term in lowered for term in ("timescale", "timeunit", "timeprecision")):
        return "timescale"
    if any(term in lowered for term in ("unresolved", "undefined", "unknown module", "module not found")) or re.search(
        r"\bmodule\b.*\bnot found\b", lowered
    ):
        return "unresolved_design_unit"
    if any(term in lowered for term in ("cannot find", "not found", "no such file", "cannot open")):
        return "missing_file_or_library"
    if any(term in lowered for term in ("elaborat", "xelab")):
        return "elaboration"
    if any(term in lowered for term in ("xvlog", "xvhdl", "compile")):
        return "compile"
    return "general"


def _message_code(line: str) -> str:
    match = re.search(r"\[([A-Za-z0-9_ -]+-[0-9]+)\]", line)
    return match.group(1).strip() if match else ""


def _read_tsv(path: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip():
            rows.append(line.split("\t"))
    return rows


def _bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _looks_bool(value: str) -> bool:
    return str(value).strip().lower() in {"0", "1", "true", "false", "yes", "no"}


def _list(container: dict[str, object], key: str) -> list[object]:
    value = container.setdefault(key, [])
    assert isinstance(value, list)
    return value
