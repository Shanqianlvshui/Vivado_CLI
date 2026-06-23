# Skill: Block Design Flow

Use this when the user wants generic Vivado IP Integrator or block design development.

## Preconditions

- A managed Vivado session exists.
- A project is open or will be created before creating a block design.
- The caller does not assume any project-specific script layout, module naming convention, board preset, or IP catalog selection.

## Normal Flow

1. Call `vivado_start_session`.
2. Open or create a project with `vivado_open_project` or `vivado_create_project`.
3. Call `vivado_bd_open_or_create` with `design_name` or `bd_path`.
4. Call `vivado_bd_summary` and `vivado_bd_audit` to inspect cells, ports, interfaces, nets, validation state, connectivity, and address issues.
5. Call `vivado_bd_apply(dry_run=true)` before nontrivial generic actions such as `create_cell`, `create_port`, `connect_net`, `connect_interface_net`, `set_property`, `apply_automation`, `assign_address`, `validate`, or `save`.
6. Call `vivado_bd_apply` for the accepted plan, then `vivado_bd_validate` to parse BD diagnostics.
7. Call `vivado_bd_generate` to generate output products and optionally add an HDL wrapper.

## Notes For AI

- Never infer project-specific names from a prior unrelated project.
- Prefer `bd_path` when the user identifies a specific `.bd` file.
- Prefer `design_name` when creating a new generic block design.
- Use `vivado_bd_audit` and `vivado_bd_summary` after each nontrivial mutation so later actions operate on current Vivado state.
- Use raw Tcl only when a requested IP Integrator action is not represented by `vivado_bd_apply`.
