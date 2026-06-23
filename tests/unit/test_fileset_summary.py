from __future__ import annotations

from pathlib import Path

from vivado_mcp.fileset_summary import (
    analyze_source_audit,
    analyze_xdc_order,
    parse_constraint_diagnostics,
    parse_describe_fileset,
    parse_list_filesets,
)


def test_parse_list_filesets_extracts_types_and_tops(tmp_path: Path) -> None:
    tsv = tmp_path / "filesets.tsv"
    tsv.write_text(
        "\n".join(
            [
                "has_project\t1",
                "current_project\tfake_project",
                "fileset\tsources_1\tSource\t3\t1\t1\t1\ttop\t1",
                "fileset\tsim_1\tSimulation\t1\t0\t1\t0\ttb_top\t0",
                "fileset\tconstrs_1\tConstrs\t2\t1\t0\t1\ttop\t1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    parsed = parse_list_filesets(tsv)
    assert parsed["has_project"] is True
    assert parsed["current_project"] == "fake_project"
    by_name = {row["name"]: row for row in parsed["filesets"]}
    assert by_name["sources_1"]["type"] == "Source"
    assert by_name["sources_1"]["is_enabled_synthesis"] is True
    assert by_name["sim_1"]["top"] == "tb_top"
    assert by_name["sim_1"]["is_default"] is False
    assert by_name["constrs_1"]["file_count"] == 2


def test_parse_describe_fileset_returns_files_and_properties(tmp_path: Path) -> None:
    tsv = tmp_path / "desc.tsv"
    tsv.write_text(
        "\n".join(
            [
                "fileset\tsources_1",
                "property\tFILESET_TYPE\tSource",
                "property\tTOP\ttop",
                "file\tC:/fake/top.v\tVerilog\txil_defaultlib\t0\t1\t1\t1",
                "file\tC:/fake/alu.v\tVerilog\txil_defaultlib\t1\t1\t1\t1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    parsed = parse_describe_fileset(tsv)
    assert parsed["name"] == "sources_1"
    assert parsed["properties"]["TOP"] == "top"
    assert len(parsed["files"]) == 2
    assert parsed["files"][0]["library"] == "xil_defaultlib"
    assert parsed["files"][1]["processing_order"] == 1


def test_parse_constraint_diagnostics_sorts_files_by_fileset_and_order(tmp_path: Path) -> None:
    tsv = tmp_path / "diag.tsv"
    tsv.write_text(
        "\n".join(
            [
                "has_project\t1",
                "current_project\tfake_project",
                "fileset\tconstrs_1\tConstrs\t1\t1\t0\t1\ttop",
                "constraint_file\tconstrs_1\t1\tC:/fake/pinout.xdc\tXDC",
                "constraint_file\tconstrs_1\t0\tC:/fake/timing.xdc\tXDC",
                "marker\tcreate_clock\t1",
                "marker\tset_input_delay\t1",
                "marker\tset_output_delay\t1",
                "marker\tget_ports\t1",
                "warning\tno_create_clock_but_has_input_delay",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    parsed = parse_constraint_diagnostics(tsv)
    assert parsed["has_project"] is True
    assert any(fs["name"] == "constrs_1" for fs in parsed["constrs_filesets"])
    orders = [row["order"] for row in parsed["constraint_files"]]
    assert orders == [0, 1]
    assert parsed["xdc_markers"]["create_clock"] == 1
    assert parsed["xdc_markers"]["set_input_delay"] == 1
    assert parsed["warnings"] == ["no_create_clock_but_has_input_delay"]


def test_analyze_source_audit_flags_missing_top_duplicates_and_scope() -> None:
    project = {
        "has_project": True,
        "top": "missing_top",
        "files": [
            {"path": "C:/fake/top.v", "file_type": "Verilog"},
            {"path": "C:/fake/top.v", "file_type": "Verilog"},
            {"path": "C:/fake/pins.xdc", "file_type": "XDC"},
        ],
        "runs": [{"name": "synth_1", "status": "Not started", "progress": "0%"}],
    }
    filesets = {
        "has_project": True,
        "filesets": [
            {"name": "sources_1", "type": "Source", "file_count": 2, "top": "missing_top"},
            {"name": "constrs_1", "type": "Constrs", "file_count": 1, "top": "missing_top"},
        ],
    }
    described = [
        {
            "name": "sources_1",
            "properties": {"TOP": "missing_top", "INCLUDE_DIRS": "C:/fake/include"},
            "files": [
                {
                    "path": "C:/fake/top.v",
                    "file_type": "Verilog",
                    "library": "xil_defaultlib",
                    "processing_order": 0,
                    "is_enabled_synthesis": True,
                    "is_enabled_simulation": True,
                    "is_enabled_implementation": True,
                },
                {
                    "path": "C:/fake/pins.xdc",
                    "file_type": "XDC",
                    "library": "",
                    "processing_order": 1,
                    "is_enabled_synthesis": True,
                    "is_enabled_simulation": False,
                    "is_enabled_implementation": True,
                },
            ],
        }
    ]
    constraints = {
        "constraint_files": [{"fileset": "constrs_1", "order": 0, "path": "C:/fake/pins.xdc", "file_type": "XDC"}],
        "xdc_markers": {"create_clock": 0},
        "warnings": [],
    }

    audit = analyze_source_audit(project, filesets, described, constraints)

    issue_ids = {issue["issue_id"] for issue in audit["issues"]}
    issues_by_id = {issue["issue_id"]: issue for issue in audit["issues"]}
    assert audit["ok"] is False
    assert {"top.not_found_in_files", "file.duplicate", "constraint.in_source_fileset", "constraints.no_create_clock"}.issubset(issue_ids)
    assert issues_by_id["top.not_found_in_files"]["confidence"] == "heuristic"
    assert audit["summary"]["fileset_count"] == 2


def test_analyze_xdc_order_flags_constraints_before_clocks() -> None:
    diagnostics = {
        "has_project": True,
        "constraint_files": [
            {"fileset": "constrs_1", "order": 0, "path": "C:/fake/exceptions.xdc", "file_type": "XDC"},
            {"fileset": "constrs_1", "order": 1, "path": "C:/fake/clocks.xdc", "file_type": "XDC"},
        ],
        "xdc_file_markers": [
            {"path": "C:/fake/exceptions.xdc", "create_clock": 0, "set_false_path": 1, "set_input_delay": 0, "set_output_delay": 0},
            {"path": "C:/fake/clocks.xdc", "create_clock": 1, "set_false_path": 0, "set_input_delay": 0, "set_output_delay": 0},
        ],
        "warnings": [],
    }

    order = analyze_xdc_order(diagnostics)

    assert order["ok"] is False
    assert order["filesets"]["constrs_1"][0]["path"].endswith("exceptions.xdc")
    assert order["issues"][0]["issue_id"] == "xdc.exception_before_clock"
