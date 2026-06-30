# Vivado CLI Design

Status: current

Date: 2026-06-24

## Goal

Provide a local CLI that controls AMD Vivado through documented Tcl flows while
keeping long-running GUI sessions usable and auditable.

## Architecture

```text
vivado-cli
  -> Python CLI core
  -> .vivado_cli/sessions/<session_ref>/inbox/*.tcl
  -> cli_bridge.tcl loaded inside Vivado
  -> Vivado Tcl/project/BD/run state
  -> result, report, summary, snapshot artifacts
```

The CLI is the product boundary. MCP is not part of the supported runtime
surface.

## Core Modules

- `vivado_cli.cli`: argparse entry point and JSON output.
- `vivado_cli.cli_core`: file-backed persistent session operations.
- `vivado_cli.assets.cli_bridge.tcl`: Vivado-side Tcl queue processor.
- `vivado_cli.tcl`: generated Vivado Tcl snippets.
- `vivado_cli.tcl_assist`: Tcl risk review and command routing.
- `vivado_cli.official_docs`: AMD documentation metadata and local PDF search.
- Summary/parser modules: project, fileset, constraints, IP, BD, simulation,
  reports, hardware, Non-project flow, and state diff.

## Session Model

Each session has a record under:

```text
.vivado_cli/sessions/<session_ref>/session.json
```

The session directory also stores command files, results, reports, summaries,
snapshots, and diffs. A separate CLI invocation can reuse the session by passing
`--workspace` and `--session`.

## Safety Model

Capability profiles:

- `safe`: workflow commands only.
- `trusted-local`: workflow commands plus reviewed raw Tcl.
- `unrestricted`: minimal path policy for local experimentation.

Expert Tcl should run through `tcl review` before execution. Destructive or
hardware-affecting commands require explicit `--expect-destructive` when run.

## Run Control

Project runs are controlled through asynchronous CLI commands:

- `run status` reads current run status without changing the project.
- `run launch` submits `launch_runs` and returns immediately after Vivado
  accepts the run; it does not emit `wait_on_run`.
- `run launch-local` starts Vivado's generated run script, such as `runme.bat`,
  when the IDE run manager leaves a run queued without a worker process. If the
  script is missing after `reset_run`, it first prepares the run with
  `launch_runs`, honoring `--jobs` and `--to-step`.
- `run diagnose` combines Vivado run properties with run-directory evidence
  such as queue markers and logs, and flags missing IP/OOC DCP files found in
  recent logs.
- `run logs` returns a bounded tail of `runme.log` or another selected run log.
- `run reset` wraps `reset_run` and requires `--expect-destructive`.

## Design Rules

- Prefer structured CLI commands when they cover the task.
- Use generated Tcl artifacts for all Vivado mutations.
- Avoid GUI click automation; the GUI is a visible state surface.
- Keep long Vivado runs asynchronous where possible.
- Refresh summaries after mutations so resumed work starts from evidence.
