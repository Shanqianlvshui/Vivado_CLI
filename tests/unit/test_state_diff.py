from __future__ import annotations

from vivado_mcp.state_diff import diff_states, state_digest


def test_diff_states_reports_project_files_runs_and_ips() -> None:
    before = {
        "project": {
            "has_project": True,
            "current_project": "demo",
            "files": [{"path": "C:/demo/top.v", "file_type": "Verilog"}],
            "runs": [{"name": "synth_1", "status": "Not started", "progress": "0%"}],
            "ips": [],
            "block_designs": [],
        },
        "filesets": {
            "filesets": [{"name": "sources_1", "type": "Source", "file_count": 1, "top": "top"}],
        },
    }
    after = {
        "project": {
            "has_project": True,
            "current_project": "demo",
            "files": [
                {"path": "C:/demo/top.v", "file_type": "Verilog"},
                {"path": "C:/demo/alu.v", "file_type": "Verilog"},
            ],
            "runs": [{"name": "synth_1", "status": "synth_design Complete!", "progress": "100%"}],
            "ips": ["axi_gpio_0"],
            "block_designs": [],
        },
        "filesets": {
            "filesets": [{"name": "sources_1", "type": "Source", "file_count": 2, "top": "alu"}],
        },
    }

    diff = diff_states(before, after)

    assert diff["changed"] is True
    assert diff["project"]["files"]["added"] == [{"path": "C:/demo/alu.v", "file_type": "Verilog"}]
    assert diff["project"]["runs"]["changed"][0]["key"] == "synth_1"
    assert diff["project"]["ips"]["added"] == ["axi_gpio_0"]
    assert diff["filesets"]["filesets"]["changed"][0]["key"] == "sources_1"


def test_diff_states_reports_constraints_and_bd_changes() -> None:
    before = {
        "constraints": {
            "constraint_files": [{"fileset": "constrs_1", "order": 0, "path": "C:/demo/base.xdc", "file_type": "XDC"}],
            "warnings": [],
            "xdc_markers": {"create_clock": 1},
        },
        "block_design": {
            "has_block_design": True,
            "current_bd_design": "design_1",
            "cells": [{"name": "/clk_wiz_0", "type": "ip", "vlnv": "xilinx.com:ip:clk_wiz:6.0"}],
            "ports": [],
            "nets": [],
            "interface_nets": [],
        },
    }
    after = {
        "constraints": {
            "constraint_files": [
                {"fileset": "constrs_1", "order": 0, "path": "C:/demo/base.xdc", "file_type": "XDC"},
                {"fileset": "constrs_1", "order": 1, "path": "C:/demo/pins.xdc", "file_type": "XDC"},
            ],
            "warnings": ["no_create_clock_but_has_false_path"],
            "xdc_markers": {"create_clock": 1, "set_false_path": 1},
        },
        "block_design": {
            "has_block_design": True,
            "current_bd_design": "design_1",
            "cells": [
                {"name": "/clk_wiz_0", "type": "ip", "vlnv": "xilinx.com:ip:clk_wiz:6.0"},
                {"name": "/axi_gpio_0", "type": "ip", "vlnv": "xilinx.com:ip:axi_gpio:2.0"},
            ],
            "ports": [{"name": "/gpio_tri_o", "direction": "O", "type": "data", "left": "31", "right": "0"}],
            "nets": [],
            "interface_nets": [],
        },
    }

    diff = diff_states(before, after)

    assert diff["constraints"]["constraint_files"]["added"][0]["path"].endswith("pins.xdc")
    assert diff["constraints"]["warnings"]["added"] == ["no_create_clock_but_has_false_path"]
    assert diff["block_design"]["cells"]["added"][0]["name"] == "/axi_gpio_0"
    assert diff["block_design"]["ports"]["added"][0]["name"] == "/gpio_tri_o"


def test_state_digest_is_stable_for_reordered_data() -> None:
    left = {"project": {"ips": ["b", "a"], "files": [{"path": "b.v"}, {"path": "a.v"}]}}
    right = {"project": {"files": [{"path": "a.v"}, {"path": "b.v"}], "ips": ["a", "b"]}}

    assert state_digest(left) == state_digest(right)
