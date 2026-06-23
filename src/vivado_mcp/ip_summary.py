from __future__ import annotations

from pathlib import Path


def parse_ip_catalog(path: Path) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for parts in _read_tsv(path):
        if not parts or parts[0] != "catalog_ip":
            continue
        rows.append(
            {
                "vlnv": parts[1] if len(parts) > 1 else "",
                "name": parts[2] if len(parts) > 2 else "",
                "display_name": parts[3] if len(parts) > 3 else "",
                "version": parts[4] if len(parts) > 4 else "",
                "vendor": parts[5] if len(parts) > 5 else "",
                "library": parts[6] if len(parts) > 6 else "",
                "taxonomy": parts[7] if len(parts) > 7 else "",
                "supported": _bool(parts[8] if len(parts) > 8 else "1"),
            }
        )
    return {"ips": rows, "count": len(rows)}


def parse_ip_list(path: Path) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    has_project = False
    current_project = ""
    for parts in _read_tsv(path):
        if not parts:
            continue
        key = parts[0]
        if key == "has_project":
            has_project = parts[1:2] == ["1"]
        elif key == "current_project":
            current_project = parts[1] if len(parts) > 1 else ""
        elif key == "ip":
            rows.append(_ip_row(parts))
    return {"has_project": has_project, "current_project": current_project, "ips": rows, "count": len(rows)}


def parse_ip_detail(path: Path) -> dict[str, object]:
    detail: dict[str, object] = {"name": "", "properties": {}, "targets": []}
    for parts in _read_tsv(path):
        if not parts:
            continue
        key = parts[0]
        if key == "ip":
            detail.update(_ip_row(parts))
        elif key == "property" and len(parts) >= 3:
            props = detail.setdefault("properties", {})
            assert isinstance(props, dict)
            props[parts[1]] = parts[2]
        elif key == "target" and len(parts) >= 2:
            targets = detail.setdefault("targets", [])
            assert isinstance(targets, list)
            targets.append(parts[1])
        elif key == "error" and len(parts) >= 2:
            detail["error"] = parts[1]
    return detail


def _ip_row(parts: list[str]) -> dict[str, object]:
    return {
        "name": parts[1] if len(parts) > 1 else "",
        "vlnv": parts[2] if len(parts) > 2 else "",
        "xci_path": parts[3] if len(parts) > 3 else "",
        "locked": _bool(parts[4] if len(parts) > 4 else "0"),
        "upgrade_available": _bool(parts[5] if len(parts) > 5 else "0"),
        "generated": _bool(parts[6] if len(parts) > 6 else "0"),
        "synthesis_status": parts[7] if len(parts) > 7 else "",
    }


def _read_tsv(path: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip():
            rows.append(line.split("\t"))
    return rows


def _bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}
