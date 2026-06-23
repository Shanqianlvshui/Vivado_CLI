from __future__ import annotations

from vivado_mcp.gui_probe import _matches_vivado_window


def test_vivado_gui_match_ignores_transient_script_progress_window() -> None:
    watched_pids = {59396}

    assert not _matches_vivado_window(
        {
            "handle": 1,
            "pid": 59396,
            "title": r" Sourcing Tcl script 'C:\tools\vivado_mcp\assets\mcp_bridge.tcl' ",
        },
        watched_pids=watched_pids,
        title_hints=[],
    )

    assert _matches_vivado_window(
        {
            "handle": 2,
            "pid": 59396,
            "title": "design_1 - [C:/workspace/demo.xpr] - Vivado 2023.1",
        },
        watched_pids=watched_pids,
        title_hints=[],
    )

    assert _matches_vivado_window(
        {"handle": 3, "pid": 59396, "title": "Vivado 2023.1"},
        watched_pids=watched_pids,
        title_hints=[],
    )
