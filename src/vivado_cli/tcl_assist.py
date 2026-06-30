from __future__ import annotations

import re
from dataclasses import dataclass


RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


TCL_CONTROL_COMMANDS = {
    "after",
    "append",
    "binary",
    "break",
    "catch",
    "clock",
    "close",
    "concat",
    "continue",
    "dict",
    "else",
    "elseif",
    "eval",
    "expr",
    "for",
    "foreach",
    "format",
    "gets",
    "global",
    "if",
    "incr",
    "join",
    "lappend",
    "lindex",
    "linsert",
    "list",
    "llength",
    "lrange",
    "lreplace",
    "lsearch",
    "lsort",
    "namespace",
    "package",
    "proc",
    "puts",
    "read",
    "regexp",
    "regsub",
    "return",
    "scan",
    "set",
    "split",
    "string",
    "switch",
    "unset",
    "update",
    "uplevel",
    "upvar",
    "variable",
    "while",
}


DOCS_BY_TOPIC: dict[str, tuple[str, ...]] = {
    "tcl": ("UG835", "UG894"),
    "project": ("UG892", "UG895", "UG912", "UG835"),
    "bd": ("UG994", "UG912", "UG835"),
    "ip": ("UG896", "UG994", "UG1118", "UG835", "UG912"),
    "constraints": ("UG903", "UG899", "UG912", "UG835"),
    "build": ("UG901", "UG904", "UG906", "UG949", "UG1292", "UG835"),
    "simulation": ("UG900", "UG896", "UG835"),
    "reports": ("UG906", "UG907", "UG949", "UG1292", "UG835"),
    "hardware": ("UG908", "UG835", "UG912"),
}


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
        pattern=r"(?m)(?:^|[;\{\[])\s*(exit|quit)\b",
        reason="Stops Vivado or the CLI bridge process and can prevent normal result/artifact reporting.",
        requires_expect_destructive=True,
    ),
    RiskRule(
        risk_id="external.exec",
        severity="critical",
        pattern=r"(?m)(?:^|[;\{\[])\s*exec\b|\bopen\s+\|",
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
        pattern=r"(?m)(?:^|[;\{\[])\s*file\s+(delete|rename)\b",
        reason="Deletes or moves files on disk from inside Vivado Tcl.",
        requires_expect_destructive=True,
    ),
    RiskRule(
        risk_id="project.reset",
        severity="high",
        pattern=r"\b(reset_project|reset_run|reset_runs|reset_property)\b",
        reason="Resets project or run state and can discard generated outputs.",
        requires_expect_destructive=True,
    ),
    RiskRule(
        risk_id="ip.upgrade",
        severity="high",
        pattern=r"\b(upgrade_ip)\b",
        reason="Upgrades IP metadata and can rewrite .xci files or generated products.",
        recommended_docs=("UG835", "UG896"),
        requires_expect_destructive=True,
    ),
    RiskRule(
        risk_id="ip.generate",
        severity="medium",
        pattern=r"\bgenerate_target\b",
        reason="Regenerates IP or BD output products and can change generated files.",
        recommended_docs=("UG835", "UG896", "UG994"),
        requires_expect_destructive=True,
    ),
    RiskRule(
        risk_id="delete.objects",
        severity="high",
        pattern=r"(?m)(?:^|[;\{\[])\s*(delete_[A-Za-z0-9_]+|remove_files)\b",
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
        pattern=r"(?m)(?:^|[;\{\[])\s*source\b",
        reason="Sources another Tcl file. Review the sourced file before executing it.",
    ),
    RiskRule(
        risk_id="set.param",
        severity="medium",
        pattern=r"(?m)(?:^|[;\{\[])\s*set_param\b",
        reason="Changes Vivado tool parameters and can affect later commands globally.",
    ),
)


