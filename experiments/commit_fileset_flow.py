"""Commit and push the fileset / source / constraint workflow changes."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(r"C:\Workspace\Vivado_mcp")
COMMIT_MSG = """Add fileset, source, and constraint workflow tools

Closes the highest-friction gap in the prior project build flow: complex
projects that need more than a single sources_1 / constrs_1 pair, files
attached to non-default filesets, USED_IN scopes, custom libraries and
include directories, explicit top selection, and a real XDC order /
scope audit before synthesis.

New tools (and the manager methods behind them):

- vivado_list_filesets: list every fileset with type, file_count,
  USED_IN flags, top, and is_default.
- vivado_create_fileset: create a new fileset (constrs | simulation |
  Source | BlockSrcs) for a non-default constraint or RTL set.
- vivado_describe_fileset: return one fileset's files, library, library
  assignment, processing order, and USED_IN flags in a structured dict.
- vivado_add_sources: extend the existing API with sources_fileset,
  include_dirs, defines, library, file_type, used_in, and
  processing_order. All new options are optional and stay backward
  compatible.
- vivado_remove_sources: scoped remove_files with an explicit
  expect_destructive flag in the result.
- vivado_set_file_properties: set FILE_TYPE / LIBRARY / PROCESSING_ORDER
  / USED_IN_* scoped to a fileset when the same file lives in several.
- vivado_set_top: read or write the top module for a fileset; pass
  top=None to query without mutating.
- vivado_constraint_diagnostics: TSV-driven audit that lists every
  Constrs fileset, its XDC files in loading order, the USED_IN scopes,
  and UG903/UG949 methodology markers (create_clock,
  set_input_delay, set_false_path, set_clock_groups, get_ports) with
  warnings for obviously broken combinations.

Internal: tcl.py gains list_filesets_tcl, create_fileset_tcl,
describe_fileset_tcl, remove_files_tcl, set_file_properties_tcl,
set_top_tcl, constraint_diagnostics_tcl. New fileset_summary.py
parses the TSV outputs into structured dicts. fake_vivado.py gets
mocks for the new commands so the manager methods can be exercised
end-to-end through the existing fake-bat bridge.

Documentation: new seed skill fileset-constraint-flow.md (one in
docs/skills and one in src/vivado_mcp/skills), and project-build-flow.md
grows steps 5 and 9 that route the AI through list_filesets /
describe_fileset / set_top / set_file_properties / constraint_diagnostics
for non-trivial projects. README "Implemented Tools" and "Initial scope"
sections list the new tools.

45 tests pass (4 new: 3 parser tests in test_fileset_summary.py and
one end-to-end test that exercises list_filesets -> create_fileset ->
describe_fileset -> add_sources -> set_file_properties -> set_top ->
remove_sources -> constraint_diagnostics through the fake Vivado
bridge).
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
    add = run(["git", "add", "-A"])
    if add.returncode != 0:
        return add.returncode
    commit = run(["git", "commit", "-m", COMMIT_MSG])
    if commit.returncode != 0:
        return commit.returncode
    push = run(["git", "push"])
    return push.returncode


if __name__ == "__main__":
    raise SystemExit(main())
