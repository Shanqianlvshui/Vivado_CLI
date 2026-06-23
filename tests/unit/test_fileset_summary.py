from __future__ import annotations

from pathlib import Path

from vivado_mcp.fileset_summary import (
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
