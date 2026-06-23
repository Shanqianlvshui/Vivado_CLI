# Skill: Fileset, Source, and Constraint Workflow

Use this whenever the active project is more complex than a single
`sources_1` / `constrs_1` pair, or when XDC loading order, USED_IN scopes,
top selection, include directories, defines, or library assignments are
blocking a build.

## Preconditions

- A managed Vivado session is running and the active project is open.
- Files and directories you intend to add are under allowed workspace roots.
- For XDC work, the current `constrs_1` usually already exists. Additional
  constraint sets can be created through `vivado_constraint_set_apply`.

## Normal Flow

1. Call `vivado_source_audit` first. It combines project summary, fileset
   summaries, and constraint diagnostics, then flags missing tops, duplicate
   files, disabled source scopes, misplaced XDC files, and missing clock
   markers.
2. Call `vivado_list_filesets` and `vivado_describe_fileset(name="...")`
   when the audit points at a specific source, simulation, or constraint
   fileset. Verify file list, library assignments, properties, and processing
   order before mutating anything.
3. Add or move source/XDC files with `vivado_add_sources`. Use
   `sources_fileset="sources_2"` or another custom name when adding to a
   non-default fileset.
4. Apply source-fileset settings with `vivado_fileset_apply`. Use it for
   include directories, defines, top module, and fileset-level properties.
   Pass `dry_run=true` first on complex projects, then `capture_diff=true`
   when applying anything that changes project state.
5. Apply constraint-set changes with `vivado_constraint_set_apply`. Use it
   to create extra constraint sets, add/remove XDC files, set USED_IN scopes,
   reorder XDC loading order, and make a constraint set active. Pass
   `dry_run=true` to review the plan and `capture_diff=true` for
   before/after summary and diff artifacts.
6. For per-file overrides that are not covered by the structured apply tools,
   call `vivado_set_file_properties`. Always pass `fileset="..."` when the
   same file is included by more than one fileset so the right scope is
   updated.
7. Before building, call `vivado_xdc_order_check`. It reports XDC files in
   loading order and flags false paths, clock groups, and I/O delay
   constraints that appear before any clock definition in the same set. Use
   its `reorder_plan` and `actions` as the draft for
   `vivado_constraint_set_apply`.
8. If you need the raw evidence, call `vivado_constraint_diagnostics` and
   inspect `constrs_filesets`, `constraint_files`, `xdc_markers`,
   `xdc_file_markers`, and `warnings`.
9. Run `vivado_run_synthesis`. If timing fails, return to the audit and XDC
   order checks before editing constraints again.

## Removing Files

- `vivado_remove_sources(paths=[...], fileset="...")` removes the listed
  files from one fileset. Pass `force=True` if Vivado complains about
  in-use files. This is destructive; the AI should call `vivado_review_tcl`
  first if the call list is unusual.

## Notes For AI

- Prefer `vivado_fileset_apply` and `vivado_constraint_set_apply` over raw
  Tcl for source and constraint setup. Use expert Tcl only when the
  structured tools do not cover the operation.
- Use dry-run plans before applying broad include/define/top or XDC reorder
  changes. A dry run validates paths and returns the intended structured
  actions without executing Tcl.
- Vivado evaluates constraint fileset USED_IN flags before XDC processing
  order matters. Check that every constraint set has
  `IS_ENABLED_IMPLEMENTATION=1` when implementation is failing on a
  constraint that looks correct on paper.
- Library assignment (VHDL `work` / Verilog `xil_defaultlib`) is read at
  elaboration time, not at synthesis. Changing `LIBRARY` after synthesis
  has no effect on the current run.
- Do not assume every XDC issue surfaces in `report_timing_summary`. For
  cross-clock and inter-block constraint questions, use
  `report_clock_interaction` after the run and re-evaluate USED_IN scopes.
- For custom DFX or partial-reconfiguration flows, the same fileset
  commands work, but `IS_DEFAULT_FILESET` becomes load-bearing. Do not
  change it without re-reading UG909.

## Common Problems

- `xdc_load_order_unknown`: call `vivado_xdc_order_check`, then confirm the
  raw `constraint_files` ordering with `vivado_constraint_diagnostics`.
- `top_not_found`: call `vivado_source_audit` and
  `vivado_describe_fileset(name="sources_1")`, then fix the fileset top with
  `vivado_fileset_apply`.
- `multiple_library_assignment`: set `LIBRARY` explicitly with
  `vivado_set_file_properties(fileset="...")` rather than letting Vivado
  auto-assign from the file extension.
- `define_not_in_effect`: use `vivado_fileset_apply(defines=[...])` instead
  of inline `+define+` flags; the property is read at elaboration.
