# Skill: GUI Session

Use this when the user wants AI to open Vivado and keep the GUI visible while AI operates the same session.

## Normal Flow

1. Call `vivado_check_installation`.
2. Call `vivado_start_session` with `open_gui=true`.
3. Call `vivado_session_state` and confirm the bridge is idle.
4. Use workflow tools or `vivado_run_tcl`.
5. Call `vivado_stop_session` when finished.

## Notes For AI

- Do not use GUI click automation.
- Treat the GUI as a visible state viewer and occasional human interaction surface.
- Refresh session state before mutating commands because the user may have changed state in the GUI.

