# ADR 0004: Provide built-in help and skills

Status: accepted

Date: 2026-06-23

## Context

Vivado is large, and the MCP server exposes both safe workflow tools and high-freedom raw Tcl tools. AI clients need guidance about which tool to call, in what order, and what to inspect after failures. Relying only on external documentation would make the MCP harder to use and more error-prone.

MCP supports tools for model-controlled actions and resources for application-controlled context. Help content fits naturally as resources, while discovery and recommendation fit naturally as tools.

## Decision

The server will include a built-in help/skills system.

Initial tools:

- `vivado_help`
- `vivado_list_skills`
- `vivado_get_skill`
- `vivado_suggest_next_steps`

Initial resources:

- `vivado://help/index`
- `vivado://skills/index`
- `vivado://skills/gui-session`
- `vivado://skills/project-build-flow`
- `vivado://skills/raw-tcl-expert`

The help system should be available in every capability profile, including `safe`.

## Consequences

Benefits:

- AI clients can learn the intended workflows before operating Vivado.
- The MCP can steer models toward safer workflow tools while still documenting expert raw Tcl mode.
- Tutorials can evolve without changing the core tool interface.

Costs:

- The help content must be maintained alongside tool behavior.
- The server needs tests that resource IDs and skill IDs stay valid.

Follow-up:

- Keep skill docs concise and task-oriented.
- Add examples from real Vivado failures as the project matures.
- Let users add workspace-local custom skills later.
