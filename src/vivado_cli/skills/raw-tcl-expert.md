# Skill: Raw Tcl Expert Mode

Use this only when the active capability profile is `trusted-local` or `unrestricted`, and the user wants maximum Vivado freedom.

## Normal Flow

1. Run `vivado-cli session state --session <ref>`.
2. Confirm the active profile allows raw Tcl.
3. Run `vivado-cli tcl help <command>` for unfamiliar commands or options.
4. Run `vivado-cli tcl review --file <script.tcl>`, `--stdin`, or `--tcl <text>` on the final snippet before execution.
5. Prefer `vivado-cli session run-tcl --stdin` for multi-line probes, `--tcl` for one-line probes, and `source-tcl` for reusable script files.
6. Pass `--expect-destructive` when review reports destructive, reset, delete, programming, or project-mutating behavior. Use structured hardware commands such as `vivado-cli hw list-debug-cores --expect-hardware-access`, `vivado-cli hw vio-read --expect-hardware-access`, `vivado-cli hw vio-write --expect-hardware-access --expect-vio-write`, `vivado-cli hw capture-ila --expect-hardware-access`, and `vivado-cli hw spi-read --expect-hardware-access` for generic hardware workflows.
7. Prefer structured commands with automatic `state_tracking` for covered workflows; for raw Tcl, capture state manually with summary commands before/after important mutations.
8. Keep commands small enough that failures are easy to isolate.
9. Read the command result artifact, relevant run logs, and project/BD summaries.
10. If the Tcl mutated project state, run `vivado-cli session state` and `vivado-cli project summary` again.

## Notes For AI

- Raw Tcl is effectively local code execution through Vivado.
- Avoid Tcl commands that call external shells unless the user explicitly asks.
- Prefer structured CLI commands when `vivado-cli tools list` shows coverage.
- Use `--stdin` when sending multi-line Tcl through PowerShell or another shell, so quoting and braces are not split by the command line.
- Use `--expect-destructive` for commands that delete, reset runs, or program/erase hardware. Do not use raw Tcl for ILA capture or generic VIO SPI readback when structured hardware commands cover it.
- Use summary/report commands around raw project-mutating Tcl that is not covered by structured commands with automatic state diff.