COMMAND_DOC_TOPICS: dict[str, str] = {
    "add_files": "project",
    "connect_bd_intf_net": "bd",
    "connect_bd_net": "bd",
    "create_bd_cell": "bd",
    "create_bd_design": "bd",
    "create_bd_port": "bd",
    "create_clock": "constraints",
    "create_fileset": "project",
    "create_generated_clock": "constraints",
    "create_ip": "ip",
    "create_project": "project",
    "connect_hw_server": "hardware",
    "delete_bd_objs": "bd",
    "generate_target": "bd",
    "get_files": "project",
    "get_hw_devices": "hardware",
    "get_hw_targets": "hardware",
    "get_runs": "build",
    "launch_simulation": "simulation",
    "launch_runs": "build",
    "make_wrapper": "bd",
    "open_bd_design": "bd",
    "open_hw_manager": "hardware",
    "open_hw_target": "hardware",
    "open_project": "project",
    "program_hw_devices": "hardware",
    "boot_hw_device": "hardware",
    "refresh_hw_device": "hardware",
    "read_vhdl": "build",
    "read_verilog": "build",
    "read_xdc": "build",
    "remove_files": "project",
    "report_drc": "reports",
    "report_messages": "reports",
    "report_power": "reports",
    "report_clock_interaction": "reports",
    "report_timing": "reports",
    "report_timing_summary": "reports",
    "report_utilization": "reports",
    "reset_project": "project",
    "set_clock_groups": "constraints",
    "set_false_path": "constraints",
    "set_input_delay": "constraints",
    "set_output_delay": "constraints",
    "set_property": "project",
    "opt_design": "build",
    "place_design": "build",
    "route_design": "build",
    "synth_design": "build",
    "validate_bd_design": "bd",
    "write_checkpoint": "build",
}


