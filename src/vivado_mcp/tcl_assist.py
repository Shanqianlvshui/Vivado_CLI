from __future__ import annotations

import re
from dataclasses import dataclass


RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


@dataclass(frozen=True)
class RiskRule:
    risk_id: str
    severity: str
    pattern: str
    reason: str
    recommended_docs: tuple[str, ...] = ("UG835",)
    requires_expect_destructive: bool = False


RISK_RULES: tuple[RiskRule, ...] = (
    RiskRule(
        risk_id="session.exit",
        severity="critical",
        pattern=r"(?m)^\s*(exit|quit)\b",
        reason="Stops Vivado or the MCP bridge process and can prevent normal result/artifact reporting.",
        requires_expect_destructive=True,
    ),
    RiskRule(
        risk_id="external.exec",
        severity="critical",
        pattern=r"(?m)^\s*exec\b|open\s+\|",
        reason="Runs external programs from Vivado Tcl, equivalent to local command execution.",
        requires_expect_destructive=True,
    ),
    RiskRule(
        risk_id="hardware.program",
        severity="critical",
        pattern=r"\b(program_hw_devices|write_cfgmem|boot_hw_device)\b",
        reason="Can program or alter connected hardware devices.",
        recommended_docs=("UG835", "UG908"),
        requires_expect_destructive=True,
    ),
    RiskRule(
        risk_id="hardware.session",
        severity="high",
        pattern=r"\b(open_hw_manager|connect_hw_server|open_hw_target|refresh_hw_device)\b",
        reason="Touches live hardware-manager state and can race with user hardware sessions.",
        recommended_docs=("UG835", "UG908"),
    ),
    RiskRule(
        risk_id="file.delete",
        severity="critical",
        pattern=r"(?m)^\s*file\s+(delete|rename)\b",
        reason="Deletes or moves files on disk from inside Vivado Tcl.",
        requires_expect_destructive=True,
    ),
    RiskRule(
        risk_id="project.reset",
        severity="high",
        pattern=r"\b(reset_project|reset_run|reset_property)\b",
        reason="Resets project or run state and can discard generated outputs.",
        requires_expect_destructive=True,
    ),
    RiskRule(
        risk_id="delete.objects",
        severity="high",
        pattern=r"(?m)^\s*(delete_[A-Za-z0-9_]+|remove_files)\b",
        reason="Deletes Vivado design objects or removes files from the project.",
        requires_expect_destructive=True,
    ),
    RiskRule(
        risk_id="force.overwrite",
        severity="medium",
        pattern=r"\s-force\b",
        reason="Forces overwrite or regeneration behavior; verify target paths and generated outputs.",
        requires_expect_destructive=True,
    ),
    RiskRule(
        risk_id="source.script",
        severity="medium",
        pattern=r"(?m)^\s*source\b",
        reason="Sources another Tcl file. Review the sourced file before executing it.",
    ),
    RiskRule(
        risk_id="set.param",
        severity="medium",
        pattern=r"(?m)^\s*set_param\b",
        reason="Changes Vivado tool parameters and can affect later commands globally.",
    ),
)


