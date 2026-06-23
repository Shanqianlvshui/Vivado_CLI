# Skill: Project Build Flow

Use this for ordinary Project Mode FPGA work: create/open a project, add files, run synthesis/implementation, generate reports, and summarize failures.

## Normal Flow

1. Call `vivado_check_installation`.
2. Call `vivado_start_session` with `open_gui=true`.
3. Call `vivado_create_project` or `vivado_open_project`.
4. Call `vivado_project_summary` to inspect project files, runs, IP, and block designs.
5. When resuming a previous session, call `vivado_recovery_brief` first, then `vivado_session_timeline` if you need chronological detail.
6. For complex projects, call `vivado_source_audit` before changing filesets, sources, top modules, or XDC files.
7. For non-trivial changes, call `vivado_capture_state` first or pass `capture_diff=true` to the mutating tool.
8. Call `vivado_add_sources`, `vivado_fileset_apply`, or `vivado_constraint_set_apply` as appropriate.
9. For project IP, use `vivado_ip_catalog_search`, `vivado_create_ip(dry_run=true)` before non-trivial creation, `vivado_describe_ip`, `vivado_ip_upgrade_check`, and `vivado_generate_ip_outputs`. Upgrade only through `vivado_upgrade_ip(expect_upgrade=true)`.
10. For testbench work, use `vivado_simulation_audit`, `vivado_prepare_simulation(dry_run=true)` before non-trivial fileset changes, `vivado_launch_simulation`, and `vivado_analyze_xsim_logs`.
11. For Non-project Mode, use `vivado_nonproject_audit`, dry-run `vivado_nonproject_read_sources` or step tools for non-trivial flows, then run `vivado_nonproject_synth_design`, `vivado_nonproject_opt_design`, `vivado_nonproject_place_design`, and `vivado_nonproject_route_design`.
12. For read-only hardware discovery, use `vivado_hw_discover(expect_hardware_access=true)`; do not program devices through structured tools.
13. Call `vivado_xdc_order_check` before synthesis when constraints changed.
14. Call `vivado_run_synthesis`.
15. If synthesis succeeds, call `vivado_run_implementation`.
16. Call `vivado_analyze_reports` for timing, clock interaction, utilization, DRC, methodology, and power diagnostics; use `quality_gates`, `next_action_plan`, issue IDs, evidence, root-cause hints, and official-doc queries to decide the next action.
17. Use targeted `vivado_report` calls after the aggregate analysis identifies a failure area.

## Notes For AI

- Prefer workflow tools over raw Tcl for repeatable project operations.
- Use `capture_diff=true` on source/fileset/top/property/IP/simulation/run operations when you need a before/after audit trail; inspect `state_diff.summary`, `changes`, and `recommendations`.
- Use `vivado_recovery_brief` before resuming a long-running task; use `vivado_session_timeline` or filtered `vivado_list_artifacts` for details.
- Link raw logs and reports as resources instead of pasting entire logs.
- If a run fails, inspect `vivado_analyze_reports` `quality_gates`, `next_action_plan`, and issue `root_cause_hint` values before retrying.
- If simulation fails, inspect `vivado_analyze_xsim_logs` and `vivado_simulation_audit` before changing RTL or IP.
- If a Non-project step fails, inspect `vivado_nonproject_audit`, its command artifact, prerequisites, and requested reports before rerunning later steps.
- If hardware discovery fails, inspect `vivado_hw_discover` warning rows and verify the hw_server URL or cable target before expert Tcl.
- Fix `timing.unconstrained_paths`, `drc.io_standard_missing`, and `drc.io_pin_unconstrained` before treating implementation strategy as the main problem.
