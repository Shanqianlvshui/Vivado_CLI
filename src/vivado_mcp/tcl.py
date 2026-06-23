from __future__ import annotations

from pathlib import Path
from typing import Any


def quote_tcl(value: str | Path) -> str:
    text = str(value).replace("\\", "/")
    return "{" + text.replace("}", "\\}") + "}"


def tcl_list(values: list[str | Path]) -> str:
    return " ".join(quote_tcl(value) for value in values)


def set_argv_tcl(args: list[str]) -> str:
    return "\n".join(
        [
            f"set ::argv [list {tcl_list(args)}]",
            f"set ::argc {len(args)}",
        ]
    )


def stop_bridge_tcl() -> str:
    return "\n".join(
        [
            "catch { stop_gui }",
            "set ::vivado_mcp_bridge_forever 1",
            'return "stopping"',
        ]
    )


def create_project_tcl(
    *,
    project_name: str,
    project_dir: Path,
    part: str | None,
    board_part: str | None,
    force: bool,
) -> str:
    force_arg = " -force" if force else ""
    lines = [
        f"create_project {quote_tcl(project_name)} {quote_tcl(project_dir)}{force_arg}",
    ]
    if part:
        lines[0] += f" -part {quote_tcl(part)}"
    if board_part:
        lines.append(f"set_property board_part {quote_tcl(board_part)} [current_project]")
    lines.append('return "project_created=[current_project]"')
    return "\n".join(lines)


def open_project_tcl(project_path: Path) -> str:
    return "\n".join(
        [
            f"open_project {quote_tcl(project_path)}",
            'return "project_opened=[current_project]"',
        ]
    )


def add_sources_tcl(
    *,
    sources: list[Path],
    constraints: list[Path],
    top: str | None,
) -> str:
    lines: list[str] = []
    if sources:
        lines.append(f"add_files [list {tcl_list(sources)}]")
    if constraints:
        lines.append(f"add_files -fileset constrs_1 [list {tcl_list(constraints)}]")
    if top:
        lines.append(f"set_property top {quote_tcl(top)} [current_fileset]")
    lines.append('update_compile_order -fileset sources_1')
    lines.append('return "sources_updated"')
    return "\n".join(lines)


def bd_open_or_create_tcl(*, design_name: str | None = None, bd_path: Path | None = None, create_if_missing: bool = True) -> str:
    lines = [_bd_helper_tcl()]
    if bd_path is not None:
        lines.extend(
            [
                f"open_bd_design {quote_tcl(bd_path)}",
                'return "bd_design=[current_bd_design]"',
            ]
        )
        return "\n".join(lines)
    if not design_name:
        raise ValueError("Either design_name or bd_path is required")
    lines.extend(
        [
            f"set mcp_bd_name {quote_tcl(design_name)}",
            "set mcp_bd_file [mcp_find_bd_file $mcp_bd_name]",
            "if {$mcp_bd_file ne \"\"} {",
            "  open_bd_design $mcp_bd_file",
            "} else {",
        ]
    )
    if create_if_missing:
        lines.append("  create_bd_design $mcp_bd_name")
    else:
        lines.append('  error "Block design not found: $mcp_bd_name"')
    lines.extend(
        [
            "}",
            'return "bd_design=[current_bd_design]"',
        ]
    )
    return "\n".join(lines)