COMMAND_COVERAGE: dict[str, dict[str, object]] = {
    "create_project": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado_create_project"],
        "notes": "Structured project creation covers common part/board/force use. Use Tcl for less common create_project options.",
    },
    "open_project": {
        "coverage_status": "covered",
        "recommended_tools": ["vivado_open_project"],
        "notes": "Use the structured project tool to refresh GUI/session state after opening.",
    },
    "add_files": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado_add_sources"],
        "notes": "Structured source adding covers common RTL/XDC use. Use Tcl for advanced fileset/file properties.",
    },
    "create_bd_design": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado_bd_open_or_create"],
        "notes": "Basic open/create is covered; advanced -dir/-cell forms still require Tcl.",
    },
    "open_bd_design": {
        "coverage_status": "covered",
        "recommended_tools": ["vivado_bd_open_or_create"],
        "notes": "Use the structured BD opener to preserve session state and artifact reporting.",
    },
    "create_bd_cell": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado_bd_apply"],
        "notes": "Common IP/module/hier cell creation is covered; unusual options may need Tcl.",
    },
    "create_bd_port": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado_bd_apply"],
        "notes": "Common port creation is covered; verify advanced options against UG835.",
    },
    "connect_bd_net": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado_bd_apply"],
        "notes": "Basic net connections are covered; named net/boundary options may need Tcl.",
    },
    "connect_bd_intf_net": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado_bd_apply"],
        "notes": "Basic interface connections are covered; advanced options may need Tcl.",
    },
    "validate_bd_design": {
        "coverage_status": "covered",
        "recommended_tools": ["vivado_bd_validate"],
        "notes": "Use the structured validator to keep validation artifacts attached to the session.",
    },
    "generate_target": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado_bd_generate"],
        "notes": "BD output generation is covered for common targets; force/advanced forms may need Tcl.",
    },
    "make_wrapper": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado_bd_generate"],
        "notes": "Common wrapper generation is covered; import/fileset/language variants may need Tcl.",
    },
    "launch_runs": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado_run_synthesis", "vivado_run_implementation", "vivado_generate_bitstream"],
        "notes": "Build tools cover standard synth/impl/bitstream runs. Use Tcl for custom run names, steps, strategies, or non-project flows.",
    },
    "report_timing_summary": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado_report"],
        "notes": "Use report_type='timing_summary' for the default report. Use Tcl for custom options, filters, or report formatting.",
    },
    "report_timing": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado_report"],
        "notes": "Use report_type='timing_paths' for the default report. Use Tcl for path filters and advanced timing options.",
    },
    "report_utilization": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado_report"],
        "notes": "Use report_type='utilization' for the default report. Use Tcl for hierarchy or formatting options.",
    },
    "report_drc": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado_report"],
        "notes": "Use report_type='drc' for the default report. Use Tcl for custom rule decks or filtering.",
    },
    "report_power": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado_report"],
        "notes": "Use report_type='power' for the default report. Use Tcl for activity-file and advanced estimation options.",
    },
    "report_messages": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado_report"],
        "notes": "Use report_type='messages' for the default report. Use Tcl for advanced message filtering.",
    },
    "get_files": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado_project_summary"],
        "notes": "Use summary tools for common state inspection; raw Tcl remains useful for ad hoc filters.",
    },
    "get_runs": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado_project_summary"],
        "notes": "Use summary tools for common run state; raw Tcl remains useful for ad hoc filters.",
    },
}


def review_tcl(tcl: str, *, intended_goal: str | None = None) -> dict[str, object]:
    body = _strip_comments(tcl)
    risks = []
    recommended_docs = {"UG835", "UG894"}
    requires_expect_destructive = False
    risk_level = "low"

    for rule in RISK_RULES:
        matches = [match.group(0).strip() for match in re.finditer(rule.pattern, body, flags=re.IGNORECASE)]
        if not matches:
            continue
        risks.append(
            {
                "risk_id": rule.risk_id,
                "severity": rule.severity,
                "matches": matches[:8],
                "reason": rule.reason,
                "recommended_docs": list(rule.recommended_docs),
                "requires_expect_destructive": rule.requires_expect_destructive,
            }
        )
        recommended_docs.update(rule.recommended_docs)
        requires_expect_destructive = requires_expect_destructive or rule.requires_expect_destructive
        if RISK_ORDER[rule.severity] > RISK_ORDER[risk_level]:
            risk_level = rule.severity

    commands = _top_level_commands(body)
    for command in commands:
        if command.startswith("report_"):
            recommended_docs.update({"UG906", "UG949"})
        if command.startswith("create_bd") or command.endswith("_bd_design") or command.startswith("connect_bd"):
            recommended_docs.update({"UG994", "UG912"})
        if command.startswith("program_hw") or command.startswith("open_hw") or command.startswith("connect_hw"):
            recommended_docs.add("UG908")

    return {
        "ok": True,
        "intended_goal": intended_goal,
        "risk_level": risk_level,
        "requires_expect_destructive": requires_expect_destructive,
        "risks": risks,
        "commands": commands,
        "recommended_docs": sorted(recommended_docs),
        "recommended_tools": ["vivado_tcl_command_help", "vivado_search_official_docs"],
        "guidance": _review_guidance(risk_level, requires_expect_destructive),
    }


