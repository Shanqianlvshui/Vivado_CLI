from __future__ import annotations

import csv
import math
import re
from pathlib import Path
from typing import Any

MAX_DFT_SAMPLES = 4096
DEFAULT_SPI_STATUS_LAYOUT: dict[str, object] = {
    "data_bits": [7, 0],
    "addr_bits": [22, 8],
    "target_bits": [24, 23],
    "busy_bit": 25,
    "done_bit": 26,
    "enable_bit": 27,
    "error_bit": 28,
}


def parse_hardware_summary(path: Path) -> dict[str, object]:
    summary: dict[str, object] = {
        "servers": [],
        "targets": [],
        "devices": [],
        "properties": [],
        "warnings": [],
    }
    for parts in _read_tsv(path):
        if not parts:
            continue
        key = parts[0]
        if key == "server":
            _list(summary, "servers").append(
                {
                    "url": parts[1] if len(parts) > 1 else "",
                    "status": parts[2] if len(parts) > 2 else "",
                }
            )
        elif key == "target":
            _list(summary, "targets").append(
                {
                    "name": parts[1] if len(parts) > 1 else "",
                    "status": parts[2] if len(parts) > 2 else "",
                }
            )
        elif key == "device":
            _list(summary, "devices").append(
                {
                    "name": parts[1] if len(parts) > 1 else "",
                    "part": parts[2] if len(parts) > 2 else "",
                    "dna": parts[3] if len(parts) > 3 else "",
                    "programmed": _bool(parts[4] if len(parts) > 4 else "0"),
                    "status": parts[5] if len(parts) > 5 else "",
                }
            )
        elif key == "property":
            _list(summary, "properties").append(
                {
                    "object": parts[1] if len(parts) > 1 else "",
                    "name": parts[2] if len(parts) > 2 else "",
                    "value": parts[3] if len(parts) > 3 else "",
                }
            )
        elif key == "warning" and len(parts) >= 2:
            _list(summary, "warnings").append(parts[1])
        elif key == "error" and len(parts) >= 2:
            summary["error"] = parts[1]
    summary["server_count"] = len(summary["servers"]) if isinstance(summary["servers"], list) else 0
    summary["target_count"] = len(summary["targets"]) if isinstance(summary["targets"], list) else 0
    summary["device_count"] = len(summary["devices"]) if isinstance(summary["devices"], list) else 0
    return summary


def parse_debug_cores_tsv(path: Path) -> dict[str, object]:
    summary: dict[str, object] = {
        "path": str(path),
        "cores": [],
        "ilas": [],
        "vios": [],
        "probes": [],
        "warnings": [],
        "errors": [],
    }
    cores_by_key: dict[tuple[str, str], dict[str, object]] = {}
    for parts in _read_tsv(path):
        if not parts:
            continue
        key = parts[0]
        if key == "core":
            core = _parse_debug_core_row(parts)
            core_key = (str(core["type"]), str(core["name"]))
            cores_by_key[core_key] = core
            _list(summary, "cores").append(core)
            if core["type"] == "ila":
                _list(summary, "ilas").append(core)
            elif core["type"] == "vio":
                _list(summary, "vios").append(core)
        elif key == "probe":
            probe = _parse_debug_probe_row(parts)
            _list(summary, "probes").append(probe)
            core_key = (str(probe["core_type"]), str(probe["core_name"]))
            core = cores_by_key.get(core_key)
            if core is not None:
                probes = core.setdefault("probes", [])
                assert isinstance(probes, list)
                probes.append(probe)
        elif key == "property" and len(parts) >= 5:
            core_key = (parts[1], parts[2])
            core = cores_by_key.get(core_key)
            if core is not None:
                properties = core.setdefault("properties", {})
                assert isinstance(properties, dict)
                properties[parts[3]] = parts[4]
        elif key == "warning" and len(parts) >= 2:
            _list(summary, "warnings").append(parts[1])
        elif key == "error" and len(parts) >= 2:
            _list(summary, "errors").append(parts[1])
    cores = summary["cores"] if isinstance(summary["cores"], list) else []
    for core in cores:
        if isinstance(core, dict):
            probes = core.get("probes") if isinstance(core.get("probes"), list) else []
            core["probe_count"] = len(probes)
    summary["core_count"] = len(summary["cores"]) if isinstance(summary["cores"], list) else 0
    summary["ila_count"] = len(summary["ilas"]) if isinstance(summary["ilas"], list) else 0
    summary["vio_count"] = len(summary["vios"]) if isinstance(summary["vios"], list) else 0
    summary["probe_count"] = len(summary["probes"]) if isinstance(summary["probes"], list) else 0
    return summary


