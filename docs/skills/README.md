# Vivado CLI Skills

These documents are seed content for the CLI built-in help system. CLI commands should return them as structured JSON or text payloads.

The documents are written for CLI callers and AI agents. They should explain when to use a capability, required preconditions, safe call sequences, common failure modes, and useful follow-up inspections.

Use `vivado-cli skills list`, `vivado-cli skills get <skill_id>`, `vivado-cli help topic <topic>`, `vivado-cli tools list`, and `vivado-cli tools describe <command-or-tool-id>` to discover the current CLI surface. For commands that are not yet structured, use `vivado-cli tcl help <command>`, `vivado-cli tcl review`, and then `vivado-cli session run-tcl` or `vivado-cli session source-tcl`.
