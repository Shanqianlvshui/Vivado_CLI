# Skill: Project Build Flow

Use this for ordinary Project Mode FPGA work: create/open a project, add files, run synthesis/implementation, generate reports, and summarize failures.

## Normal Flow

1. Call `vivado_check_installation`.
2. Call `vivado_start_session` with `open_gui=true`.
3. Call `vivado_create_project` or `vivado_open_project`.
4. Call `vivado_project_summary` to inspect project files, runs, IP, and block designs.
5. For complex projects, call `vivado_source_audit` before changing filesets, sources, top modules, or XDC files.
6. For non-trivial changes, call `vivado_capture_state` first or pass `capture_diff=true` to the mutating tool.
7. Call `vivado_add_sources`, `vivado_fileset_apply`, or `vivado_constraint_set_apply` as appropriate.
8. Call `vivado_xdc_order_check` before synthesis when constraints changed.
9. Call `vivado_run_synthesis`.
10. If synthesis succeeds, call `vivado_run_implementation`.
11. Call `vivado_report` for `timing_summary`, `utilization`, `drc`, and `messages`.

## Notes For AI

- Prefer workflow tools over raw Tcl for repeatable project operations.
- Use `capture_diff=true` on source/fileset/top/property/run operations when you need a before/after audit trail.
- Link raw logs and reports as resources instead of pasting entire logs.
- If a run fails, inspect errors and critical warnings before retrying.
