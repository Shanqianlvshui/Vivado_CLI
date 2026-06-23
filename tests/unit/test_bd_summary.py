from __future__ import annotations

from pathlib import Path

from vivado_mcp.bd_summary import parse_bd_summary


def test_parse_bd_summary(tmp_path: Path) -> None:
    path = tmp_path / "bd_summary.tsv"
    path.write_text(
        "\n".join(
            [
                "has_block_design\t1",
                "current_bd_design\tdesign_1",
                "block_design\tC:/work/project/project.srcs/sources_1/bd/design_1/design_1.bd",
                "cell\t/axi_gpio_0\tip\txilinx.com:ip:axi_gpio:2.0",
                "port\t/gpio_tri_o\tO\tdata\t31\t0",
                "interface_port\t/S_AXI\tSlave\txilinx.com:interface:aximm_rtl:1.0",
                "net\t/net_gpio\t/axi_gpio_0/gpio_io_o,/gpio_tri_o",
                "interface_net\t/net_s_axi\t/S_AXI,/axi_gpio_0/S_AXI",
                "validation\t0\t",
            ]
        ),
        encoding="utf-8",
    )

    summary = parse_bd_summary(path)

    assert summary["has_block_design"] is True
    assert summary["current_bd_design"] == "design_1"
    assert summary["cells"] == [{"name": "/axi_gpio_0", "type": "ip", "vlnv": "xilinx.com:ip:axi_gpio:2.0"}]
    assert summary["ports"][0]["name"] == "/gpio_tri_o"
    assert summary["nets"][0]["endpoints"] == ["/axi_gpio_0/gpio_io_o", "/gpio_tri_o"]
    assert summary["validation"] == {"code": 0, "message": ""}
