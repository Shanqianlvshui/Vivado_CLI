# ADR 0002: Support managed GUI Tcl sessions

Status: accepted, amended by ADR 0005

Date: 2026-06-23

## Context

The primary user experience should allow the user to keep Vivado open visually while the CLI operates the same project. AMD documents that Vivado supports Tcl commands through the Tcl shell and IDE Tcl Console. AMD also documents that `start_gui` opens the Vivado IDE from the Tcl shell with the current project, design, and run information. Tcl scripts can be sourced from the IDE, but IDE operations are blocked until the script completes.

There is no documented general-purpose external attach interface that lets an arbitrary external process connect to a manually opened Vivado GUI and inject Tcl commands. Depending on such an interface would make the core product fragile.

## Decision

The preferred interactive mode will be a managed Vivado Tcl session:

```text
vivado-cli -> vivado -mode tcl -source cli_bridge.tcl -> start_gui
```

The CLI owns the Vivado process, but the user sees and can interact with the Vivado GUI. Workflow commands are submitted through a small Tcl bridge loaded inside that Vivado process.

Batch mode remains as a fallback adapter for CI and non-interactive builds.

Attaching to an already-open Vivado GUI is supported only when that GUI session has sourced the CLI bridge and completed a handshake with the CLI session record.

## Consequences

Benefits:

- AI actions and user-visible GUI state refer to the same Vivado process.
- The design avoids GUI click automation.
- The CLI can serialize commands and prevent concurrent state corruption.
- The bridge gives an explicit, auditable control path instead of relying on undocumented process attachment.

Costs:

- The first implementation must manage long-lived process state.
- The bridge has to report busy/idle/error state accurately.
- User GUI actions can still change state between AI commands, so every command must refresh project/session state before acting.
- Batch mode and session mode need shared workflow logic so their behavior does not drift.

Follow-up:

- Prototype the bridge with a file-backed command queue first.
- Measure whether `start_gui` leaves enough Tcl event-loop responsiveness for the bridge on Windows and Linux.
- Add a manual "source bridge in existing GUI" path only after the managed session path is stable.
