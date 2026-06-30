from vivado_cli.official_docs import search_official_docs
from vivado_cli.tcl_assist import build_tcl_command_help, review_tcl, tcl_command_coverage, tcl_command_doc_topic


def test_tcl_command_help_routes_official_search_by_command_topic(monkeypatch) -> None:
    result = build_tcl_command_help(
        command="create_clock",
        official_search={"ok": True, "topic": "constraints", "results": []},
        official_doc_topic=tcl_command_doc_topic("create_clock"),
    )

    assert result["ok"] is True
    assert result["official_doc_topic"] == "constraints"
    assert result["coverage"]["recommended_tools"] == ["vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli project summary"]


def test_official_search_accepts_command_topic(monkeypatch) -> None:
    calls = []

    def fake_references_for_search(**kwargs):
        calls.append(kwargs)
        return []

    monkeypatch.setattr("vivado_cli.official_docs._references_for_search", fake_references_for_search)

    result = search_official_docs(query="create_clock", topic=tcl_command_doc_topic("create_clock"))

    assert result["ok"] is True
    assert result["topic"] == "constraints"
    assert calls == [{"doc_id": None, "topic": "constraints"}]


def test_review_tcl_flags_high_risk_commands() -> None:
    result = review_tcl(
        """
        create_project demo ./demo -force
        file delete -force ./old_runs
        program_hw_devices [current_hw_device]
        exit
        """
    )

    assert result["risk_level"] == "critical"
    assert result["requires_expect_destructive"] is True
    assert {"file.delete", "hardware.program", "session.exit"}.issubset({risk["risk_id"] for risk in result["risks"]})
    assert "UG908" in result["recommended_docs"]


def test_review_tcl_returns_command_guidance_and_doc_queries() -> None:
    result = review_tcl(
        """
        create_clock -period 3.2 [get_ports sys_clk]
        launch_runs impl_1 -to_step write_bitstream
        create_ip -name axi_gpio -vendor xilinx.com -library ip -module_name gpio_0
        """
    )

    command_reviews = {row["command"]: row for row in result["command_reviews"]}

    assert command_reviews["create_clock"]["official_doc_topic"] == "constraints"
    assert command_reviews["create_clock"]["coverage"]["recommendation"] == "use_expert_tcl_with_review"
    assert command_reviews["launch_runs"]["coverage"]["coverage_status"] == "partial"
    assert command_reviews["create_ip"]["official_doc_topic"] == "ip"
    assert "vivado-cli tcl help create_clock" in result["recommended_tools"]
    assert "vivado-cli run launch" in result["recommended_tools"]
    assert "vivado-cli tcl help create_ip" in result["recommended_tools"]
    assert "UG903" in result["recommended_docs"]
    assert "UG896" in result["recommended_docs"]
    assert {"command": "launch_runs", "topic": "build", "query": "launch_runs", "tool": "vivado-cli tcl help launch_runs"} in result[
        "official_doc_queries"
    ]


def test_review_tcl_flags_nested_and_semicolon_commands() -> None:
    result = review_tcl(
        """
        if {$do_cleanup} { file delete -force ./old_runs }; open_hw_manager
        set fp [open |notepad.exe r]
        reset_project
        delete_bd_objs [get_bd_cells axi_gpio_0]
        """
    )

    risk_ids = {risk["risk_id"] for risk in result["risks"]}
    assert result["risk_level"] == "critical"
    assert result["requires_expect_destructive"] is True
    assert {"file.delete", "external.exec", "project.reset", "delete.objects", "hardware.session"}.issubset(risk_ids)
    assert "UG908" in result["recommended_docs"]
    command_reviews = {row["command"]: row for row in result["command_reviews"]}
    assert "risk:file.delete" in command_reviews["file"]["sources"]
    assert "risk:external.exec" in command_reviews["open"]["sources"]
    assert "risk:hardware.session" in command_reviews["open_hw_manager"]["sources"]
    assert "vivado-cli tcl help file" in result["recommended_tools"]
    assert "vivado-cli session run-tcl --expect-destructive" in result["recommended_tools"]


def test_review_tcl_flags_plural_reset_runs() -> None:
    result = review_tcl("reset_runs {synth_1 impl_1}")

    assert result["risk_level"] == "high"
    assert result["requires_expect_destructive"] is True
    assert {risk["risk_id"] for risk in result["risks"]} == {"project.reset"}


def test_review_tcl_does_not_treat_windows_drive_letters_as_commands() -> None:
    result = review_tcl(
        "open_project -read_only {C:/Workspace/Vivado/project.xpr}\n"
        'return "project=[current_project]"'
    )

    assert result["risk_level"] == "low"
    assert result["requires_expect_destructive"] is False
    assert "open_project" in result["commands"]
    assert "return" in result["commands"]
    assert "current_project" in result["commands"]
    assert "C" not in result["commands"]


