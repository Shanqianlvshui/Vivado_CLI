# Skill: Fileset, Source, and Constraint Workflow

Use this whenever the active project is more complex than a single
`sources_1` / `constrs_1` pair, or when XDC loading order, USED_IN scopes,
or USED_IN conflicts are blocking a build.

## Preconditions

- A managed Vivado session is running and the active project is open.
- Files and directories you intend to add are under allowed workspace roots.
- For XDC work, the current `constrs_1` already exists (Vivado creates it
  on `create_project`).

## Normal Flow

1. Call `vivado_list_filesets` to see every fileset in the project with
   type, file count, USED_IN flags, and top.
2. Call `vivado_describe_fileset(name="...")` for the fileset you intend
   to mutate. Verify the existing file list, library assignments, and
   processing order.
3. For an extra constraint set, call
   `vivado_create_fileset(name="constrs_extra", kind="constrs")`.
4. Add or move files with `vivado_add_sources`. Use
   `sources_fileset="sources_2"` (or your custom name) when adding to a
   non-default fileset. Use `include_dirs` and `defines` to attach search
   paths and Verilog/VHDL macros at the fileset level rather than per file.
5. Override per-file properties (LIBRARY, PROCESSING_ORDER, USED_IN_*) via
   `vivado_set_file_properties`. Always pass `fileset="..."` when the same
   file is included by more than one fileset so the right scope is updated.
6. Confirm or change the top with `vivado_set_top(top="alu",
   fileset="sources_1")`. Pass `top=None` to read the current value.
7. Before building, call `vivado_constraint_diagnostics`. Check
   `constrs_filesets`, `constraint_files` (in loading order), `xdc_markers`,
   and `warnings`. Resolve any `no_create_clock_but_has_input_delay` or
   similar warnings before synthesis — they are early hints for real timing
   issues.
8. Run `vivado_run_synthesis`. If timing fails, return to step 7 and
   re-audit after editing the XDC files.

## Removing Files

- `vivado_remove_sources(paths=[...], fileset="...")` removes the listed
  files from one fileset. Pass `force=True` if Vivado complains about
  in-use files. This is destructive; the AI should call
  `vivado_review_tcl` first if the call list is unusual.

## Notes For AI

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
  commands work, but `IS_DEFAULT_FILESET` becomes load-bearing — do not
  change it without re-reading UG909.

## Common Problems

- `xdc_load_order_unknown`: call `vivado_constraint_diagnostics` and
  confirm the `constraint_files` ordering inside `constrs_1`.
- `top_not_found`: call `vivado_describe_fileset(name="sources_1")` and
  confirm the `TOP` property and the file list.
- `multiple_library_assignment`: set `LIBRARY` explicitly with
  `vivado_set_file_properties(fileset="...")` rather than letting Vivado
  auto-assign from the file extension.
- `define_not_in_effect`: use `vivado_add_sources(defines=[...])` instead
  of inline `+define+` flags; the property is read at elaboration.