def parse_vio_read_tsv(path: Path, *, value_radix: str = "auto") -> dict[str, object]:
    summary: dict[str, object] = {
        "path": str(path),
        "value_radix": _normalize_radix(value_radix),
        "vio": "",
        "probes": [],
        "warnings": [],
        "errors": [],
    }
    for parts in _read_tsv(path):
        if not parts:
            continue
        key = parts[0]
        if key == "probe":
            probe = _parse_vio_read_probe_row(parts, value_radix=value_radix)
            _list(summary, "probes").append(probe)
        elif key == "meta" and len(parts) >= 3:
            if parts[1] == "vio":
                summary["vio"] = parts[2]
            meta = summary.setdefault("meta", {})
            assert isinstance(meta, dict)
            meta[parts[1]] = parts[2]
        elif key == "warning" and len(parts) >= 2:
            _list(summary, "warnings").append(parts[1])
        elif key == "error" and len(parts) >= 2:
            _list(summary, "errors").append(parts[1])
    probes = summary["probes"] if isinstance(summary["probes"], list) else []
    summary["probe_count"] = len(probes)
    summary["input_probe_count"] = sum(1 for probe in probes if isinstance(probe, dict) and str(probe.get("direction") or "").upper() == "IN")
    summary["output_probe_count"] = sum(1 for probe in probes if isinstance(probe, dict) and str(probe.get("direction") or "").upper() == "OUT")
    return summary


def parse_vio_write_tsv(path: Path, *, value_radix: str = "auto") -> dict[str, object]:
    summary: dict[str, object] = {
        "path": str(path),
        "value_radix": _normalize_radix(value_radix),
        "vio": "",
        "writes": [],
        "warnings": [],
        "errors": [],
    }
    for parts in _read_tsv(path):
        if not parts:
            continue
        key = parts[0]
        if key == "write":
            write = _parse_vio_write_row(parts, value_radix=value_radix)
            _list(summary, "writes").append(write)
        elif key == "meta" and len(parts) >= 3:
            if parts[1] == "vio":
                summary["vio"] = parts[2]
            meta = summary.setdefault("meta", {})
            assert isinstance(meta, dict)
            meta[parts[1]] = parts[2]
        elif key == "warning" and len(parts) >= 2:
            _list(summary, "warnings").append(parts[1])
        elif key == "error" and len(parts) >= 2:
            _list(summary, "errors").append(parts[1])
    writes = summary["writes"] if isinstance(summary["writes"], list) else []
    summary["write_count"] = len(writes)
    summary["write_ok_count"] = sum(1 for write in writes if isinstance(write, dict) and write.get("write_ok") is True)
    summary["all_write_ok"] = bool(writes) and summary["write_ok_count"] == len(writes)
    return summary


