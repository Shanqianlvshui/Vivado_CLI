from vivado_mcp.report_parser import analyze_report_summaries, parse_messages, parse_power, parse_timing, parse_utilization


def test_parse_timing_extracts_wns_and_status() -> None:
    summary = parse_timing("WNS(ns) -0.125\nTNS(ns) -1.250\nFailing Endpoints: 4\n")
    assert summary["parsed"] is True
    assert summary["status"] == "fail"
    assert summary["wns"] == -0.125
    assert summary["tns"] == -1.25
    assert summary["failing_endpoints"] == 4


def test_parse_utilization_extracts_table_row() -> None:
    summary = parse_utilization("| CLB LUTs | 1,234 | 10,000 | 12.34 |")
    assert summary["parsed"] is True
    assert summary["resources"]["clb_luts"]["used"] == 1234
    assert summary["resources"]["clb_luts"]["utilization_percent"] == 12.34


def test_parse_messages_counts_vivado_messages() -> None:
    summary = parse_messages("ERROR: [DRC A-1] broken\nCRITICAL WARNING: [TIMING B-2] weak\nWARNING: [C 3]\n")
    assert summary["errors"] == 1
    assert summary["critical_warnings"] == 1
    assert summary["warnings"] == 1
    assert summary["rules"]["DRC A-1"]["errors"] == 1
    assert summary["rules"]["TIMING B-2"]["critical_warnings"] == 1
    assert summary["rules"]["TIMING B-2"]["warnings"] == 0
    assert summary["rules"]["C 3"]["warnings"] == 1


def test_parse_power_extracts_totals() -> None:
    summary = parse_power("Total On-Chip Power (W) 3.210\nDynamic (W) 2.100\nDevice Static (W) 1.110\n")

    assert summary["parsed"] is True
    assert summary["total_on_chip_power_w"] == 3.21
    assert summary["dynamic_power_w"] == 2.1
    assert summary["static_power_w"] == 1.11


def test_analyze_report_summaries_prioritizes_actionable_findings() -> None:
    analysis = analyze_report_summaries(
        {
            "timing_summary": parse_timing("WNS(ns) -0.500\nTNS(ns) -10.0\nFailing Endpoints: 12\n"),
            "utilization": parse_utilization("| DSPs | 95 | 100 | 95.0 |"),
            "drc": parse_messages("ERROR: [DRC NSTD-1] Unspecified I/O Standard\n"),
            "power": parse_power("Total On-Chip Power (W) 7.500\nDynamic (W) 6.000\nDevice Static (W) 1.500\n"),
        }
    )

    issue_ids = [issue["issue_id"] for issue in analysis["issues"]]
    assert analysis["ok"] is False
    assert issue_ids[:2] == ["drc.error", "timing.setup_failed"]
    assert "utilization.high" in issue_ids
    assert "power.high_total" in issue_ids
    assert "vivado_report" in analysis["suggested_next_tools"]
    assert "UG906" in analysis["official_references"]
