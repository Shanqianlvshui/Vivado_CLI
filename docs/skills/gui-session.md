# Skill: GUI Session

Use this when the user wants AI to open Vivado and keep the GUI visible while AI operates the same session.

## Preconditions

- Vivado is installed and discoverable, or the user provides `vivado_path`.
- The user is comfortable with the MCP server starting a local Vivado process.
- The session should have a dedicated workspace/session directory.

## Normal Flow

1. Call `vivado_check_installation`.
2. Call `vivado_start_session` with `open_gui=true`.
3. Call `vivado_session_state` and confirm the bridge is idle.
4. Use workflow tools such as `vivado_create_project`, `vivado_add_sources`, `vivado_run_synthesis`, and `vivado_report`.
5. Call `vivado_stop_session` when finished.

## Notes For AI

- Do not use GUI click automation.
- Treat the Vivado GUI as a visible state viewer and occasional human interaction surface.
- Before each mutating command, refresh session state because the user may have changed the project in the GUI.
- If the session is busy, wait or ask before sending another command.

## Common Problems

- If Vivado starts but bridge state is not idle, inspect the session log resource.
- If GUI shutdown returns a non-zero process code, prefer the bridge result file when it shows the command succeeded.
- If the user already opened Vivado manually, ask them to source the bridge script or start a managed session instead.

