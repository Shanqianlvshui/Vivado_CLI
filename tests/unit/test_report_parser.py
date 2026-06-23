from vivado_mcp.report_parser import (
    append_report_generation_issues,
    analyze_report_summaries,
    parse_clock_interaction,
    parse_messages,
    parse_power,
    parse_timing,
    parse_utilization,
)


def test_parse_timing_extracts_wns_and_status() -> None:
    summary = parse_timing(
        "\n".join(
            [
                "WNS(ns) -0.125",
                "TNS(ns) -1.250",
                "WHS(ns) -0.030",
                "THS(ns) -0.090",
                "Failing Endpoints: 4",
                "Unconstrained Paths: 3",
                "Unconstrained Clocks: 1",
                "Clock Interaction Warnings: 2",
            ]
        )
    )
    assert summary["parsed"] is True
    assert summary["status"] == "fail"
    assert summary["wns"] == -0.125
    assert summary["tns"] == -1.25
    assert summary["whs"] == -0.03
    assert summary["setup"]["wns"] == -0.125
    assert summary["hold"]["whs"] == -0.03
    assert summary["failing_endpoints"] == 4
    assert summary["unconstrained_paths"] == 3
    assert summary["unconstrained_clocks"] == 1
    assert summary["clock_interaction_warnings"] == 2


def test_parse_timing_extracts_paths_and_pulse_width() -> None:
    summary = parse_timing(
        "\n".join(
            [
                "Slack (VIOLATED) : -0.222ns",
                "Slack (MET) : 0.051ns",
                "Startpoint Clock: clk_a",
                "Endpoint Clock: clk_b",
                "WPWS(ns) -0.010",
                "TPWS(ns) -0.020",
            ]
        )
    )

    assert summary["parsed"] is True
    assert summary["worst_slack_ns"] == -0.222
    assert summary["violated_path_count"] == 1
    assert summary["timing_path_sample"]["startpoint_clock"] == "clk_a"
    assert summary["timing_path_sample"]["endpoint_clock"] == "clk_b"
    assert summary["pulse_width"]["wpws"] == -0.01


def test_parse_utilization_extracts_table_row() -> None:
    summary = parse_utilization("| CLB LUTs | 1,234 | 10,000 | 12.34 |\n| DSPs | 95 | 0 | 0 | 100 | 95.0 |")
    assert summary["parsed"] is True
    assert summary["resources"]["clb_luts"]["used"] == 1234
    assert summary["resources"]["clb_luts"]["utilization_percent"] == 12.34
    assert summary["resources"]["dsps"]["available"] == 100
    assert summary["resources"]["dsps"]["resource_class"] == "dsp"


def test_parse_utilization_extracts_io_and_clock_buffers() -> None:
    summary = parse_utilization("| Bonded IOB | 230 | 240 | 95.8 |\n| BUFG | 29 | 32 | 90.6 |\n")

    assert summary["parsed"] is True
    assert summary["resources"]["bonded_iob"]["resource_class"] == "io"
    assert summary["resources"]["bufg"]["resource_class"] == "clocking"


def test_parse_messages_counts_vivado_messages() -> None:
    summary = parse_messages(
        "ERROR: [DRC NSTD-1] Unspecified I/O Standard\n"
        "ERROR: [DRC UCIO-1] Unconstrained Logical Port\n"
        "CRITICAL WARNING: [METHODOLOGY TIMING-1] Review clocks\n"
        "WARNING: [C 3] generic warning\n"
    )
    assert summary["errors"] == 2
    assert summary["critical_warnings"] == 1
    assert summary["warnings"] == 1
    assert summary["rules"]["DRC NSTD-1"]["errors"] == 1
    assert summary["rules"]["DRC UCIO-1"]["errors"] == 1
    assert summary["rules"]["METHODOLOGY TIMING-1"]["critical_warnings"] == 1
    assert summary["rules"]["METHODOLOGY TIMING-1"]["warnings"] == 0
    assert summary["rules"]["C 3"]["warnings"] == 1
    assert summary["rule_categories"]["io_standard_missing"] == 1
    assert summary["rule_categories"]["io_pin_unconstrained"] == 1
    assert summary["rule_categories"]["clocking"] == 1
    assert summary["category_rules"]["io_standard_missing"]["DRC NSTD-1"] == 1
    assert summary["messages"][0]["rule_id"] == "DRC NSTD-1"


