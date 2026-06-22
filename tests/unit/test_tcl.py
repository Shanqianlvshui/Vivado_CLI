from pathlib import Path

import pytest

from vivado_mcp.tcl import create_project_tcl, quote_tcl, report_tcl


def test_quote_tcl_normalizes_windows_paths() -> None:
    assert quote_tcl(Path(r"C:\Work\a b\top.v")) == "{C:/Work/a b/top.v}"


def test_create_project_tcl_supports_part_and_force() -> None:
    script = create_project_tcl(
        project_name="demo",
        project_dir=Path("build/demo"),
        part="xc7a35tcpg236-1",
        board_part=None,
        force=True,
    )
    assert "create_project {demo}" in script
    assert "-part {xc7a35tcpg236-1}" in script
    assert "-force" in script


def test_report_tcl_rejects_unknown_report_type() -> None:
    with pytest.raises(ValueError):
        report_tcl("unknown", Path("out.rpt"))

