from vivado_mcp.tcl_assist import build_tcl_command_help, review_tcl, tcl_command_coverage


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


def test_tcl_command_coverage_prefers_structured_tool_for_bd_cell() -> None:
    coverage = tcl_command_coverage("create_bd_cell")

    assert coverage["coverage_status"] == "partial"
    assert "vivado_bd_apply" in coverage["recommended_tools"]
    assert coverage["recommendation"] == "prefer_structured_tool_when_possible"


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
    assert result["coverage"]["coverage_status"] == "partial"
    assert result["installed_vivado_help"]["available"] is True
    assert result["official_search"]["results"][0]["doc_id"] == "UG835"


def test_build_tcl_command_help_rejects_empty_command() -> None:
    result = build_tcl_command_help(command="")

    assert result["ok"] is False
    assert result["coverage"]["coverage_status"] == "invalid"
    assert result["recommended_sequence"][0]["step"] == "provide_command"
