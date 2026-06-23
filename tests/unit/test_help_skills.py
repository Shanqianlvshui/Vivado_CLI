from vivado_mcp.help_skills import get_skill, help_topic, list_skills, skills_index
import vivado_mcp.official_docs as official_docs
from vivado_mcp.official_docs import (
    DEFAULT_LOCAL_DOCS_ROOT,
    get_official_reference,
    list_official_references,
    official_docs_index,
    search_official_docs,
)


def test_lists_builtin_skills() -> None:
    skills = list_skills()
    assert {skill["skill_id"] for skill in skills} == {
        "gui-session",
        "project-build-flow",
        "block-design-flow",
        "official-docs-reference",
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

    docs_help = help_topic("official_docs")
    assert "vivado_list_official_references" in docs_help["recommended_tools"]
    assert "vivado_search_official_docs" in docs_help["recommended_tools"]
    assert "vivado://official-docs/index" in docs_help["related_resources"]

    tcl_help = help_topic("raw-tcl")
    assert "vivado_tcl_command_help" in tcl_help["recommended_tools"]
    assert "vivado_review_tcl" in tcl_help["recommended_tools"]


def test_skills_index_contains_resource_uris() -> None:
    index = skills_index()
    assert "vivado://skills/project-build-flow" in index
    assert "vivado://skills/block-design-flow" in index


def test_official_references_cover_core_tcl_and_bd_docs() -> None:
    tcl_docs = {doc["doc_id"] for doc in list_official_references(topic="tcl")}
    bd_docs = {doc["doc_id"] for doc in list_official_references(topic="bd")}
    all_docs = {doc["doc_id"] for doc in list_official_references()}

    assert {"UG835", "UG894", "UG893"}.issubset(tcl_docs)
    assert {"UG835", "UG994", "UG912"}.issubset(bd_docs)
    assert {"UG899", "UG949", "UG1292", "UG973", "UG911", "UG953", "UG974", "UG1046"}.issubset(all_docs)

    ug835 = get_official_reference("ug835")
    assert ug835["resource_uri"] == "vivado://official-docs/ug835"
    assert ug835["url"].startswith("https://docs.amd.com/")
    assert ug835["local_docs_root"] == DEFAULT_LOCAL_DOCS_ROOT
    assert rf"{DEFAULT_LOCAL_DOCS_ROOT}\ug835.pdf" in ug835["local_path_candidates"]

    index = official_docs_index()
    assert "Vivado Official References" in index
    assert "UG835" in index
    assert DEFAULT_LOCAL_DOCS_ROOT in index


def test_search_official_docs_returns_local_snippets(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("VIVADO_MCP_DOCS_ROOT", str(tmp_path))
    (tmp_path / "ug835.pdf").write_bytes(b"%PDF fake")
    monkeypatch.setattr(
        official_docs,
        "_read_document_text",
        lambda path, timeout_seconds=120: "The create_bd_cell command creates block design cells. Use the -type ip option.",
    )

    result = search_official_docs("create_bd_cell", doc_id="ug835")

    assert result["ok"] is True
    assert result["query"] == "create_bd_cell"
    assert result["results"][0]["doc_id"] == "UG835"
    assert "create_bd_cell" in result["results"][0]["snippets"][0]["text"]
