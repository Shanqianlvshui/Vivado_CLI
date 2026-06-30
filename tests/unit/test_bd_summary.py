from __future__ import annotations

from pathlib import Path

from vivado_cli.bd_summary import analyze_bd_audit, parse_bd_summary, parse_bd_validate_result


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
    assert summary["validation"]["code"] == 0
    assert summary["validation"]["message"] == ""
    assert summary["validation"]["ok"] is True


def test_bd_audit_flags_validation_and_unconnected_objects() -> None:
    summary = {
        "has_block_design": True,
        "current_bd_design": "design_1",
        "ports": [{"name": "/clk", "type": "clk"}],
        "interface_ports": [{"name": "/S_AXI", "mode": "Slave"}],
        "nets": [{"name": "/clk_net", "endpoints": ["/clk"]}],
        "interface_nets": [],
        "validation": {
            "code": 1,
            "message": "ERROR: [BD 41-1356] Slave segment is not assigned into address space\nWARNING: [BD 41-759] pin is not connected",
        },
    }

    audit = analyze_bd_audit(summary)

    assert audit["ok"] is False
    issue_ids = {issue["issue_id"] for issue in audit["issues"]}
    assert {"bd.validation_failed", "bd.address_unassigned", "bd.connection_missing", "bd.interface_port_unconnected"} <= issue_ids
    assert audit["recommendations"][0]["tool"] == "vivado_bd_validate"


def test_parse_bd_validate_result_returns_structured_issues() -> None:
    result = "ERROR: [BD 41-758] Port is not connected\nWARNING: [BD 41-1356] Address segment is not assigned"

    parsed = parse_bd_validate_result(result)

    assert parsed["ok"] is False
    assert parsed["issue_count"] == 2
    assert parsed["issues"][0]["code"] == "BD 41-758"
    assert {issue["issue_id"] for issue in parsed["issues"]} == {"bd.connection_missing", "bd.address_unassigned"}
