# Skill: Hardware Debug Flow

Use this when the user wants to inspect live Vivado hardware, capture ILA data,
or debug a programmed device while keeping the workflow reusable across boards
and projects.

## Normal Flow

1. Run `vivado-cli session state --session <ref>` and confirm the session is
   idle, CLI-compatible, and attached to the intended project.
2. Prefer `vivado-cli tools list --query hw` before writing Hardware Manager
   Tcl. Use structured commands when they cover the operation.
3. List debug cores and probes with `vivado-cli hw list-debug-cores --session
   <ref> --expect-hardware-access` before guessing ILA/VIO/probe names.
4. Read current VIO probe values with `vivado-cli hw vio-read --session <ref>
   --vio <hw_vio_or_cell> --probe <probe> --expect-hardware-access`.
5. Write VIO output probes only when needed with `vivado-cli hw vio-write
   --session <ref> --vio <hw_vio_or_cell> --set <probe>=<value>
   --expect-hardware-access --expect-vio-write`.
6. Capture ILA data with `vivado-cli hw capture-ila --session <ref> --ila
   <hw_ila_name_or_pattern> --expect-hardware-access`.
7. Read VIO-backed SPI/status registers with `vivado-cli hw spi-read --session
   <ref> --vio <hw_vio_or_cell> --status-probe <probe> --req-probe <probe>
   --target-probe <probe> --addr-probe <probe> --reg <target>:<addr>
   --expect-hardware-access`.
8. Pass `--analysis adc14`, `--analysis signed`, or `--analysis unsigned` when
   numeric probe statistics are useful. Pass `--sample-rate-hz <rate>` when FFT
   bins should be converted to Hz.
9. Store a meaningful `--label` so artifacts remain searchable across long
   bring-up sessions.
10. Use expert Tcl only for hardware actions that are not yet structured. Run
   `vivado-cli tcl help <command>` and `vivado-cli tcl review` first.
11. Keep programming operations such as `program_hw_devices`, configuration
   memory writes, and boot operations in reviewed expert Tcl with explicit
   destructive acknowledgement.

## Notes For AI

- Do not hard-code board names, ILA names, or probe names in reusable flows.
- Use `hw list-debug-cores` output as the evidence source for `--ila`,
  `--cell-name`, `--vio`, and probe parameters.
- Use `hw vio-read` before `hw spi-read` when you only need to inspect status
  or confirm that a VIO probe is changing.
- Use `hw vio-write` only for output probes. It requires both
  `--expect-hardware-access` and `--expect-vio-write`; take a `vio-read`
  snapshot first when the current state matters.
- Treat `--expect-hardware-access` as acknowledgement that the command touches
  live hw_server/device state, not as permission to program or erase hardware.
- Use artifact paths and analysis JSON as evidence; do not rely only on GUI
  waveforms or screenshots.
- For `hw spi-read`, pass probe names and status bit layout explicitly. Keep
  board/device register tables outside the generic command unless a separate
  preset/config layer is added.
- If a project needs board-specific register presets, keep them outside the
  generic hardware capture command and pass them as explicit preset data later.
