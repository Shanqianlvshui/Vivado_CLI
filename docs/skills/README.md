# Vivado MCP Skills

These documents are seed content for the MCP server's built-in help system. The server should expose them as MCP resources and make them discoverable through help tools.

Suggested resource URIs:

- `vivado://skills/index`
- `vivado://skills/gui-session`
- `vivado://skills/project-build-flow`
- `vivado://skills/block-design-flow`
- `vivado://skills/official-docs-reference`
- `vivado://skills/raw-tcl-expert`
- `vivado://official-docs/index`

The documents are written for AI clients. They should explain when to use a capability, required preconditions, safe call sequences, common failure modes, and useful follow-up inspections.

Official-document guidance is exposed as metadata and topic routing, not copied AMD document bodies. Use `vivado_official_reference_guide`, `vivado_list_official_references`, and `vivado_get_official_reference` to find the relevant AMD source before generating Tcl or using expert mode.
