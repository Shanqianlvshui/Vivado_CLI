# Skill: Fileset, Source, and Constraint Workflow

Use this whenever the active project is more complex than a single
`sources_1` / `constrs_1` pair, or when XDC loading order, USED_IN scopes,
top selection, include directories, defines, or library assignments are
blocking a build.

## Preconditions

- A managed Vivado session is running and the active project is open.
- Files and directories you intend to add are under allowed workspace roots.
- For XDC work, the current `constrs_1` usually already exists. Additional
  constraint sets can be created or updated with `vivado-cli constraint apply`.

## Normal Flow

1. Run `vivado-cli project summary --session <ref>` first to inspect active project and runs.
2. Run `vivado-cli fileset list --session <ref>` and `vivado-cli fileset describe --session <ref> <fileset>` before mutating source membership or properties.
3. Use `vivado-cli fileset add-files`, `vivado-cli fileset apply`, `vivado-cli fileset set-file-properties`, and `vivado-cli fileset set-top` for common source/top/include/define/library work.
4. Use `vivado-cli constraint diagnostics`, `vivado-cli constraint check-order`, and `vivado-cli constraint apply` for XDC set membership, USED_IN scopes, active constraint set, and XDC order.
5. Run `vivado-cli tcl help <command>` and `vivado-cli tcl review` only for uncommon options not covered by structured commands.
6. Re-run `vivado-cli project summary`, `vivado-cli fileset describe`, and `vivado-cli constraint check-order` after mutation.
7. If timing fails, inspect reports with `vivado-cli report` before editing constraints again.

## State Tracking

- Structured mutating fileset and constraint commands attach `state_tracking` and `state_diff` by default.
- Use the diff artifact to verify what changed before launching long runs or handing work to another agent.
- For intentional bulk edits where speed matters more than immediate diff artifacts, pass `--no-state-diff` and run explicit summary commands afterward.

## Removing Files

- Removing source files uses `vivado-cli fileset remove-files --expect-destructive`.
- Removing XDC files from a constraint set uses `vivado-cli constraint apply --remove ... --expect-destructive`.
- Reordering XDC files uses `vivado-cli constraint apply --reorder ...` after `vivado-cli constraint check-order` produces or confirms the desired order.

## Notes For AI

- Prefer structured CLI commands first. Use raw Tcl only for uncommon Vivado options that are not exposed by `fileset` or `constraint` commands.
- Keep source/XDC Tcl small and inspectable.
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

- `xdc_load_order_unknown`: run `vivado-cli constraint check-order` and apply a confirmed plan with `vivado-cli constraint apply --reorder`.
- `top_not_found`: inspect project summary and set the fileset `top` property
  with `vivado-cli fileset set-top` or `vivado-cli fileset apply --top`.
- `multiple_library_assignment`: set `LIBRARY` explicitly with
  `vivado-cli fileset set-file-properties --property LIBRARY=...` rather than letting Vivado auto-assign from the
  file extension.
- `define_not_in_effect`: set fileset defines with `vivado-cli fileset apply --define`; the property is read at elaboration.
