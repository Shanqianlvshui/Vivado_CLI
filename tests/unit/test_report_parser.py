from vivado_mcp.report_parser import parse_messages, parse_timing, parse_utilization


def test_parse_timing_extracts_wns_and_status() -> None:
    summary = parse_timing("WNS(ns) -0.125\nTNS(ns) -1.250\n")
    assert summary["parsed"] is True
    assert summary["status"] == "fail"
    assert summary["wns"] == -0.125
    assert summary["tns"] == -1.25


def test_parse_utilization_extracts_table_row() -> None:
    summary = parse_utilization("| CLB LUTs | 1,234 | 10,000 | 12.34 |")
    assert summary["parsed"] is True
    assert summary["resources"]["clb_luts"]["used"] == 1234


def test_parse_messages_counts_vivado_messages() -> None:
    summary = parse_messages("ERROR: [A 1]\nCRITICAL WARNING: [B 2]\nWARNING: [C 3]\n")
    assert summary["errors"] == 1
    assert summary["critical_warnings"] == 1
    assert summary["warnings"] == 1

