"""Commit and push the current staged working tree."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(r"C:\Workspace\Vivado_mcp")
COMMIT_MSG = """Add vivado_tcl_command_help and vivado_review_tcl expert-mode safety layer

New cross-cutting tools that combine local UG835 search, optional installed
Vivado help, MCP coverage guidance, and destructive-command risk review for
the raw-Tcl expert path:

- vivado_tcl_command_help: inputs a command name, returns official-doc
  snippets, current Vivado help text (when a session is attached), and a
  coverage verdict that tells the AI whether to use a structured MCP tool
  or fall back to expert Tcl.
- vivado_review_tcl: scans a Tcl snippet for destructive, hardware-affecting,
  or project-resetting patterns (exit/exec, file delete, reset_*,
  delete_*, program_hw_*, open_hw_*, -force, source, set_param) and reports
  risk level, expect_destructive recommendation, and the AMD documents
  to read first (UG835, UG894, UG906, UG949, UG908, UG994, UG912).

Also wires the two tools into help_topic("raw-tcl"), suggest_next_steps, the
official-docs and raw-tcl-expert skill docs, the README flow, and the MCP
protocol smoke test. Adds a fake-vivado help {cmd} mock so the session
helper for installed help is exercised in unit tests.

41 tests pass.
"""


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    print("$", " ".join(cmd), flush=True)
    completed = subprocess.run(
        cmd,
        cwd=str(REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        **kwargs,
    )
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    print(f"(rc={completed.returncode})", flush=True)
    return completed


def main() -> int:
    status = run(["git", "status", "--short"])
    if status.returncode != 0:
        return status.returncode

    commit = run(["git", "commit", "-m", COMMIT_MSG])
    if commit.returncode != 0:
        return commit.returncode

    push = run(["git", "push"])
    return push.returncode


if __name__ == "__main__":
    raise SystemExit(main())
