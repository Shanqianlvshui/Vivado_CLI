from __future__ import annotations

from pathlib import Path

from vivado_cli.nonproject_summary import analyze_nonproject_audit, nonproject_step_prerequisites, parse_nonproject_summary


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


def test_analyze_nonproject_audit_detects_stage_and_next_step() -> None:
    summary = {
        "files": [{"kind": "verilog", "path": "C:/demo/top.v"}],
        "constraints": [{"path": "C:/demo/timing.xdc"}],
        "steps": [{"name": "synth_design", "status": "ok"}],
        "part": "xc7a35tcpg236-1",
        "top": "top",
    }

    audit = analyze_nonproject_audit(summary)

    assert audit["ok"] is True
    assert audit["stage"] == "synth_design"
    assert audit["next_step"] == "opt_design"
    assert audit["recommendations"][0]["tool"] == "vivado_nonproject_opt_design"


def test_analyze_nonproject_audit_flags_missing_inputs() -> None:
    audit = analyze_nonproject_audit({"files": [], "constraints": [], "steps": []}, expected_top="top")

    assert audit["ok"] is False
    issue_ids = {issue["issue_id"] for issue in audit["issues"]}
    assert {"nonproject.sources_missing", "nonproject.part_missing", "nonproject.top_missing"} <= issue_ids
    assert audit["recommendations"][0]["tool"] == "vivado_nonproject_read_sources"


def test_nonproject_step_prerequisites() -> None:
    synth = nonproject_step_prerequisites("synth_design", {"files": []}, part="", top="")
    assert {"nonproject.sources_missing", "nonproject.part_missing", "nonproject.top_missing"} <= {
        issue["issue_id"] for issue in synth["issues"]
    }

    place = nonproject_step_prerequisites("place_design", {"steps": [{"name": "synth_design", "status": "ok"}]})
    assert place["ok"] is False
    assert place["issues"][0]["issue_id"] == "nonproject.previous_step_missing"