COMMAND_COVERAGE: dict[str, dict[str, object]] = {
    "create_project": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli session open-project"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "No structured project-create command is exposed yet. Review create_project Tcl, execute it through expert mode, then open the .xpr through the CLI session command.",
    },
    "open_project": {
        "coverage_status": "covered",
        "recommended_tools": ["vivado-cli session open-project", "vivado-cli project summary"],
        "notes": "Use the CLI session command to open the project and refresh session/project state.",
    },
    "add_files": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli project summary"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "No structured fileset mutation command is exposed yet. Review add_files Tcl and inspect the project summary afterward.",
    },
    "create_fileset": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli project summary"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "No structured create_fileset command is exposed yet. Use reviewed Tcl and inspect the fileset state through project summary.",
    },
    "remove_files": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl --expect-destructive", "vivado-cli project summary"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "File removal is destructive. Review the Tcl, acknowledge destructive execution when required, then inspect the project summary.",
    },
    "set_property": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli project summary"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "No structured set_property command is exposed yet. Check UG912/UG835, review the Tcl, and inspect project state afterward.",
    },
    "create_bd_design": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli bd summary", "vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli bd validate"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "BD creation/mutation is still expert Tcl. Use BD summary/validation before and after the reviewed Tcl action.",
    },
    "open_bd_design": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli bd summary", "vivado-cli tcl review", "vivado-cli session run-tcl"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "No dedicated open_bd_design CLI command is exposed yet. Use reviewed Tcl and then refresh the BD summary.",
    },
    "create_bd_cell": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli bd summary", "vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli bd validate"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "BD cell creation is not structured yet. Inspect current BD state, review Tcl, run it, then validate the BD.",
    },
    "create_bd_port": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli bd summary", "vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli bd validate"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "BD port creation is not structured yet. Verify options against UG835 and validate the BD afterward.",
    },
    "connect_bd_net": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli bd summary", "vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli bd validate"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "BD net connection is not structured yet. Use summary/validation around reviewed Tcl.",
    },
    "connect_bd_intf_net": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli bd summary", "vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli bd validate"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "BD interface connection is not structured yet. Use summary/validation around reviewed Tcl.",
    },
    "validate_bd_design": {
        "coverage_status": "covered",
        "recommended_tools": ["vivado-cli bd validate", "vivado-cli bd summary"],
        "notes": "Use the CLI validator to keep parsed validation diagnostics attached to the session artifacts.",
    },
    "generate_target": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl --expect-destructive", "vivado-cli project summary", "vivado-cli bd summary"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "IP/BD output generation is not exposed as a structured CLI command yet and can rewrite generated files.",
    },
    "make_wrapper": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli project summary"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "Wrapper generation is expert Tcl for now. Inspect project files afterward.",
    },
    "launch_runs": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado-cli run status", "vivado-cli run launch", "vivado-cli run launch-local", "vivado-cli run diagnose", "vivado-cli run logs"],
        "notes": "The CLI covers project run launch/status/diagnostics/logs. Use Tcl for uncommon launch_runs options or non-project flows.",
    },
    "launch_simulation": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli project summary", "vivado-cli tcl review", "vivado-cli session run-tcl"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "Dedicated simulation commands are not exposed yet. Inspect project state, review launch Tcl, and capture logs manually as needed.",
    },
    "open_hw_manager": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli session state"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "Hardware Manager access is expert Tcl for now. Review against UG908/UG835 before touching live hardware state.",
    },
    "connect_hw_server": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli session state"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "hw_server access is expert Tcl for now. Review target selection and avoid programming operations unless explicitly approved.",
    },
    "open_hw_target": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli session state"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "Opening hardware targets is expert Tcl for now. Review target filters and state impact first.",
    },
    "get_hw_targets": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "Read-only hardware enumeration is still expert Tcl until a dedicated CLI command is exposed.",
    },
    "get_hw_devices": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "Read-only hardware device enumeration is still expert Tcl until a dedicated CLI command is exposed.",
    },
    "refresh_hw_device": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "Refreshing hardware device state is expert Tcl. Review whether it is read-only for the target flow before execution.",
    },
    "program_hw_devices": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl --expect-destructive"],
        "recommendation": "requires_explicit_user_approval_and_expert_tcl",
        "notes": "No structured programming command exists. Review against UG908/UG835 and require --expect-destructive for expert Tcl.",
    },
    "write_cfgmem": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl --expect-destructive"],
        "recommendation": "requires_explicit_user_approval_and_expert_tcl",
        "notes": "No structured configuration-memory write command exists. Review against UG908/UG835 and require --expect-destructive.",
    },
    "boot_hw_device": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl --expect-destructive"],
        "recommendation": "requires_explicit_user_approval_and_expert_tcl",
        "notes": "No structured boot command exists. Review against UG908/UG835 and require --expect-destructive.",
    },
    "read_verilog": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "Dedicated Non-project commands are not exposed yet. Use reviewed Tcl for read_verilog/read_vhdl/read_xdc.",
    },
    "read_vhdl": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "Dedicated Non-project commands are not exposed yet. Use reviewed Tcl for read_verilog/read_vhdl/read_xdc.",
    },
    "read_xdc": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "Dedicated Non-project commands are not exposed yet. Use reviewed Tcl for constraint loading.",
    },
    "synth_design": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli report"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "Dedicated Non-project synthesis is not exposed yet. Use reviewed Tcl and generate reports after synthesis.",
    },
    "opt_design": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli report"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "Dedicated Non-project optimization is not exposed yet. Use reviewed Tcl and inspect reports/checkpoints afterward.",
    },
    "place_design": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli report"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "Dedicated Non-project placement is not exposed yet. Use reviewed Tcl and inspect timing/utilization afterward.",
    },
    "route_design": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli report"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "Dedicated Non-project routing is not exposed yet. Use reviewed Tcl and inspect final timing/DRC/power reports.",
    },
    "write_checkpoint": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "Checkpoint writing is expert Tcl for now. Keep checkpoint paths under the intended workspace.",
    },
    "create_clock": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli project summary"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "No structured clock-constraint writer exists yet. Check UG903/UG835, review the Tcl, then inspect XDC order and scope.",
    },
    "create_generated_clock": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli project summary"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "No structured generated-clock writer exists yet. Confirm generated clock source/master semantics before applying.",
    },
    "set_clock_groups": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli project summary"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "No structured clock-group writer exists yet. Verify asynchronous or logically exclusive intent before applying.",
    },
    "set_false_path": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli report"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "No structured timing-exception writer exists yet. Prefer a narrow exception and inspect timing coverage afterward.",
    },
    "set_input_delay": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli report"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "No structured I/O delay writer exists yet. Verify referenced clock and min/max intent in UG903.",
    },
    "set_output_delay": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli report"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "No structured I/O delay writer exists yet. Verify referenced clock and external timing budget in UG903.",
    },
    "create_ip": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli project summary"],
        "recommendation": "use_expert_tcl_with_review",
        "notes": "Dedicated IP commands are not exposed yet. Use reviewed create_ip Tcl and inspect project IP state afterward.",
    },
    "upgrade_ip": {
        "coverage_status": "raw_tcl",
        "recommended_tools": ["vivado-cli tcl review", "vivado-cli session run-tcl --expect-destructive", "vivado-cli project summary"],
        "recommendation": "requires_explicit_user_approval_and_expert_tcl",
        "notes": "IP upgrade can rewrite .xci files. Review the Tcl and require --expect-destructive before execution.",
    },
    "report_timing_summary": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado-cli report"],
        "notes": "Use `vivado-cli report timing_summary` for the default report. Use reviewed Tcl for custom options or filters.",
    },
    "report_timing": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado-cli report"],
        "notes": "Use `vivado-cli report timing_paths` for the default path report. Use reviewed Tcl for path filters and advanced options.",
    },
    "report_utilization": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado-cli report"],
        "notes": "Use `vivado-cli report utilization` for the default report. Use reviewed Tcl for hierarchy or formatting options.",
    },
    "report_drc": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado-cli report"],
        "notes": "Use `vivado-cli report drc` for the default report. Use reviewed Tcl for custom rule decks or filtering.",
    },
    "report_power": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado-cli report"],
        "notes": "Use `vivado-cli report power` for the default report. Use reviewed Tcl for activity-file and advanced estimation options.",
    },
    "report_clock_interaction": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado-cli report"],
        "notes": "Use `vivado-cli report clock_interaction` for default clock-interaction diagnostics. Use reviewed Tcl for custom filters or formatting.",
    },
    "report_messages": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado-cli report"],
        "notes": "Use `vivado-cli report messages` for the default report. Use reviewed Tcl for advanced message filtering.",
    },
    "get_files": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado-cli project summary"],
        "notes": "Use project summary for common state inspection; raw Tcl remains useful for ad hoc filters.",
    },
    "get_runs": {
        "coverage_status": "partial",
        "recommended_tools": ["vivado-cli project summary", "vivado-cli run status"],
        "notes": "Use project summary and run status for common run state; raw Tcl remains useful for ad hoc filters.",
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

    command_reviews = _reviewed_command_guidance(commands, risks)
    for review in command_reviews:
        recommended_docs.update(DOCS_BY_TOPIC.get(str(review["official_doc_topic"]), ("UG835",)))

    return {
        "ok": True,
        "intended_goal": intended_goal,
        "risk_level": risk_level,
        "requires_expect_destructive": requires_expect_destructive,
        "risks": risks,
        "commands": commands,
        "command_reviews": command_reviews,
        "official_doc_queries": _official_doc_queries(command_reviews),
        "recommended_docs": sorted(recommended_docs),
        "recommended_tools": _review_recommended_tools(command_reviews, requires_expect_destructive),
        "guidance": _review_guidance(risk_level, requires_expect_destructive),
    }


def tcl_command_coverage(command: str) -> dict[str, object]:
    normalized = _normalize_command(command)
    if not normalized:
        return {
            "command": "",
            "coverage_status": "invalid",
            "recommended_tools": ["vivado-cli tcl help <command>"],
            "recommendation": "provide_command_name",
            "notes": "A Tcl command name is required.",
        }
    coverage = COMMAND_COVERAGE.get(normalized)
    if coverage is None:
        return {
            "command": normalized,
            "coverage_status": "raw_tcl",
            "recommended_tools": ["vivado-cli help topic official-docs", "vivado-cli tcl review", "vivado-cli session run-tcl"],
            "recommendation": "use_expert_tcl_with_review",
            "notes": "No structured CLI command mapping is registered for this command yet.",
        }

    recommendation = str(
        coverage.get(
            "recommendation",
            "prefer_structured_tool" if coverage["coverage_status"] == "covered" else "prefer_structured_tool_when_possible",
        )
    )
    return {
        "command": normalized,
        "coverage_status": coverage["coverage_status"],
        "recommended_tools": coverage["recommended_tools"],
        "recommendation": recommendation,
        "notes": coverage["notes"],
    }


def tcl_command_doc_topic(command: str) -> str:
    normalized = _normalize_command(command)
    if not normalized:
        return "tcl"
    if normalized in COMMAND_DOC_TOPICS:
        return COMMAND_DOC_TOPICS[normalized]
    if normalized.startswith(("create_bd_", "connect_bd_", "get_bd_", "set_bd_", "delete_bd_")):
        return "bd"
    if normalized.startswith(("create_ip", "get_ip", "upgrade_ip", "generate_target")):
        return "ip"
    if normalized.startswith(("report_",)):
        return "reports"
    if normalized.startswith(("open_hw", "program_hw", "connect_hw", "get_hw")):
        return "hardware"
    if normalized in {"read_verilog", "read_vhdl", "read_xdc", "synth_design", "opt_design", "place_design", "route_design", "write_checkpoint"}:
        return "build"
    return "tcl"


def build_tcl_command_help(
    *,
    command: str,
    official_search: dict[str, object] | None = None,
    installed_help: dict[str, object] | None = None,
    official_doc_topic: str | None = None,
) -> dict[str, object]:
    normalized = _normalize_command(command)
    doc_topic = official_doc_topic or tcl_command_doc_topic(normalized)
    if not normalized:
        return {
            "ok": False,
            "command": "",
            "error": "command must not be empty",
            "coverage": tcl_command_coverage(normalized),
            "official_doc_topic": doc_topic,
            "official_search": official_search or {"ok": False, "results": [], "error": "not requested"},
            "installed_vivado_help": _installed_help_summary(installed_help),
            "recommended_sequence": [{"step": "provide_command", "why": "Pass one Vivado Tcl command name, such as create_project."}],
        }
    coverage = tcl_command_coverage(normalized)
    return {
        "ok": True,
        "command": normalized,
        "coverage": coverage,
        "official_doc_topic": doc_topic,
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
    body = _mask_braced_text(tcl)
    for match in re.finditer(r"(?m)(?:^|[;\[])\s*([A-Za-z_][A-Za-z0-9_]*)\b", body):
        command = match.group(1)
        if command not in commands:
            commands.append(command)
    return commands


def _mask_braced_text(tcl: str) -> str:
    chars = list(tcl)
    brace_depth = 0
    escaped = False
    for index, char in enumerate(chars):
        if escaped:
            if brace_depth:
                chars[index] = " "
            escaped = False
            continue
        if char == "\\":
            escaped = True
            if brace_depth:
                chars[index] = " "
            continue
        if brace_depth:
            if char == "{":
                brace_depth += 1
            elif char == "}":
                brace_depth -= 1
            if char not in "\r\n":
                chars[index] = " "
            continue
        if char == "{":
            brace_depth = 1
            chars[index] = " "
    return "".join(chars)


def _normalize_command(command: str) -> str:
    parts = command.strip().split()
    return parts[0].lower() if parts else ""


def _reviewed_command_guidance(commands: list[str], risks: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for command in commands:
        _add_reviewed_command(rows, command, "top_level")
    for risk in risks:
        risk_id = str(risk.get("risk_id") or "risk")
        for match in risk.get("matches", []):
            for command in _risk_match_commands(str(match), risk_id):
                _add_reviewed_command(rows, command, f"risk:{risk_id}")
    return list(rows.values())


def _add_reviewed_command(rows: dict[str, dict[str, object]], command: str, source: str) -> None:
    normalized = _normalize_command(command)
    if not normalized:
        return
    if source == "top_level" and normalized in TCL_CONTROL_COMMANDS:
        return
    row = rows.get(normalized)
    if row is None:
        coverage = tcl_command_coverage(normalized)
        row = {
            "command": normalized,
            "official_doc_topic": tcl_command_doc_topic(normalized),
            "coverage": coverage,
            "help_tool": f"vivado-cli tcl help {normalized}",
            "sources": [],
        }
        rows[normalized] = row
    sources = row["sources"]
    assert isinstance(sources, list)
    if source not in sources:
        sources.append(source)


def _risk_match_commands(match: str, risk_id: str) -> list[str]:
    cleaned = match.strip().lstrip(";{[ ").strip()
    if not cleaned:
        return []
    words = cleaned.split()
    if not words:
        return []
    command = words[0]
    if risk_id == "project.reset" and command == "reset_runs":
        return ["reset_runs"]
    if risk_id == "file.delete":
        return ["file"]
    if risk_id == "external.exec" and command == "open":
        return ["open"]
    return [command]


def _official_doc_queries(command_reviews: list[dict[str, object]]) -> list[dict[str, str]]:
    return [
        {
            "command": str(row["command"]),
            "topic": str(row["official_doc_topic"]),
            "query": str(row["command"]),
            "tool": str(row["help_tool"]),
        }
        for row in command_reviews
    ]


def _review_recommended_tools(command_reviews: list[dict[str, object]], requires_expect_destructive: bool) -> list[str]:
    tools: list[str] = []
    for row in command_reviews:
        tools.append(str(row["help_tool"]))
    tools.append("vivado-cli help topic official-docs")
    for row in command_reviews:
        coverage = row["coverage"]
        assert isinstance(coverage, dict)
        for tool in coverage.get("recommended_tools", []):
            tools.append(str(tool))
    tools.append("vivado-cli session run-tcl --expect-destructive" if requires_expect_destructive else "vivado-cli session run-tcl")
    return _dedupe(tools) or ["vivado-cli tcl help <command>", "vivado-cli help topic official-docs"]


def _review_guidance(risk_level: str, requires_expect_destructive: bool) -> list[str]:
    guidance = ["Search official docs and prefer structured CLI commands when they cover the operation."]
    if risk_level in {"high", "critical"}:
        guidance.append("Do not execute automatically in a long-running task without a clear goal and state checkpoint.")
    if requires_expect_destructive:
        guidance.append("If executed through expert mode, pass --expect-destructive and inspect state immediately afterward.")
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
        sequence.append({"step": "structured_command", "why": "Use the mapped CLI command before raw Tcl when it covers the requested operation."})
    if coverage["coverage_status"] != "covered":
        sequence.append({"step": "review_tcl", "why": "Review any expert Tcl before execution."})
        sequence.append({"step": "expert_tcl", "why": "Use raw Tcl only for uncovered options or project-specific flows."})
    sequence.append({"step": "inspect_state", "why": "Refresh project/BD/report summaries after changes."})
    return sequence


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
