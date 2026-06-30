# Skill: Official Docs Reference

Use this whenever a Vivado task depends on command syntax, flow rules, object properties, or report interpretation.

## Normal Flow

1. Run `vivado-cli skills get official-docs-reference` to read this routing guide.
2. Use the topic routing below to choose the smallest set of AMD/Xilinx documents needed for the task.
3. Use local PDFs under `C:\Database\domains\fpga\xilinx\vivado\docs\raw` or the shared `C:\Database` knowledge base when available.
4. Run `vivado-cli tcl help <command>` for exact installed-version Tcl command help.
5. Run `vivado-cli tools list` or `vivado-cli tools describe <command>` to check whether the CLI already exposes a structured command.
6. If no structured command exists, use `vivado-cli tcl review` before `vivado-cli session run-tcl` or `source-tcl`.
7. For exact command syntax, treat UG835 as the command authority.
8. For object properties, treat UG912 as the property authority.
9. For workflow concepts, use the topic-specific user guide before generating Tcl.
10. Prefer structured CLI workflow commands when they cover the task.
11. Use `vivado-cli tcl review` before `vivado-cli session run-tcl` or `source-tcl` when the workflow commands do not expose the needed command.

## Topic Routing

- Tcl command syntax: UG835, then UG894.
- Tcl script structure and object queries: UG894, plus UG893 for Tcl Console and IDE context.
- Project and source management: UG892, UG895, UG893, UG888, UG835, UG912.
- Block design and IP Integrator: UG994, UG835, UG912, UG895, UG896.
- IP customization and output products: UG896, UG994, UG1118, UG835.
- Constraints: UG903, UG899, UG912, UG835.
- Synthesis and implementation: UG901, UG904, UG906, UG949, UG1292, UG835.
- Simulation: UG900, UG896, UG835.
- Reports and closure: UG906, UG907, UG949, UG1292, UG835.
- Hardware programming and debug: UG908, UG835, UG912.
- Dynamic Function eXchange: UG909, UG835, UG912.
- I/O and clock planning: UG899, UG903, UG912, UG835.
- Installation, licensing, and release notes: UG973.
- ISE migration: UG911, UG903, UG835, UG912.
- Device primitive libraries: UG953 for 7 Series/Zynq-7000 and UG974 for UltraScale/UltraScale+.
- Embedded methodology: UG1046, then the flow-specific Vivado guides.

## Notes For AI

- The CLI package includes official-document metadata and routing guidance, not the full AMD document text or every individual IP product guide.
- The default local documentation root is `C:\Database\domains\fpga\xilinx\vivado\docs\raw`; deployments can override it with `VIVADO_CLI_DOCS_ROOT`.
- Local PDF search uses Poppler `pdftotext`; set `VIVADO_CLI_PDFTOTEXT` when it is not on `PATH`.
- PDF download uses AMD KHub APIs and verifies the `%PDF` signature instead of saving Fluid Topics HTML pages.
- If an installed Vivado version differs from the packaged guide version, prefer the installed Vivado command help for version-specific syntax checks.
- Do not assume every UG835 command has a structured CLI command. Expert mode can run raw Tcl, but workflow commands should stay the first choice for repeatable operations.
- For destructive or hardware-affecting Tcl, use `vivado-cli tcl review`, call out the risk before execution, and pass `--expect-destructive`.