def bd_summary_tcl(output_path: Path, *, design_name: str | None = None, bd_path: Path | None = None, validate: bool = False) -> str:
    out = quote_tcl(output_path)
    out_string = str(output_path).replace("\\", "/")
    lines = [
        _bd_helper_tcl(),
        f"set mcp_bd_summary_file {out}",
        "set f [open $mcp_bd_summary_file w]",
        "proc mcp_put {f args} { puts $f [join $args \"\\t\"] }",
        "set mcp_bd_files [get_files -quiet -filter {FILE_TYPE == \"Block Designs\"}]",
        "foreach bd_file $mcp_bd_files { mcp_put $f block_design $bd_file }",
    ]
    lines.extend(_bd_select_lines(design_name=design_name, bd_path=bd_path, open_first=True))
    lines.extend(
        [
            "set mcp_current_bd \"\"",
            "catch { set mcp_current_bd [current_bd_design] }",
            "if {$mcp_current_bd eq \"\"} {",
            "  mcp_put $f has_block_design 0",
            "  close $f",
            f"  return \"bd_summary={out_string}\"",
            "}",
            "mcp_put $f has_block_design 1",
            "mcp_put $f current_bd_design $mcp_current_bd",
            "foreach cell [get_bd_cells -quiet] {",
            "  set cell_type \"\"",
            "  set vlnv \"\"",
            "  catch { set cell_type [get_property TYPE $cell] }",
            "  catch { set vlnv [get_property VLNV $cell] }",
            "  mcp_put $f cell $cell $cell_type $vlnv",
            "}",
            "foreach port [get_bd_ports -quiet] {",
            "  set dir \"\"",
            "  set ptype \"\"",
            "  set left \"\"",
            "  set right \"\"",
            "  catch { set dir [get_property DIR $port] }",
            "  catch { set ptype [get_property TYPE $port] }",
            "  catch { set left [get_property LEFT $port] }",
            "  catch { set right [get_property RIGHT $port] }",
            "  mcp_put $f port $port $dir $ptype $left $right",
            "}",
            "foreach port [get_bd_intf_ports -quiet] {",
            "  set mode \"\"",
            "  set vlnv \"\"",
            "  catch { set mode [get_property MODE $port] }",
            "  catch { set vlnv [get_property VLNV $port] }",
            "  mcp_put $f interface_port $port $mode $vlnv",
            "}",
            "foreach net [get_bd_nets -quiet] {",
            "  set endpoints [concat [get_bd_pins -quiet -of_objects $net] [get_bd_ports -quiet -of_objects $net]]",
            "  mcp_put $f net $net [join $endpoints ,]",
            "}",
            "foreach net [get_bd_intf_nets -quiet] {",
            "  set endpoints [concat [get_bd_intf_pins -quiet -of_objects $net] [get_bd_intf_ports -quiet -of_objects $net]]",
            "  mcp_put $f interface_net $net [join $endpoints ,]",
            "}",
        ]
    )
    if validate:
        lines.extend(
            [
                "set mcp_validate_code [catch {validate_bd_design} mcp_validate_result]",
                "mcp_put $f validation $mcp_validate_code $mcp_validate_result",
            ]
        )
    lines.extend(
        [
            "close $f",
            f"return \"bd_summary={out_string}\"",
        ]
    )
    return "\n".join(lines)


def bd_apply_tcl(
    *,
    actions: list[dict[str, Any]],
    design_name: str | None = None,
    bd_path: Path | None = None,
    validate: bool = True,
    save: bool = True,
) -> str:
    lines = [_bd_helper_tcl()]
    lines.extend(_bd_select_lines(design_name=design_name, bd_path=bd_path, open_first=False))
    lines.append("set mcp_bd_actions_applied 0")
    for action in actions:
        lines.extend(_bd_action_lines(action))
        lines.append("incr mcp_bd_actions_applied")
    if validate:
        lines.append("validate_bd_design")
    if save:
        lines.append("save_bd_design")
    lines.append('return "bd_actions_applied=$mcp_bd_actions_applied current_bd_design=[current_bd_design]"')
    return "\n".join(lines)


def bd_validate_tcl(*, design_name: str | None = None, bd_path: Path | None = None, save: bool = False) -> str:
    lines = [_bd_helper_tcl()]
    lines.extend(_bd_select_lines(design_name=design_name, bd_path=bd_path, open_first=False))
    lines.append("validate_bd_design")
    if save:
        lines.append("save_bd_design")
    lines.append('return "bd_validated=[current_bd_design]"')
    return "\n".join(lines)


