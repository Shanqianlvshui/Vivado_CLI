from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIVADO = Path(r"C:\Xilinx\Vivado\2023.1\bin\vivado.bat")
BRIDGE = ROOT / "experiments" / "mcp_bridge.tcl"


def wait_for(path: Path, timeout_s: float) -> str:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if path.exists():
            return path.read_text(errors="replace")
        time.sleep(0.1)
    raise TimeoutError(f"Timed out waiting for {path}")


def write_command(session: Path, name: str, body: str) -> Path:
    inbox = session / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    command = inbox / name
    command.write_text(body, encoding="utf-8")
    return command


def main() -> int:
    open_gui = "--gui" in sys.argv[1:]
    mode_gui = "--mode-gui" in sys.argv[1:]
    session_name = ".vivado_mcp_session_smoke_headless"
    if open_gui:
        session_name = ".vivado_mcp_session_smoke_start_gui"
    if mode_gui:
        session_name = ".vivado_mcp_session_smoke_mode_gui"
    session = ROOT / session_name

    if session.exists():
        shutil.rmtree(session)
    session.mkdir(parents=True)

    command = [
        "cmd",
        "/c",
        str(VIVADO),
        "-mode",
        "gui" if mode_gui else "tcl",
        "-source",
        str(BRIDGE),
        "-tclargs",
        str(session),
    ]
    if open_gui and not mode_gui:
        command.append("--gui")

    proc = subprocess.Popen(
        command,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    try:
        status = wait_for(session / "status.txt", 25)
        if "state=idle" not in status:
            time.sleep(1)
            status = (session / "status.txt").read_text(errors="replace")
        print("STATUS:")
        print(status.strip())

        write_command(
            session,
            "001_probe.tcl",
            "\n".join(
                [
                    'puts "MCP_RAW_TCL_PROBE"',
                    'set ::mcp_probe_version [version -short]',
                    'return "version=$::mcp_probe_version"',
                ]
            ),
        )
        result = wait_for(session / "done" / "001_probe.result.txt", 25)
        print("RESULT:")
        print(result.strip())

        write_command(session, "999_exit.tcl", "catch { stop_gui }\nset ::vivado_mcp_bridge_forever 1\nreturn \"stopping\"\n")
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.terminate()
            proc.wait(timeout=10)
        print(f"PROCESS_EXIT={proc.returncode}")
        return 0 if "code=0" in result and "version=2023.1" in result else 1
    finally:
        if proc.poll() is None:
            proc.terminate()


if __name__ == "__main__":
    sys.exit(main())