def test_parse_messages_classifies_cdc_reset_and_bitstream_blockers() -> None:
    summary = parse_messages(
        "CRITICAL WARNING: [METHODOLOGY CDC-10] Unsafe CDC path\n"
        "WARNING: [METHODOLOGY RESET-1] Reset is not synchronized\n"
        "ERROR: [DRC BITSTREAM-1] Bitstream generation is not allowed\n",
        report_type="methodology",
    )

    assert summary["rule_categories"]["cdc"] == 1
    assert summary["rule_categories"]["reset"] == 1
    assert summary["rule_categories"]["bitstream_blocker"] == 1


def test_parse_clock_interaction_counts_unsafe_relationships() -> None:
    summary = parse_clock_interaction(
        "Clock Interaction Report\n"
        "Unsafe clock interaction between clk_a and clk_b\n"
        "No common primary clock between clk_c and clk_d\n"
        "Partial false path coverage\n"
    )

    assert summary["parsed"] is True
    assert summary["unsafe_count"] == 1
    assert summary["no_common_clock_count"] == 1
    assert summary["partial_count"] == 1


def test_parse_power_extracts_totals() -> None:
    summary = parse_power(
        "Total On-Chip Power (W) 3.210\n"
        "Dynamic (W) 2.100\n"
        "Device Static (W) 1.110\n"
        "Junction Temperature (C) 76.5\n"
        "Thermal Margin (C) 8.0\n"
        "Confidence Level: Low\n"
    )

    assert summary["parsed"] is True
    assert summary["total_on_chip_power_w"] == 3.21
    assert summary["dynamic_power_w"] == 2.1
    assert summary["static_power_w"] == 1.11
    assert summary["junction_temperature_c"] == 76.5
    assert summary["thermal_margin_c"] == 8.0
    assert summary["confidence_level"] == "low"


def test_analyze_report_summaries_emits_structured_issue_taxonomy() -> None:
    analysis = analyze_report_summaries(
        {
            "timing_summary": parse_timing(
                "WNS(ns) -0.500\nTNS(ns) -10.0\nWHS(ns) -0.050\nTHS(ns) -0.5\n"
                "Failing Endpoints: 12\nUnconstrained Paths: 2\nClock Interaction Warnings: 1\n"
            ),
            "utilization": parse_utilization("| DSPs | 95 | 100 | 95.0 |"),
            "drc": parse_messages("ERROR: [DRC NSTD-1] Unspecified I/O Standard\n"),
            "methodology": parse_messages(
                "CRITICAL WARNING: [METHODOLOGY TIMING-1] Review generated clocks\n",
                report_type="methodology",
            ),
            "power": parse_power(
                "Total On-Chip Power (W) 7.500\nDynamic (W) 6.000\nDevice Static (W) 1.500\n"
                "Junction Temperature (C) 86.0\nThermal Margin (C) 4.0\n"
            ),
            "clock_interaction": parse_clock_interaction("Unsafe clock interaction between clk_a and clk_b\n"),
        }
    )

    issue_ids = [issue["issue_id"] for issue in analysis["issues"]]
    assert analysis["ok"] is False
    assert issue_ids[:3] == ["drc.io_standard_missing", "timing.unconstrained_paths", "timing.setup_failed"]
    assert "timing.hold_failed" in issue_ids
    assert "timing.clock_interaction_issue" in issue_ids
    assert "utilization.resource_pressure" in issue_ids
    assert "methodology.clocking_issue" in issue_ids
    assert "clock_interaction.unsafe" in issue_ids
    assert "power.thermal_risk" in issue_ids
    assert "power.high_total" in issue_ids
    assert analysis["quality_gates"]["bitstream_ready"] is False
    assert analysis["next_action_plan"][0]["tool"] == "vivado_constraint_diagnostics"
    assert analysis["issues"][0]["root_cause_hint"]
    assert analysis["issues"][0]["next_tools"]
    assert analysis["issues"][0]["official_doc_queries"]
    assert "vivado_report" in analysis["suggested_next_tools"]
    assert "UG906" in analysis["official_references"]


