# Skill: Raw Tcl Expert Mode

Use this only when the active capability profile is `trusted-local` or `unrestricted`, and the user wants maximum Vivado freedom.

## Preconditions

- A managed Vivado session is running.
- The bridge is idle.
- The active capability profile allows raw Tcl.
- The command has been written as a clear, auditable Tcl snippet or source file.

## Normal Flow

1. Call `vivado_session_state`.
2. Confirm the active profile allows raw Tcl.
3. Call `vivado_tcl_command_help` for unfamiliar commands or options.
4. Call `vivado_review_tcl` on the final snippet before execution.
5. Prefer `vivado_source_tcl` for longer scripts and `vivado_run_tcl` for short probes.
6. Set `expect_destructive=true` when `vivado_review_tcl` reports destructive, overwrite, reset, delete, or hardware-affecting behavior.
7. Keep commands small enough that failures are easy to isolate.
8. Read the command result artifact and relevant log resource.
9. If the Tcl mutated project state, call `vivado_session_state` again.

## Notes For AI

- Raw Tcl is effectively local code execution through Vivado.
- Never hide that risk from the user.
- Avoid Tcl commands that call external shells unless the user explicitly asks.
- Prefer structured MCP tools when `vivado_tcl_command_help` says the command is covered.
- Use `expect_destructive=true` for commands that delete, overwrite, reset runs, or modify hardware/programming state.
- Prefer introspection commands before mutation, such as `get_projects`, `current_project`, `get_files`, `get_runs`, and `report_property`.

## Common Problems

- A raw Tcl script can call `exit`; if it does, the bridge may not write a normal result artifact.
- Long-running Tcl commands should use a timeout.
- GUI and AI actions can race; refresh state before and after raw Tcl.
