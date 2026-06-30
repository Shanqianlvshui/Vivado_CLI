# ADR 0005: Remove MCP adapter and standardize on CLI

Status: accepted

Date: 2026-06-24

## Context

The project started as an MCP server, but the practical control path for Vivado
is a local CLI that generates Tcl, owns session artifacts, and talks to a small
Tcl bridge inside Vivado. Keeping MCP as an optional adapter created confusing
architecture and naming: callers could not tell whether the tool was an MCP
server, a CLI, or a Tcl wrapper.

Vivado itself is controlled through Tcl. The durable product boundary should
therefore be the CLI command surface plus generated Tcl artifacts, not an AI
protocol adapter.

## Decision

Remove MCP as a supported runtime surface. The project exposes:

- `vivado-cli` as the only installed command.
- `src/vivado_cli` as the Python package.
- `cli_bridge.tcl` as the managed Vivado process bridge.
- JSON output for both human scripts and AI agents.

No `mcp` dependency, optional extra, console script, MCP server module, MCP
protocol test, or MCP client configuration is retained.

## Consequences

Benefits:

- The architecture is simpler: CLI -> Tcl bridge -> Vivado Tcl.
- Tests no longer require an MCP SDK dependency.
- Future features can focus on state diff, job control, BD/IP/fileset tools,
  and report diagnosis without maintaining protocol adapter parity.
- AI clients can still invoke the CLI as a normal local tool.

Costs:

- MCP-native clients no longer get tool/resource discovery from this package.
- Help and artifact discovery must be represented as CLI JSON commands.

Follow-up:

- Rename remaining internal helper variables that still use historical `mcp_*`
  Tcl names where it can be done without destabilizing generated Tcl parsers.
- Replace legacy design docs with a CLI-specific design document.
- Add async job commands for long Vivado runs so the CLI does not block on
  `wait_on_run`.
