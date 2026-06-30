# Skill: GUI Session

Use this when the user wants AI to open Vivado and keep the GUI visible while AI operates the same session.

## Normal Flow

1. Run `vivado-cli check-installation`.
2. Run `vivado-cli session start` unless a usable session already exists.
3. Use `vivado-cli session list` and `vivado-cli session state --session <ref>` to recover the active session.
4. Open the project with `vivado-cli session open-project --session <ref> <project.xpr>`.
5. Use workflow commands such as `vivado-cli project summary`, `vivado-cli bd summary`, `vivado-cli run status`, `vivado-cli report`, `vivado-cli hw list-debug-cores`, `vivado-cli hw vio-read`, `vivado-cli hw vio-write`, `vivado-cli hw capture-ila`, and `vivado-cli hw spi-read`.
6. Use `vivado-cli session run-tcl` or `vivado-cli session source-tcl` only after `vivado-cli tcl review` for nontrivial Tcl.
7. Run `vivado-cli session stop --session <ref>` only when the user wants the GUI/process closed.

## Notes For AI

- Do not use GUI click automation.
- Treat the GUI as a visible state viewer and occasional human interaction surface.
- Refresh session state before mutating commands because the user may have changed state in the GUI.
- Do not close an existing Vivado GUI unless the user explicitly asks.
- The CLI controls Vivado through the Tcl bridge, not GUI clicks.