def bd_generate_tcl(
    *,
    design_name: str | None = None,
    bd_path: Path | None = None,
    target: str = "all",
    make_wrapper: bool = True,
    wrapper_top: bool = True,
) -> str:
    lines = [_bd_helper_tcl()]
    lines.extend(_bd_select_lines(design_name=design_name, bd_path=bd_path, open_first=False))
    lines.extend(
        [
            "save_bd_design",
            "set mcp_bd_file [mcp_current_bd_file]",
            'if {$mcp_bd_file eq ""} { error "Could not resolve current block design file" }',
            f"generate_target {quote_tcl(target)} [get_files $mcp_bd_file]",
            "set mcp_wrapper \"\"",
        ]
    )
    if make_wrapper:
        top_arg = " -top" if wrapper_top else ""
        lines.extend(
            [
                f"set mcp_wrapper [make_wrapper -files [get_files $mcp_bd_file]{top_arg}]",
                'if {$mcp_wrapper ne ""} { add_files -norecurse $mcp_wrapper }',
                "update_compile_order -fileset sources_1",
            ]
        )
    lines.append('return "bd_generated=$mcp_bd_file wrapper=$mcp_wrapper"')
    return "\n".join(lines)


def _bd_helper_tcl() -> str:
    return "\n".join(
        [
            "proc mcp_find_bd_file {bd_name} {",
            "  foreach bd_file [get_files -quiet -filter {FILE_TYPE == \"Block Designs\"}] {",
            "    if {[file rootname [file tail $bd_file]] eq $bd_name} { return $bd_file }",
            "  }",
            "  return \"\"",
            "}",
            "proc mcp_current_bd_file {} {",
            "  set bd_name [current_bd_design]",
            "  return [mcp_find_bd_file $bd_name]",
            "}",
            "proc mcp_bd_endpoint {name} {",
            "  set obj [get_bd_pins -quiet $name]",
            "  if {[llength $obj] == 0} { set obj [get_bd_ports -quiet $name] }",
            "  if {[llength $obj] == 0} { error \"BD pin/port endpoint not found: $name\" }",
            "  return $obj",
            "}",
            "proc mcp_bd_intf_endpoint {name} {",
            "  set obj [get_bd_intf_pins -quiet $name]",
            "  if {[llength $obj] == 0} { set obj [get_bd_intf_ports -quiet $name] }",
            "  if {[llength $obj] == 0} { error \"BD interface endpoint not found: $name\" }",
            "  return $obj",
            "}",
            "proc mcp_bd_object {object_type name} {",
            "  switch -- $object_type {",
            "    cell { set obj [get_bd_cells -quiet $name] }",
            "    pin { set obj [get_bd_pins -quiet $name] }",
            "    port { set obj [get_bd_ports -quiet $name] }",
            "    interface_pin { set obj [get_bd_intf_pins -quiet $name] }",
            "    interface_port { set obj [get_bd_intf_ports -quiet $name] }",
            "    net { set obj [get_bd_nets -quiet $name] }",
            "    interface_net { set obj [get_bd_intf_nets -quiet $name] }",
            "    design { return [current_bd_design] }",
            "    default { error \"Unsupported BD object_type: $object_type\" }",
            "  }",
            "  if {[llength $obj] == 0} { error \"BD object not found: $object_type $name\" }",
            "  return $obj",
            "}",
        ]
    )


def _bd_select_lines(*, design_name: str | None, bd_path: Path | None, open_first: bool) -> list[str]:
    if bd_path is not None:
        return [f"open_bd_design {quote_tcl(bd_path)}"]
    if design_name:
        return [
            f"set mcp_bd_name {quote_tcl(design_name)}",
            "set mcp_bd_file [mcp_find_bd_file $mcp_bd_name]",
            "if {$mcp_bd_file ne \"\"} {",
            "  open_bd_design $mcp_bd_file",
            "} elseif {[catch {current_bd_design $mcp_bd_name}]} {",
            "  error \"Block design not found: $mcp_bd_name\"",
            "}",
        ]
    if open_first:
        return [
            "if {[catch {current_bd_design} mcp_current] || $mcp_current eq \"\"} {",
            "  set mcp_bd_files [get_files -quiet -filter {FILE_TYPE == \"Block Designs\"}]",
            "  if {[llength $mcp_bd_files] > 0} { open_bd_design [lindex $mcp_bd_files 0] }",
            "}",
        ]
    return [
        "if {[catch {current_bd_design} mcp_current] || $mcp_current eq \"\"} {",
        "  error \"No current block design. Call vivado_bd_open_or_create first, or pass design_name/bd_path.\"",
        "}",
    ]


