# ADR 0001: Control Vivado through Tcl batch mode

Status: amended by ADR 0002

Date: 2026-06-23

## Context

The project needs an MCP server that allows AI clients to operate AMD Vivado. Vivado can be operated through its GUI, Tcl shell, batch scripts, Project Mode, and Non-Project Mode. The MCP interface must be predictable, auditable, testable, and safe enough for local automation.

AMD documentation describes Vivado Tcl as the interface for controlling the tools and design data. Vivado flows can be developed through Tcl commands or batch scripts. Project Mode provides run infrastructure and source management; Non-Project Mode provides full manual flow control but requires the caller to manage reports, checkpoints, and reruns.

## Decision

Batch-mode automation will control Vivado by generating validated Tcl scripts and running:

```text
vivado -mode batch -source <generated-script.tcl>
```

Project Mode remains the first workflow target. Non-Project Mode will be added later as an internal adapter for scripted flows.

The MCP server will expose workflow-level tools, not a one-to-one mirror of Vivado Tcl commands.

ADR 0002 changes the primary user experience: the first interactive mode is now a managed Tcl session that can open the GUI with `start_gui`. Batch mode remains a fallback and CI adapter.

## Consequences

Benefits:

- Tool calls are auditable because every Vivado action has a generated Tcl artifact.
- The server can validate inputs before Tcl is generated.
- The AI-facing interface stays small.
- The implementation can use Vivado's documented run infrastructure.
- Tests can use a fake Vivado executable without requiring Vivado for every unit test.

Costs:

- Starting Vivado for each batch operation is slower than a managed session.
- Batch operation does not provide the primary "user watches GUI while AI acts" experience.
- Advanced Tcl users may initially miss a raw Tcl escape hatch.

Follow-up:

- Implement managed GUI Tcl sessions as described in ADR 0002.
- Revisit hardware manager support only after a separate safety design.