def analyze_ila_csv(
    path: Path,
    *,
    mode: str = "none",
    sample_rate_hz: float | None = None,
    signed_width: int | None = None,
) -> dict[str, object]:
    """Analyze a Vivado ``write_hw_ila_data -csv_file`` capture.

    The analysis is intentionally project-agnostic: probe names are preserved
    from the CSV header, numeric widths are inferred from ``[N:M]`` suffixes
    when possible, and ADC-specific signed conversion is only selected through
    the explicit ``adc14`` mode.
    """
    normalized_mode = (mode or "none").strip().lower()
    if normalized_mode not in {"none", "digital", "unsigned", "signed", "adc14"}:
        raise ValueError(f"Unsupported ILA analysis mode: {mode}")
    if normalized_mode == "none":
        return {"mode": "none", "csv_path": str(path), "row_count": _ila_row_count(path)}
    requested_mode = normalized_mode
    if normalized_mode == "adc14":
        signed_width = 14
        normalized_mode = "signed"
    if normalized_mode == "signed" and signed_width is not None and signed_width < 1:
        raise ValueError("signed_width must be greater than zero")

    header, radices, data_rows = _read_ila_csv(path)
    ignored = {"Sample in Buffer", "Sample in Window", "TRIGGER"}
    signals: dict[str, object] = {}
    for index, name in enumerate(header):
        if name in ignored:
            continue
        raw_values = [row[index] for row in data_rows if index < len(row)]
        radix = radices[index] if index < len(radices) else ""
        values = [_parse_ila_scalar(value, radix=radix) for value in raw_values]
        if not values:
            continue
        width = signed_width if normalized_mode == "signed" and signed_width else _probe_width(name)
        if normalized_mode == "signed" and width:
            values = [_sign_extend(value, width) for value in values]
        stats = _signal_stats(
            values,
            name=name,
            mode=normalized_mode,
            width=width,
            sample_rate_hz=sample_rate_hz,
        )
        signals[name] = stats

    near_clip = [
        name
        for name, stats in signals.items()
        if isinstance(stats, dict) and stats.get("near_clip") is True
    ]
    constant = [
        name
        for name, stats in signals.items()
        if isinstance(stats, dict) and stats.get("p2p") == 0
    ]
    return {
        "mode": "adc14" if requested_mode == "adc14" else normalized_mode,
        "csv_path": str(path),
        "sample_rate_hz": sample_rate_hz,
        "row_count": len(data_rows),
        "signal_count": len(signals),
        "signals": signals,
        "summary": {
            "near_clip_signals": near_clip,
            "constant_signals": constant,
            "numeric_signal_count": len(signals),
        },
    }


def parse_spi_read_tsv(
    path: Path,
    *,
    status_layout: dict[str, object] | None = None,
    status_radix: str = "hex",
) -> dict[str, object]:
    layout = normalize_spi_status_layout(status_layout)
    summary: dict[str, object] = {
        "path": str(path),
        "status_layout": layout,
        "status_radix": _normalize_radix(status_radix),
        "reads": [],
        "warnings": [],
        "errors": [],
    }
    for parts in _read_tsv(path):
        if not parts:
            continue
        key = parts[0]
        if key == "read":
            read = _parse_spi_read_row(parts, status_layout=layout, status_radix=status_radix)
            _list(summary, "reads").append(read)
        elif key == "warning" and len(parts) >= 2:
            _list(summary, "warnings").append(parts[1])
        elif key == "error" and len(parts) >= 2:
            _list(summary, "errors").append(parts[1])
        elif key == "meta" and len(parts) >= 3:
            meta = summary.setdefault("meta", {})
            assert isinstance(meta, dict)
            meta[parts[1]] = parts[2]
    reads = summary["reads"] if isinstance(summary["reads"], list) else []
    summary["register_count"] = len(reads)
    summary["read_ok_count"] = sum(1 for read in reads if isinstance(read, dict) and read.get("read_ok") is True)
    summary["all_read_ok"] = bool(reads) and summary["read_ok_count"] == len(reads)
    return summary


def decode_spi_status(
    raw: str,
    *,
    status_layout: dict[str, object] | None = None,
    status_radix: str = "hex",
) -> dict[str, object]:
    layout = normalize_spi_status_layout(status_layout)
    value = _parse_scalar(raw, radix=status_radix)
    decoded: dict[str, object] = {
        "status_raw": raw,
        "status_value": value,
        "status_hex": f"0x{value:X}",
        "data": _extract_bits(value, layout["data_bits"]),
        "last_addr": _extract_bits(value, layout["addr_bits"]),
        "last_target": _extract_bits(value, layout["target_bits"]),
        "busy": _extract_optional_bit(value, layout.get("busy_bit")),
        "done": _extract_optional_bit(value, layout.get("done_bit")),
        "enable": _extract_optional_bit(value, layout.get("enable_bit")),
        "error": _extract_optional_bit(value, layout.get("error_bit")),
    }
    decoded["data_hex"] = f"0x{int(decoded['data']):02X}"
    decoded["last_addr_hex"] = f"0x{int(decoded['last_addr']):04X}"
    return decoded