def tcl_command_coverage(command: str) -> dict[str, object]:
    normalized = _normalize_command(command)
    if not normalized:
        return {
            "command": "",
            "coverage_status": "invalid",
            "recommended_tools": ["vivado_tcl_command_help"],
            "recommendation": "provide_command_name",
            "notes": "A Tcl command name is required.",
        }
    coverage = COMMAND_COVERAGE.get(normalized)
    if coverage is None:
        return {
            "command": normalized,
            "coverage_status": "raw_tcl",
            "recommended_tools": ["vivado_search_official_docs", "vivado_review_tcl", "vivado_run_tcl"],
            "recommendation": "use_expert_tcl_with_review",
            "notes": "No structured MCP tool mapping is registered for this command yet.",
        }

    recommendation = (
        "prefer_structured_tool"
        if coverage["coverage_status"] == "covered"
        else "prefer_structured_tool_when_possible"
    )
    return {
        "command": normalized,
        "coverage_status": coverage["coverage_status"],
        "recommended_tools": coverage["recommended_tools"],
        "recommendation": recommendation,
        "notes": coverage["notes"],
    }


def build_tcl_command_help(
    *,
    command: str,
    official_search: dict[str, object] | None = None,
    installed_help: dict[str, object] | None = None,
) -> dict[str, object]:
    normalized = _normalize_command(command)
    if not normalized:
        return {
            "ok": False,
            "command": "",
            "error": "command must not be empty",
            "coverage": tcl_command_coverage(normalized),
            "official_search": official_search or {"ok": False, "results": [], "error": "not requested"},
            "installed_vivado_help": _installed_help_summary(installed_help),
            "recommended_sequence": [{"step": "provide_command", "why": "Pass one Vivado Tcl command name, such as create_project."}],
        }
    coverage = tcl_command_coverage(normalized)
    return {
        "ok": True,
        "command": normalized,
        "coverage": coverage,
        "official_search": official_search or {"ok": False, "results": [], "error": "not requested"},
        "installed_vivado_help": _installed_help_summary(installed_help),
        "recommended_sequence": _command_help_sequence(coverage),
    }


def _strip_comments(tcl: str) -> str:
    lines = []
    for line in tcl.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        lines.append(line)
    return "\n".join(lines)


def _top_level_commands(tcl: str) -> list[str]:
    commands: list[str] = []
    for line in tcl.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\b", stripped)
        if match:
            command = match.group(1)
            if command not in commands:
                commands.append(command)
    return commands


def _normalize_command(command: str) -> str:
    parts = command.strip().split()
    return parts[0].lower() if parts else ""


def _review_guidance(risk_level: str, requires_expect_destructive: bool) -> list[str]:
    guidance = ["Search official docs and prefer structured MCP tools when they cover the operation."]
    if risk_level in {"high", "critical"}:
        guidance.append("Do not execute automatically in a long-running task without a clear goal and state checkpoint.")
    if requires_expect_destructive:
        guidance.append("If executed through expert mode, set expect_destructive=true and inspect state immediately afterward.")
    return guidance


def _installed_help_summary(installed_help: dict[str, object] | None) -> dict[str, object]:
    if installed_help is None:
        return {"available": False, "reason": "session_ref was not provided"}
    if not installed_help.get("ok"):
        return {
            "available": False,
            "error": installed_help.get("error") or installed_help.get("result") or "Vivado help failed",
            "raw": installed_help,
        }
    text = str(installed_help.get("result") or "")
    return {
        "available": True,
        "text": text[:6000],
        "truncated": len(text) > 6000,
        "raw": installed_help,
    }


def _command_help_sequence(coverage: dict[str, object]) -> list[dict[str, str]]:
    sequence = [{"step": "official_docs", "why": "Verify syntax and options with UG835/local official docs."}]
    if coverage["coverage_status"] in {"covered", "partial"}:
        sequence.append({"step": "structured_tool", "why": "Use the mapped MCP tool before raw Tcl when it covers the requested operation."})
    if coverage["coverage_status"] != "covered":
        sequence.append({"step": "review_tcl", "why": "Review any expert Tcl before execution."})
        sequence.append({"step": "expert_tcl", "why": "Use raw Tcl only for uncovered options or project-specific flows."})
    sequence.append({"step": "inspect_state", "why": "Refresh project/BD/report summaries after changes."})
    return sequence
