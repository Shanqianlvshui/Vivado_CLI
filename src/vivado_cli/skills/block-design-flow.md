# Skill: Block Design Flow

Use this when the user wants generic Vivado IP Integrator or block design development.

## Normal Flow

1. Start or reuse a session with `vivado-cli session start` / `vivado-cli session list`.
2. Open the project with `vivado-cli session open-project --session <ref> <project.xpr>`.
3. Inspect the current design with `vivado-cli bd summary --session <ref>`.
4. Validate with `vivado-cli bd validate --session <ref>`.
5. For BD mutations not yet exposed as structured CLI actions, use `vivado-cli tcl help <bd_command>`, `vivado-cli tcl review`, then `vivado-cli session run-tcl` or `source-tcl`.
6. Re-run `vivado-cli bd summary` and `vivado-cli bd validate` after each nontrivial mutation.

## Notes For AI

- Do not assume project-specific module names, board names, IP names, scripts, or directory layouts.
- Prefer `bd_path` when the user identifies a specific `.bd` file.
- Prefer `design_name` when creating a new generic block design.
- Use raw Tcl only when a requested IP Integrator action is not represented by current CLI commands.