def normalize_spi_status_layout(layout: dict[str, object] | None = None) -> dict[str, object]:
    source = {**DEFAULT_SPI_STATUS_LAYOUT, **(layout or {})}
    return {
        "data_bits": _normalize_bit_range(source.get("data_bits"), "data_bits"),
        "addr_bits": _normalize_bit_range(source.get("addr_bits"), "addr_bits"),
        "target_bits": _normalize_bit_range(source.get("target_bits"), "target_bits"),
        "busy_bit": _normalize_optional_bit(source.get("busy_bit"), "busy_bit"),
        "done_bit": _normalize_optional_bit(source.get("done_bit"), "done_bit"),
        "enable_bit": _normalize_optional_bit(source.get("enable_bit"), "enable_bit"),
        "error_bit": _normalize_optional_bit(source.get("error_bit"), "error_bit"),
    }


def _read_tsv(path: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip():
            rows.append(line.split("\t"))
    return rows


def _parse_debug_core_row(parts: list[str]) -> dict[str, object]:
    return {
        "type": parts[1] if len(parts) > 1 else "",
        "name": parts[2] if len(parts) > 2 else "",
        "cell_name": parts[3] if len(parts) > 3 else "",
        "device": parts[4] if len(parts) > 4 else "",
        "properties": {},
        "probes": [],
    }


def _parse_debug_probe_row(parts: list[str]) -> dict[str, object]:
    return {
        "core_type": parts[1] if len(parts) > 1 else "",
        "core_name": parts[2] if len(parts) > 2 else "",
        "name": parts[3] if len(parts) > 3 else "",
        "direction": parts[4] if len(parts) > 4 else "",
        "width": _optional_int(parts[5] if len(parts) > 5 else ""),
        "probe_type": parts[6] if len(parts) > 6 else "",
        "input_value": parts[7] if len(parts) > 7 else "",
        "output_value": parts[8] if len(parts) > 8 else "",
    }


def _parse_vio_read_probe_row(parts: list[str], *, value_radix: str) -> dict[str, object]:
    if len(parts) < 9:
        raise ValueError(f"Malformed VIO read row: {parts!r}")
    input_value = parts[7]
    output_value = parts[8]
    value = input_value if input_value != "" else output_value
    row: dict[str, object] = {
        "index": int(parts[1]),
        "vio": parts[2],
        "name": parts[3],
        "direction": parts[4],
        "width": _optional_int(parts[5]),
        "probe_type": parts[6],
        "input_value": input_value,
        "output_value": output_value,
        "value": value,
    }
    if value != "":
        try:
            row["decoded_int"] = _parse_scalar(value, radix=value_radix)
        except ValueError as exc:
            row["decode_error"] = str(exc)
    return row


def _parse_vio_write_row(parts: list[str], *, value_radix: str) -> dict[str, object]:
    if len(parts) < 10:
        raise ValueError(f"Malformed VIO write row: {parts!r}")
    requested_value = parts[6]
    before_value = parts[7]
    after_value = parts[8]
    status = parts[9]
    row: dict[str, object] = {
        "index": int(parts[1]),
        "vio": parts[2],
        "name": parts[3],
        "direction": parts[4],
        "width": _optional_int(parts[5]),
        "requested_value": requested_value,
        "before_value": before_value,
        "after_value": after_value,
        "status": status,
        "write_ok": status == "ok",
    }
    for key in ("requested_value", "before_value", "after_value"):
        value = str(row.get(key) or "")
        if value == "":
            continue
        try:
            row[f"{key}_int"] = _parse_scalar(value, radix=value_radix)
        except ValueError as exc:
            row[f"{key}_decode_error"] = str(exc)
    return row


def _optional_int(value: str) -> int | None:
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text, 0)
    except ValueError:
        return None


def _read_ila_csv(path: Path) -> tuple[list[str], list[str], list[list[str]]]:
    if not path.exists():
        raise FileNotFoundError(f"ILA CSV does not exist: {path}")
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        rows = list(csv.reader(handle))
    if not rows:
        raise ValueError(f"ILA CSV is empty: {path}")
    header = rows[0]
    radices = rows[1] if len(rows) > 1 else []
    data_rows = [row for row in rows[2:] if row and row[0].strip().lstrip("-").isdigit()]
    return header, radices, data_rows


