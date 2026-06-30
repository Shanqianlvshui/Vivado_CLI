from __future__ import annotations

from pathlib import Path

from vivado_cli.hardware_summary import (
    analyze_ila_csv,
    decode_spi_status,
    parse_debug_cores_tsv,
    parse_hardware_summary,
    parse_spi_read_tsv,
    parse_vio_read_tsv,
    parse_vio_write_tsv,
)


def test_parse_hardware_summary_extracts_targets_devices_and_properties(tmp_path: Path) -> None:
    tsv = tmp_path / "hardware.tsv"
    tsv.write_text(
        "\n".join(
            [
                "server\tlocalhost:3121\tconnected",
                "target\txilinx_tcf/Digilent/123\topen",
                "device\txc7a35t_0\txc7a35tcpg236-1\t0123456789abcdef\t1\tReady",
                "property\txc7a35t_0\tPROGRAM.IS_PROGRAMMED\t1",
                "warning\tno_hw_targets",
                "",
            ]
        ),
        encoding="utf-8",
    )

    parsed = parse_hardware_summary(tsv)

    assert parsed["server_count"] == 1
    assert parsed["target_count"] == 1
    assert parsed["device_count"] == 1
    assert parsed["devices"][0]["programmed"] is True
    assert parsed["properties"][0]["name"] == "PROGRAM.IS_PROGRAMMED"
    assert parsed["warnings"] == ["no_hw_targets"]


def test_parse_debug_cores_tsv_groups_ila_vio_and_probes(tmp_path: Path) -> None:
    tsv = tmp_path / "debug_cores.tsv"
    tsv.write_text(
        "\n".join(
            [
                "core\tila\thw_ila_0\ttop/u_ila_0\txczu19eg_0",
                "probe\tila\thw_ila_0\ttop/sine[13:0]\tIN\t14\tDATA\t0000\t",
                "core\tvio\thw_vio_0\tchip_config/vio_spi_readback\txczu19eg_0",
                "property\tvio\thw_vio_0\tCELL_NAME\tchip_config/vio_spi_readback",
                "probe\tvio\thw_vio_0\tchip_config/spi_read_status\tIN\t29\tDATA\t0D028103\t",
                "",
            ]
        ),
        encoding="utf-8",
    )

    parsed = parse_debug_cores_tsv(tsv)

    assert parsed["core_count"] == 2
    assert parsed["ila_count"] == 1
    assert parsed["vio_count"] == 1
    assert parsed["probe_count"] == 2
    assert parsed["ilas"][0]["probes"][0]["name"] == "top/sine[13:0]"
    assert parsed["ilas"][0]["probes"][0]["width"] == 14
    assert parsed["vios"][0]["cell_name"] == "chip_config/vio_spi_readback"
    assert parsed["vios"][0]["properties"]["CELL_NAME"] == "chip_config/vio_spi_readback"
    assert parsed["vios"][0]["probes"][0]["input_value"] == "0D028103"


def test_parse_vio_read_tsv_decodes_input_and_output_values(tmp_path: Path) -> None:
    tsv = tmp_path / "vio.tsv"
    tsv.write_text(
        "\n".join(
            [
                "meta\tvio\thw_vio_0",
                "probe\t0\thw_vio_0\tchip_config/spi_read_status\tIN\t29\tDATA\t0D028103\t",
                "probe\t1\thw_vio_0\tchip_config/spi_read_req\tOUT\t1\tDATA\t\t0",
                "",
            ]
        ),
        encoding="utf-8",
    )

    parsed = parse_vio_read_tsv(tsv)

    assert parsed["vio"] == "hw_vio_0"
    assert parsed["probe_count"] == 2
    assert parsed["input_probe_count"] == 1
    assert parsed["output_probe_count"] == 1
    assert parsed["probes"][0]["value"] == "0D028103"
    assert parsed["probes"][0]["decoded_int"] == int("0D028103", 16)
    assert parsed["probes"][1]["value"] == "0"
    assert parsed["probes"][1]["decoded_int"] == 0


def test_parse_vio_write_tsv_decodes_before_and_after_values(tmp_path: Path) -> None:
    tsv = tmp_path / "vio_write.tsv"
    tsv.write_text(
        "\n".join(
            [
                "meta\tvio\thw_vio_0",
                "write\t0\thw_vio_0\tchip_config/spi_read_req\tOUT\t1\t1\t0\t1\tok",
                "",
            ]
        ),
        encoding="utf-8",
    )

    parsed = parse_vio_write_tsv(tsv)

    assert parsed["vio"] == "hw_vio_0"
    assert parsed["write_count"] == 1
    assert parsed["write_ok_count"] == 1
    assert parsed["all_write_ok"] is True
    write = parsed["writes"][0]
    assert write["requested_value"] == "1"
    assert write["before_value"] == "0"
    assert write["after_value"] == "1"
    assert write["requested_value_int"] == 1
    assert write["before_value_int"] == 0
    assert write["after_value_int"] == 1


def test_analyze_ila_csv_uses_radix_and_adc14_signed_values(tmp_path: Path) -> None:
    csv_path = tmp_path / "capture.csv"
    csv_path.write_text(
        "\n".join(
            [
                "Sample in Buffer,Sample in Window,TRIGGER,top/sine[13:0],top/valid",
                "Radix - UNSIGNED,UNSIGNED,UNSIGNED,HEX,UNSIGNED",
                "0,0,1,0000,1",
                "1,1,0,0064,1",
                "2,2,0,0000,1",
                "3,3,0,3f9c,1",
                "4,4,0,0000,1",
                "5,5,0,0064,1",
                "6,6,0,0000,1",
                "7,7,0,3f9c,1",
                "",
            ]
        ),
        encoding="utf-8",
    )

    analysis = analyze_ila_csv(csv_path, mode="adc14", sample_rate_hz=80.0)

    sine = analysis["signals"]["top/sine[13:0]"]
    assert analysis["row_count"] == 8
    assert sine["min"] == -100
    assert sine["max"] == 100
    assert sine["p2p"] == 200
    assert sine["peak_bin"] == 2
    assert sine["peak_frequency_hz"] == 20.0
    assert sine["near_clip"] is False
    assert analysis["signals"]["top/valid"]["unique_values"] == [1]


def test_parse_spi_read_tsv_decodes_default_status_layout(tmp_path: Path) -> None:
    tsv = tmp_path / "spi.tsv"
    tsv.write_text(
        "\n".join(
            [
                "meta\tvio\thw_vio_0",
                "read\t0\t2\t0x0281\t0D028103\t3\t0",
                "",
            ]
        ),
        encoding="utf-8",
    )

    parsed = parse_spi_read_tsv(tsv)

    assert parsed["all_read_ok"] is True
    read = parsed["reads"][0]
    assert read["read_ok"] is True
    assert read["requested_target"] == 2
    assert read["requested_addr"] == 0x0281
    assert read["data"] == 0x03
    assert read["data_hex"] == "0x03"
    assert read["last_target"] == 2
    assert read["last_addr"] == 0x0281
    assert read["done"] is True
    assert read["busy"] is False
    assert read["enable"] is True
    assert read["error"] is False


def test_decode_spi_status_reports_failure_relevant_fields() -> None:
    decoded = decode_spi_status("02000002")

    assert decoded["data"] == 0x02
    assert decoded["busy"] is True
    assert decoded["done"] is False
