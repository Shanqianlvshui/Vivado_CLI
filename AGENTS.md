## Agent skills

### Issue tracker

Issues and PRDs are tracked in GitHub Issues; external PRs are not a triage surface. See `docs/agents/issue-tracker.md`.

### Triage labels

Uses the default five-label triage vocabulary. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context repo: read root `CONTEXT.md` and `docs/adr/` when present. See `docs/agents/domain.md`.

### Vivado CLI

This repo is CLI-only. Do not look for or start a Vivado MCP server.

Use the stable installed CLI executable:

```powershell
C:\Tools\vivado-cli\bin\vivado-cli.exe
```

The user-level PATH contains the executable directory:

```powershell
C:\Tools\vivado-cli\bin
```

The full executable path is also available to new terminals as:

```powershell
$env:VIVADO_CLI_EXE
```

Prefer `vivado-cli` when PATH is loaded, or `$env:VIVADO_CLI_EXE` / the full path when an agent needs an explicit executable. The project virtual-environment copy at `C:\Workspace\Vivado_mcp\.venv\Scripts\vivado-cli.exe` is for development; use the `C:\Tools` path as the stable cross-agent entry point.