def _ila_row_count(path: Path) -> int:
    try:
        _header, _radices, rows = _read_ila_csv(path)
    except FileNotFoundError:
        return 0
    return len(rows)


def _parse_ila_scalar(value: str, *, radix: str = "") -> int:
    text = value.strip().replace("_", "")
    if not text:
        return 0
    normalized_radix = radix.strip().upper()
    if normalized_radix == "HEX":
        return int(text, 16)
    if normalized_radix in {"BIN", "BINARY"}:
        return int(text, 2)
    if normalized_radix in {"SIGNED", "UNSIGNED", "DEC", "DECIMAL"}:
        return int(text, 10)
    if text.lower().startswith("0x"):
        return int(text, 16)
    if re.fullmatch(r"[0-9a-fA-F]+", text) and re.search(r"[a-fA-F]", text):
        return int(text, 16)
    if re.fullmatch(r"[01]+", text) and len(text) > 1:
        return int(text, 2)
    return int(text, 10)


def _parse_spi_read_row(
    parts: list[str],
    *,
    status_layout: dict[str, object],
    status_radix: str,
) -> dict[str, object]:
    if len(parts) < 7:
        raise ValueError(f"Malformed SPI read row: {parts!r}")
    index = int(parts[1])
    requested_target = _parse_scalar(parts[2], radix="auto")
    requested_addr = _parse_scalar(parts[3], radix="auto")
    status_raw = parts[4]
    poll_count = int(parts[5])
    timed_out = _bool(parts[6])
    decoded = decode_spi_status(status_raw, status_layout=status_layout, status_radix=status_radix)
    failure_reasons = _spi_read_failure_reasons(
        decoded,
        requested_target=requested_target,
        requested_addr=requested_addr,
        timed_out=timed_out,
    )
    row = {
        "index": index,
        "requested_target": requested_target,
        "requested_addr": requested_addr,
        "requested_addr_hex": f"0x{requested_addr:04X}",
        "poll_count": poll_count,
        "timed_out": timed_out,
        **decoded,
        "read_ok": not failure_reasons,
        "failure_reasons": failure_reasons,
    }
    return row


def _spi_read_failure_reasons(
    decoded: dict[str, object],
    *,
    requested_target: int,
    requested_addr: int,
    timed_out: bool,
) -> list[str]:
    reasons: list[str] = []
    if timed_out:
        reasons.append("timeout")
    if decoded.get("done") is False:
        reasons.append("not_done")
    if decoded.get("busy") is True:
        reasons.append("busy")
    if decoded.get("error") is True:
        reasons.append("error_bit")
    if decoded.get("enable") is False:
        reasons.append("enable_low")
    if decoded.get("last_target") != requested_target:
        reasons.append("target_mismatch")
    if decoded.get("last_addr") != requested_addr:
        reasons.append("addr_mismatch")
    return reasons


def _parse_scalar(value: str, *, radix: str) -> int:
    text = str(value).strip().replace("_", "")
    if not text:
        raise ValueError("empty integer value")
    if text.lower().startswith("0x"):
        return int(text, 16)
    normalized = _normalize_radix(radix)
    if normalized == "hex":
        return int(text, 16)
    if normalized == "binary":
        return int(text, 2)
    if normalized == "decimal":
        return int(text, 10)
    if re.fullmatch(r"[01]+", text) and len(text) > 1:
        return int(text, 2)
    if re.fullmatch(r"[0-9a-fA-F]+", text) and re.search(r"[a-fA-F]", text):
        return int(text, 16)
    return int(text, 10)


def _normalize_radix(radix: str) -> str:
    normalized = (radix or "auto").strip().lower()
    aliases = {
        "bin": "binary",
        "binary": "binary",
        "dec": "decimal",
        "decimal": "decimal",
        "hex": "hex",
        "auto": "auto",
    }
    if normalized not in aliases:
        raise ValueError(f"Unsupported SPI status radix: {radix}")
    return aliases[normalized]


