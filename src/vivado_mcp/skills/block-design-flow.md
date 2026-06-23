# Skill: Block Design Flow

Use this when the user wants generic Vivado IP Integrator or block design development.

## Normal Flow

1. Call `vivado_start_session`.
2. Open or create a project with `vivado_open_project` or `vivado_create_project`.
3. Call `vivado_bd_open_or_create` with a generic `design_name` or `bd_path`.
4. Call `vivado_bd_summary` to inspect cells, ports, interfaces, nets, and validation state.
5. Call `vivado_bd_apply` with generic actions such as `create_cell`, `create_port`, `connect_net`, `set_property`, `apply_automation`, `validate`, or `save`.
6. Call `vivado_bd_validate`.
7. Call `vivado_bd_generate` to generate output products and optionally add an HDL wrapper.

## Notes For AI

- Do not assume project-specific module names, board names, IP names, scripts, or directory layouts.
- Prefer `bd_path` when the user identifies a specific `.bd` file.
- Prefer `design_name` when creating a new generic block design.
- Use `vivado_bd_summary` after each nontrivial mutation so later actions operate on current Vivado state.
- Use raw Tcl only when a requested IP Integrator action is not represented by `vivado_bd_apply`.
