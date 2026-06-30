# ADR 0003: Support trusted-local raw Tcl

Status: accepted, amended by ADR 0005

Date: 2026-06-23

## Context

The user wants maximum freedom for Vivado automation. Workflow-level commands are useful for common operations, but Vivado has a large Tcl surface area and many project-specific flows. Mirroring every Vivado Tcl command as a separate CLI command would create a shallow, incomplete interface.

Experiments on this machine showed that a small Tcl bridge loaded inside Vivado can execute externally submitted Tcl command files in both headless Tcl mode and GUI-visible mode.

## Decision

The CLI will support capability profiles:

- `safe`: workflow tools only.
- `trusted-local`: workflow tools plus raw Tcl execution in a managed Vivado session.
- `unrestricted`: minimal guardrails for personal experimentation.

The first raw Tcl tools are:

- `vivado_run_tcl`
- `vivado_source_tcl`

Both require a managed session. Every command must be written to an artifact before execution, and every result must be written to an artifact after execution when Vivado remains alive.

## Consequences

Benefits:

- The CLI can cover the full Vivado Tcl surface without designing hundreds of shallow commands.
- Advanced users can run project-specific Tcl flows through the same visible GUI session.
- The CLI still records command history and results.

Costs:

- Raw Tcl is effectively local code execution through Vivado.
- Some operations can mutate files, projects, IP, or tool settings in ways workflow tools cannot predict.
- Result handling is best-effort if the raw Tcl command exits Vivado or crashes the process.

Follow-up:

- Implement `trusted-local` first.
- Make the active capability profile visible in `vivado_session_state`.
- Keep workflow tools as the recommended path for repeatable operations.