def _normalize_bit_range(value: object, name: str) -> list[int]:
    if isinstance(value, str):
        parts = value.split(":")
        if len(parts) == 1:
            bit = int(parts[0], 0)
            return [bit, bit]
        if len(parts) == 2:
            return [int(parts[0], 0), int(parts[1], 0)]
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return [int(value[0]), int(value[1])]
    raise ValueError(f"{name} must be a bit range like '7:0'")


def _normalize_optional_bit(value: object, name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, str) and value.strip().lower() in {"", "none", "off", "disabled"}:
        return None
    bit = int(value, 0) if isinstance(value, str) else int(value)
    if bit < 0:
        return None
    return bit


def _extract_bits(value: int, bit_range: object) -> int:
    left, right = _normalize_bit_range(bit_range, "bit_range")
    low = min(left, right)
    high = max(left, right)
    width = high - low + 1
    return (value >> low) & ((1 << width) - 1)


def _extract_optional_bit(value: int, bit: object) -> bool | None:
    normalized = _normalize_optional_bit(bit, "bit")
    if normalized is None:
        return None
    return bool((value >> normalized) & 1)


def _probe_width(name: str) -> int | None:
    match = re.search(r"\[(\d+)(?::(\d+))?\]", name)
    if not match:
        return None
    left = int(match.group(1))
    right = int(match.group(2) or match.group(1))
    return abs(left - right) + 1


def _sign_extend(value: int, width: int) -> int:
    mask = 1 << (width - 1)
    full = 1 << width
    value &= full - 1
    return value - full if value & mask else value


def _signal_stats(
    values: list[int],
    *,
    name: str,
    mode: str,
    width: int | None,
    sample_rate_hz: float | None,
) -> dict[str, Any]:
    count = len(values)
    minimum = min(values)
    maximum = max(values)
    mean = sum(values) / count
    centered = [value - mean for value in values]
    rms_ac = math.sqrt(sum(value * value for value in centered) / count)
    unique_values = sorted(set(values))
    stats: dict[str, Any] = {
        "name": name,
        "display_name": _display_probe_name(name),
        "width": width,
        "sample_count": count,
        "min": minimum,
        "max": maximum,
        "p2p": maximum - minimum,
        "mean": mean,
        "rms_ac": rms_ac,
        "unique_values": unique_values[:16],
        "unique_value_count": len(unique_values),
    }
    if mode == "signed" and width:
        negative_full_scale = -(1 << (width - 1))
        positive_full_scale = (1 << (width - 1)) - 1
        threshold = 0.95
        stats["full_scale"] = {
            "negative": negative_full_scale,
            "positive": positive_full_scale,
        }
        stats["near_clip"] = minimum <= int(negative_full_scale * threshold) or maximum >= int(positive_full_scale * threshold)
    else:
        stats["near_clip"] = False
    if count >= 4 and count <= MAX_DFT_SAMPLES and maximum != minimum:
        peak = _dft_peak(centered)
        stats["peak_bin"] = peak["bin"]
        stats["peak_magnitude"] = peak["magnitude"]
        if sample_rate_hz:
            stats["peak_frequency_hz"] = peak["bin"] * sample_rate_hz / count
    elif count > MAX_DFT_SAMPLES:
        stats["fft_skipped"] = {
            "reason": "sample_count_exceeds_limit",
            "max_dft_samples": MAX_DFT_SAMPLES,
        }
    return stats


def _display_probe_name(name: str) -> str:
    tail = name.rsplit("/", 1)[-1]
    return re.sub(r"\[[^\]]+\]$", "", tail)


def _dft_peak(values: list[float]) -> dict[str, float | int]:
    count = len(values)
    best_bin = 0
    best_magnitude = -1.0
    for bin_index in range(1, count // 2 + 1):
        real = 0.0
        imag = 0.0
        for sample_index, value in enumerate(values):
            angle = -2.0 * math.pi * bin_index * sample_index / count
            real += value * math.cos(angle)
            imag += value * math.sin(angle)
        magnitude = math.hypot(real, imag)
        if magnitude > best_magnitude:
            best_bin = bin_index
            best_magnitude = magnitude
    return {"bin": best_bin, "magnitude": best_magnitude}


def _bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _list(container: dict[str, object], key: str) -> list[object]:
    value = container.setdefault(key, [])
    assert isinstance(value, list)
    return value