def _bd_action_lines(action: dict[str, Any]) -> list[str]:
    action_type = str(action.get("action") or action.get("type") or "").strip()
    if action_type == "create_cell":
        cell_type = str(action.get("cell_type") or "ip")
        name = _required(action, "name")
        if cell_type == "ip":
            return [f"create_bd_cell -type ip -vlnv {quote_tcl(_required(action, 'vlnv'))} {quote_tcl(name)}"]
        if cell_type == "module":
            return [f"create_bd_cell -type module -reference {quote_tcl(_required(action, 'reference'))} {quote_tcl(name)}"]
        if cell_type == "hier":
            return [f"create_bd_cell -type hier {quote_tcl(name)}"]
        raise ValueError(f"Unsupported create_cell cell_type {cell_type!r}")
    if action_type == "create_port":
        args = ["create_bd_port", "-dir", quote_tcl(_required(action, "direction"))]
        if port_type := action.get("port_type"):
            args.extend(["-type", quote_tcl(str(port_type))])
        if "from" in action:
            args.extend(["-from", str(int(action["from"]))])
        if "to" in action:
            args.extend(["-to", str(int(action["to"]))])
        args.append(quote_tcl(_required(action, "name")))
        return [" ".join(args)]
    if action_type == "create_interface_port":
        return [
            " ".join(
                [
                    "create_bd_intf_port",
                    "-mode",
                    quote_tcl(_required(action, "mode")),
                    "-vlnv",
                    quote_tcl(_required(action, "vlnv")),
                    quote_tcl(_required(action, "name")),
                ]
            )
        ]
    if action_type == "set_property":
        properties = action.get("properties")
        if not isinstance(properties, dict) or not properties:
            raise ValueError("set_property action requires non-empty properties")
        object_type = str(action.get("object_type") or "cell")
        target = "current_bd_design" if object_type == "design" else f"mcp_bd_object {quote_tcl(object_type)} {quote_tcl(_required(action, 'object'))}"
        return [f"set_property -dict [list {_property_list(properties)}] [{target}]"]
    if action_type == "connect_net":
        endpoints = _required_list(action, "endpoints", min_count=2)
        return ["connect_bd_net " + " ".join(f"[mcp_bd_endpoint {quote_tcl(endpoint)}]" for endpoint in endpoints)]
    if action_type == "connect_interface_net":
        endpoints = _required_list(action, "endpoints", min_count=2)
        return ["connect_bd_intf_net " + " ".join(f"[mcp_bd_intf_endpoint {quote_tcl(endpoint)}]" for endpoint in endpoints)]
    if action_type == "assign_address":
        return ["assign_bd_address"]
    if action_type == "apply_automation":
        rule = _required(action, "rule")
        objects = _required_list(action, "objects", min_count=1)
        object_type = str(action.get("object_type") or "interface_pin")
        config = action.get("config") or {}
        if not isinstance(config, dict):
            raise ValueError("apply_automation config must be an object")
        config_arg = f" -config [list {_property_list(config)}]" if config else ""
        object_exprs = " ".join(f"[mcp_bd_object {quote_tcl(object_type)} {quote_tcl(obj)}]" for obj in objects)
        return [f"apply_bd_automation -rule {quote_tcl(rule)}{config_arg} {object_exprs}"]
    if action_type == "validate":
        return ["validate_bd_design"]
    if action_type == "save":
        return ["save_bd_design"]
    raise ValueError(f"Unsupported BD action type {action_type!r}")


