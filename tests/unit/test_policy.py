from pathlib import Path

import pytest

from vivado_mcp.policy import PathPolicy


def test_policy_allows_paths_under_root(tmp_path: Path) -> None:
    policy = PathPolicy([tmp_path])
    child = tmp_path / "new" / "project"
    child.parent.mkdir()
    assert policy.require_under_roots(child, label="project_dir", must_exist=False) == child.resolve()


def test_policy_blocks_paths_outside_root(tmp_path: Path) -> None:
    policy = PathPolicy([tmp_path / "root"])
    outside = tmp_path / "outside"
    outside.mkdir()
    with pytest.raises(PermissionError):
        policy.require_under_roots(outside, label="outside", must_exist=True)


def test_output_name_must_be_filename(tmp_path: Path) -> None:
    policy = PathPolicy([tmp_path])
    assert policy.require_output_name("timing") == "timing.rpt"
    with pytest.raises(PermissionError):
        policy.require_output_name("../timing.rpt")

