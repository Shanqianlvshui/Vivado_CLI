from vivado_mcp.help_skills import get_skill, help_topic, list_skills, skills_index


def test_lists_builtin_skills() -> None:
    skills = list_skills()
    assert {skill["skill_id"] for skill in skills} == {
        "gui-session",
        "project-build-flow",
        "block-design-flow",
        "raw-tcl-expert",
    }


def test_reads_skill_body() -> None:
    skill = get_skill("raw-tcl-expert")
    assert skill["resource_uri"] == "vivado://skills/raw-tcl-expert"
    assert "Raw Tcl" in skill["body"]


def test_help_topic_points_to_skill() -> None:
    help_result = help_topic("gui_session")
    assert help_result["related_resources"] == ["vivado://skills/gui-session"]

    bd_help = help_topic("bd")
    assert bd_help["related_resources"] == ["vivado://skills/block-design-flow"]


def test_skills_index_contains_resource_uris() -> None:
    index = skills_index()
    assert "vivado://skills/project-build-flow" in index
    assert "vivado://skills/block-design-flow" in index