def _property_list(properties: dict[str, Any]) -> str:
    items: list[str] = []
    for key, value in properties.items():
        items.append(quote_tcl(str(key)))
        if isinstance(value, bool):
            items.append(quote_tcl("true" if value else "false"))
        else:
            items.append(quote_tcl(str(value)))
    return " ".join(items)


def _required(action: dict[str, Any], key: str) -> str:
    value = action.get(key)
    if value is None or str(value) == "":
        raise ValueError(f"BD action {action.get('action') or action.get('type')!r} requires {key!r}")
    return str(value)


def _required_list(action: dict[str, Any], key: str, *, min_count: int) -> list[str]:
    value = action.get(key)
    if not isinstance(value, list) or len(value) < min_count:
        raise ValueError(f"BD action {action.get('action') or action.get('type')!r} requires at least {min_count} {key}")
    return [str(item) for item in value]


def launch_run_tcl(run_name: str, jobs: int | None, to_step: str | None = None) -> str:
    args = [f"launch_runs {quote_tcl(run_name)}"]
    if to_step:
        args.append(f"-to_step {quote_tcl(to_step)}")
    if jobs:
        args.append(f"-jobs {int(jobs)}")
    lines = [
        " ".join(args),
        f"wait_on_run {quote_tcl(run_name)}",
        f"set status [get_property STATUS [get_runs {quote_tcl(run_name)}]]",
        'return "status=$status"',
    ]
    return "\n".join(lines)


def report_tcl(report_type: str, output_path: Path) -> str:
    commands = {
        "timing_summary": "report_timing_summary",
        "timing_paths": "report_timing",
        "utilization": "report_utilization",
        "drc": "report_drc",
        "power": "report_power",
        "clock_interaction": "report_clock_interaction",
        "messages": "report_messages",
    }
    command = commands.get(report_type)
    if command is None:
        allowed = ", ".join(sorted(commands))
        raise ValueError(f"Unsupported report_type {report_type!r}; expected one of {allowed}")
    return "\n".join(
        [
            f"{command} -file {quote_tcl(output_path)} -force",
            f"return \"report={str(output_path).replace('\\', '/')}\"",
        ]
    )


def project_summary_tcl(output_path: Path) -> str:
    out = quote_tcl(output_path)
    out_string = str(output_path).replace("\\", "/")
    return "\n".join(
        [
            f"set mcp_summary_file {out}",
            "set f [open $mcp_summary_file w]",
            "proc mcp_put {f args} { puts $f [join $args \"\\t\"] }",
            "if {[catch {current_project} project] || $project eq \"\"} {",
            "  mcp_put $f has_project 0",
            "  close $f",
            f"  return \"summary={out_string}\"",
            "}",
            "mcp_put $f has_project 1",
            "mcp_put $f current_project $project",
            "foreach {prop key} {FILE_NAME project_file PART part BOARD_PART board_part TOP top} {",
            "  set value \"\"",
            "  catch { set value [get_property $prop [current_project]] }",
            "  if {$value ne \"\"} { mcp_put $f $key $value }",
            "}",
            "foreach file [get_files -quiet] {",
            "  set file_type \"\"",
            "  catch { set file_type [get_property FILE_TYPE $file] }",
            "  mcp_put $f file $file $file_type",
            "}",
            "foreach run [get_runs -quiet] {",
            "  set status \"\"",
            "  set progress \"\"",
            "  catch { set status [get_property STATUS $run] }",
            "  catch { set progress [get_property PROGRESS $run] }",
            "  mcp_put $f run $run $status $progress",
            "}",
            "foreach ip [get_ips -quiet] { mcp_put $f ip $ip }",
            "foreach bd [get_files -quiet -filter {FILE_TYPE == \"Block Designs\"}] { mcp_put $f block_design $bd }",
            "close $f",
            f"return \"summary={out_string}\"",
        ]
    )
