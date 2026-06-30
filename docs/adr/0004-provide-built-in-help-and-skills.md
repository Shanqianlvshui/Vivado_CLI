# ADR 0004: Provide built-in help and skills

Status: accepted, amended by ADR 0005

Date: 2026-06-23

## Context

Vivado is large, and the CLI exposes both safe workflow commands and high-freedom raw Tcl commands. AI clients and human scripts need guidance about which command to call, in what order, and what to inspect after failures. Relying only on external documentation would make the CLI harder to use and more error-prone.

ADR 0005 removed MCP resources, so help content is now exposed through CLI JSON/text commands instead of MCP resources.

## Decision

The CLI will include a built-in help/skills system.

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
- The CLI can steer callers toward safer workflow commands while still documenting expert raw Tcl mode.
- Tutorials can evolve without changing the core tool interface.

Costs:

- The help content must be maintained alongside tool behavior.
- The CLI needs tests that help topics and skill IDs stay valid.

Follow-up:

- Keep skill docs concise and task-oriented.
- Add examples from real Vivado failures as the project matures.
- Let users add workspace-local custom skills later.