def test_tcl_command_coverage_routes_bd_cell_to_reviewed_expert_tcl() -> None:
    coverage = tcl_command_coverage("create_bd_cell")

    assert coverage["coverage_status"] == "raw_tcl"
    assert "vivado-cli bd summary" in coverage["recommended_tools"]
    assert "vivado-cli session run-tcl" in coverage["recommended_tools"]
    assert coverage["recommendation"] == "use_expert_tcl_with_review"


def test_command_coverage_for_priority_cross_flow_commands() -> None:
    create_clock = tcl_command_coverage("create_clock")
    assert create_clock["coverage_status"] == "raw_tcl"
    assert create_clock["recommended_tools"] == ["vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli project summary"]
    assert create_clock["recommendation"] == "use_expert_tcl_with_review"
    assert tcl_command_doc_topic("create_clock") == "constraints"

    launch_runs = tcl_command_coverage("launch_runs")
    assert launch_runs["coverage_status"] == "partial"
    assert "vivado-cli run launch" in launch_runs["recommended_tools"]
    assert tcl_command_doc_topic("launch_runs") == "build"

    launch_simulation = tcl_command_coverage("launch_simulation")
    assert launch_simulation["coverage_status"] == "raw_tcl"
    assert launch_simulation["recommended_tools"] == [
        "vivado-cli project summary",
        "vivado-cli tcl review",
        "vivado-cli session run-tcl",
    ]
    assert tcl_command_doc_topic("launch_simulation") == "simulation"

    read_verilog = tcl_command_coverage("read_verilog")
    assert read_verilog["coverage_status"] == "raw_tcl"
    assert read_verilog["recommended_tools"] == ["vivado-cli tcl review", "vivado-cli session run-tcl"]
    assert tcl_command_doc_topic("read_xdc") == "build"

    synth_design = tcl_command_coverage("synth_design")
    assert synth_design["coverage_status"] == "raw_tcl"
    assert synth_design["recommended_tools"] == ["vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli report"]

    route_design = tcl_command_coverage("route_design")
    assert route_design["coverage_status"] == "raw_tcl"
    assert route_design["recommended_tools"] == ["vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli report"]

    write_checkpoint = tcl_command_coverage("write_checkpoint")
    assert "vivado-cli session run-tcl" in write_checkpoint["recommended_tools"]

    create_ip = tcl_command_coverage("create_ip")
    assert create_ip["coverage_status"] == "raw_tcl"
    assert create_ip["recommended_tools"] == ["vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli project summary"]
    assert tcl_command_doc_topic("create_ip") == "ip"

    upgrade_ip = tcl_command_coverage("upgrade_ip")
    assert upgrade_ip["coverage_status"] == "raw_tcl"
    assert upgrade_ip["recommended_tools"] == ["vivado-cli tcl review", "vivado-cli session run-tcl --expect-destructive", "vivado-cli project summary"]

    generate_target = tcl_command_coverage("generate_target")
    assert "vivado-cli session run-tcl --expect-destructive" in generate_target["recommended_tools"]

    clock_interaction = tcl_command_coverage("report_clock_interaction")
    assert clock_interaction["coverage_status"] == "partial"
    assert clock_interaction["recommended_tools"] == ["vivado-cli report"]
    assert tcl_command_doc_topic("report_clock_interaction") == "reports"

    open_hw = tcl_command_coverage("open_hw_manager")
    assert open_hw["coverage_status"] == "raw_tcl"
    assert open_hw["recommended_tools"] == ["vivado-cli tcl review", "vivado-cli session run-tcl", "vivado-cli session state"]
    assert tcl_command_doc_topic("get_hw_devices") == "hardware"

    refresh_hw = tcl_command_coverage("refresh_hw_device")
    assert refresh_hw["coverage_status"] == "raw_tcl"
    assert refresh_hw["recommended_tools"] == ["vivado-cli tcl review", "vivado-cli session run-tcl"]

    program = tcl_command_coverage("program_hw_devices")
    assert program["coverage_status"] == "raw_tcl"
    assert "vivado-cli session run-tcl --expect-destructive" in program["recommended_tools"]


def test_build_tcl_command_help_combines_docs_vivado_and_coverage() -> None:
    result = build_tcl_command_help(
        command="create_project",
        official_search={
            "ok": True,
            "results": [{"doc_id": "UG835", "snippets": [{"text": "create_project creates a Vivado project."}]}],
        },
        installed_help={"ok": True, "result": "Usage: create_project name dir"},
    )

    assert result["command"] == "create_project"
    assert result["coverage"]["coverage_status"] == "raw_tcl"
    assert result["official_doc_topic"] == "project"
    assert result["installed_vivado_help"]["available"] is True
    assert result["official_search"]["results"][0]["doc_id"] == "UG835"


def test_build_tcl_command_help_rejects_empty_command() -> None:
    result = build_tcl_command_help(command="")

    assert result["ok"] is False
    assert result["coverage"]["coverage_status"] == "invalid"
    assert result["recommended_sequence"][0]["step"] == "provide_command"
