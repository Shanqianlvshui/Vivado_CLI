# Skill: Project Build Flow

Use this for ordinary Project Mode FPGA work: create/open a project, add files, run synthesis/implementation, generate reports, and summarize failures.

## Normal Flow

1. Run `vivado-cli check-installation`.
2. Run `vivado-cli session start` or reuse a known session from `vivado-cli session list`.
3. Open an existing project with `vivado-cli session open-project --session <ref> <project.xpr>`.
4. Run `vivado-cli project summary --session <ref>` to inspect project files, runs, IP, and block designs.
5. For run recovery, use `vivado-cli run status`, `vivado-cli run diagnose`, and `vivado-cli run logs`.
6. Launch runs with `vivado-cli run launch --session <ref> <run> --jobs <n>`.
7. If Vivado leaves a run queued without a worker, use `vivado-cli run launch-local --session <ref> <run> --jobs <n>`.
8. Reset runs only with `vivado-cli run reset --session <ref> <run> --expect-destructive`.
9. Generate targeted reports with `vivado-cli report --session <ref> <type>`.
10. For sources, constraints, IP, simulation, hardware, and Non-project flows not yet exposed as structured CLI commands, use `vivado-cli tcl help <command>`, `vivado-cli tcl review`, then `vivado-cli session run-tcl` or `source-tcl`.
11. After any project mutation, re-run `vivado-cli project summary`, `vivado-cli bd summary`, run diagnostics, or reports as appropriate.

## Notes For AI

- Prefer workflow tools over raw Tcl for repeatable project operations.
- `vivado-cli tools list` is the authority for commands currently exposed by the CLI.
- Do not assume README roadmap tools are implemented until `tools list` shows them.
- Use `run diagnose` before retrying a queued or failed run.
- Use `run logs` to read bounded logs instead of pasting entire run directories.
- Fix missing constraints, stale IP/output products, and DRC issues before treating implementation strategy as the main problem.