def test_analyze_report_summaries_emits_v2_specific_issue_ids() -> None:
    analysis = analyze_report_summaries(
        {
            "timing_paths": parse_timing("Slack (VIOLATED) : -0.100ns\nWPWS(ns) -0.020\n"),
            "utilization": parse_utilization("| Bonded IOB | 230 | 240 | 95.8 |\n| BUFG | 29 | 32 | 90.6 |\n"),
            "methodology": parse_messages(
                "CRITICAL WARNING: [METHODOLOGY CDC-10] Unsafe CDC path\n"
                "WARNING: [METHODOLOGY RESET-1] Reset is not synchronized\n"
            ),
            "power": parse_power("Confidence Level: Low\n"),
        }
    )

    issue_ids = {issue["issue_id"] for issue in analysis["issues"]}
    assert "timing.path_slack_failed" in issue_ids
    assert "timing.pulse_width_failed" in issue_ids
    assert "utilization.io_pressure" in issue_ids
    assert "utilization.clock_buffer_pressure" in issue_ids
    assert "methodology.cdc_issue" in issue_ids
    assert "methodology.reset_issue" in issue_ids
    assert "power.low_confidence" in issue_ids
    assert "UG907" in analysis["official_references"]


def test_analyze_report_summaries_prioritizes_actionable_findings() -> None:
    analysis = analyze_report_summaries(
        {
            "timing_summary": parse_timing("WNS(ns) -0.500\nTNS(ns) -10.0\nFailing Endpoints: 12\n"),
            "utilization": parse_utilization("| DSPs | 95 | 100 | 95.0 |"),
            "drc": parse_messages("ERROR: [DRC UCIO-1] Unconstrained Logical Port\n"),
            "power": parse_power("Total On-Chip Power (W) 7.500\nDynamic (W) 6.000\nDevice Static (W) 1.500\n"),
        }
    )

    issue_ids = [issue["issue_id"] for issue in analysis["issues"]]
    assert analysis["ok"] is False
    assert issue_ids[:2] == ["drc.io_pin_unconstrained", "timing.setup_failed"]
    assert "utilization.resource_pressure" in issue_ids
    assert "power.high_total" in issue_ids
    assert "vivado_report" in analysis["suggested_next_tools"]
    assert "UG906" in analysis["official_references"]


def test_append_report_generation_issues_marks_failed_reports_not_clean() -> None:
    analysis = analyze_report_summaries({})

    append_report_generation_issues(
        analysis,
        [
            {
                "report_type": "timing_summary",
                "ok": False,
                "error": "ERROR: Cannot run report_timing_summary before design is loaded",
                "result_artifact_uri": "vivado://sessions/test/artifacts/done/result.txt",
                "command_artifact_uri": "vivado://sessions/test/artifacts/running/command.tcl",
            }
        ],
    )

    assert analysis["ok"] is False
    assert analysis["summary"]["issue_count"] == 1
    assert analysis["summary"]["medium_count"] == 1
    assert analysis["issues"][0]["issue_id"] == "report.generation_failed"
    assert analysis["quality_gates"]["bitstream_ready"] is False
    assert analysis["next_action_plan"][0]["tool"] == "vivado_report"
