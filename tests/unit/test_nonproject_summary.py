from __future__ import annotations

from pathlib import Path

from vivado_mcp.nonproject_summary import parse_nonproject_summary


def test_parse_nonproject_summary_extracts_files_steps_reports(tmp_path: Path) -> None:
    tsv = tmp_path / "nonproject.tsv"
    tsv.write_text(
        "\n".join(
            [
                "file\tverilog\tC:/demo/top.v\txil_defaultlib",
                "file\tvhdl\tC:/demo/pkg.vhd\twork",
                "constraint\tC:/demo/timing.xdc\tglobal",
                "part\txc7a35tcpg236-1",
                "top\ttop",
                "step\tsynth_design\tok\t",
                "checkpoint\tsynth_design\tC:/demo/synth.dcp",
                "report\tutilization\tC:/demo/util.rpt",
                "message\twarning\tReview clocks",
                "",
            ]
        ),
        encoding="utf-8",
    )

    parsed = parse_nonproject_summary(tsv)

    assert parsed["file_count"] == 2
    assert parsed["constraint_count"] == 1
    assert parsed["step_count"] == 1
    assert parsed["part"] == "xc7a35tcpg236-1"
    assert parsed["top"] == "top"
    assert parsed["files"][0]["kind"] == "verilog"
    assert parsed["steps"][0]["name"] == "synth_design"
    assert parsed["reports"][0]["type"] == "utilization"
