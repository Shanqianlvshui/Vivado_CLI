from pathlib import Path

import pytest

from vivado_mcp.tcl import bd_apply_tcl, bd_generate_tcl, bd_open_or_create_tcl, create_project_tcl, quote_tcl, report_tcl


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


def test_bd_open_or_create_tcl_is_generic() -> None:
    script = bd_open_or_create_tcl(design_name="design_1")

    assert "create_bd_design $mcp_bd_name" in script
    assert "open_bd_design" in script
    assert "project_specific" not in script
    assert "board_preset" not in script


def test_bd_apply_tcl_builds_generic_actions() -> None:
    script = bd_apply_tcl(
        design_name="design_1",
        actions=[
            {"action": "create_cell", "name": "axi_gpio_0", "vlnv": "xilinx.com:ip:axi_gpio:*"},
            {"action": "create_port", "name": "gpio_tri_o", "direction": "O", "from": 31, "to": 0},
            {
                "action": "set_property",
                "object_type": "cell",
                "object": "axi_gpio_0",
                "properties": {"CONFIG.C_GPIO_WIDTH": 32},
            },
            {"action": "connect_net", "endpoints": ["axi_gpio_0/gpio_io_o", "gpio_tri_o"]},
        ],
    )

    assert "create_bd_cell -type ip -vlnv {xilinx.com:ip:axi_gpio:*} {axi_gpio_0}" in script
    assert "create_bd_port -dir {O} -from 31 -to 0 {gpio_tri_o}" in script
    assert "set_property -dict [list {CONFIG.C_GPIO_WIDTH} {32}]" in script
    assert "connect_bd_net [mcp_bd_endpoint {axi_gpio_0/gpio_io_o}] [mcp_bd_endpoint {gpio_tri_o}]" in script
    assert "validate_bd_design" in script
    assert "save_bd_design" in script


def test_bd_generate_tcl_can_skip_wrapper() -> None:
    script = bd_generate_tcl(design_name="design_1", target="synthesis", make_wrapper=False)

    assert "generate_target {synthesis}" in script
    assert "make_wrapper" not in script
