from __future__ import annotations

import re
import sys
import time
from pathlib import Path


def main() -> int:
    args = sys.argv[1:]
    if "-mode" in args and "batch" in args:
        print("VIVADO_MCP_VERSION=2023.1")
        return 0

    session_dir = _session_dir(args)
    inbox = session_dir / "inbox"
    running = session_dir / "running"
    done = session_dir / "done"
    inbox.mkdir(parents=True, exist_ok=True)
    running.mkdir(parents=True, exist_ok=True)
    done.mkdir(parents=True, exist_ok=True)
    _write_status(session_dir, "idle", "ready")

    deadline = time.time() + 60
    while time.time() < deadline:
        for command in sorted(inbox.glob("*.tcl")):
            target = running / command.name
            command.rename(target)
            _write_status(session_dir, "busy", command.name)
            body = target.read_text(encoding="utf-8", errors="replace")
            result_path = done / f"{target.stem}.result.txt"
            result = _result_for(body)
            result_path.write_text(
                "\n".join(
                    [
                        f"command={target.name}",
                        "started=now",
                        "finished=now",
                        "code=0",
                        f"result={result}",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            _write_status(session_dir, "idle", f"completed {command.name}")
            if "vivado_mcp_bridge_forever" in body:
                return 0
        time.sleep(0.05)
    return 2


def _session_dir(args: list[str]) -> Path:
    if "-tclargs" not in args:
        raise SystemExit("missing -tclargs")
    index = args.index("-tclargs") + 1
    return Path(args[index]).resolve()


def _write_status(session_dir: Path, state: str, detail: str) -> None:
    (session_dir / "status.txt").write_text(f"state={state}\ntime=now\ndetail={detail}\n", encoding="utf-8")


def _result_for(body: str) -> str:
    if "version -short" in body:
        return "version=2023.1"
    if "create_project" in body:
        return "project_created=fake"
    if "open_project" in body:
        return "project_opened=fake"
    bd_summary_match = re.search(r"set mcp_bd_summary_file \{([^}]+)\}", body)
    if bd_summary_match:
        path = Path(bd_summary_match.group(1))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "\n".join(
                [
                    "has_block_design\t1",
                    "current_bd_design\tdesign_1",
                    "block_design\tC:/fake/design_1.bd",
                    "cell\t/axi_gpio_0\tip\txilinx.com:ip:axi_gpio:2.0",
                    "port\t/gpio_tri_o\tO\tdata\t31\t0",
                    "net\t/net_gpio\t/axi_gpio_0/gpio_io_o,/gpio_tri_o",
                    "validation\t0\t",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return f"bd_summary={path}"
    if "bd_actions_applied=" in body or "create_bd_cell" in body:
        return "bd_actions_applied=1 current_bd_design=design_1"
    if "bd_validated=" in body or "validate_bd_design" in body:
        return "bd_validated=design_1"
    if "generate_target" in body:
        return "bd_generated=C:/fake/design_1.bd wrapper=C:/fake/design_1_wrapper.v"
    if "create_bd_design" in body or "open_bd_design" in body:
        return "bd_design=design_1"
    if "launch_runs" in body:
        return "status=complete"
    summary_match = re.search(r"set mcp_summary_file \{([^}]+)\}", body)
    if summary_match:
        path = Path(summary_match.group(1))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "\n".join(
                [
                    "has_project\t1",
                    "current_project\tfake_project",
                    "project_file\tC:/fake/fake_project.xpr",
                    "part\txc7a35tcpg236-1",
                    "top\ttop",
                    "file\tC:/fake/top.v\tVerilog",
                    "run\tsynth_1\tsynth_design Complete!\t100%",
                    "run\timpl_1\tNot started\t0%",
                    "ip\tfake_ip_0",
                    "block_design\tC:/fake/design_1.bd",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return f"summary={path}"
    report_match = re.search(r"-file \{([^}]+)\}", body)
    if report_match:
        path = Path(report_match.group(1))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("FAKE REPORT\nWNS 0.000\n", encoding="utf-8")
        return f"report={path}"
    if "vivado_mcp_bridge_forever" in body:
        return "stopping"
    return "ok"


if __name__ == "__main__":
    raise SystemExit(main())
