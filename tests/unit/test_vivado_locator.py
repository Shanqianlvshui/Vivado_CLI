from __future__ import annotations

import sys
from pathlib import Path

from vivado_mcp.vivado_locator import check_vivado


def test_check_vivado_with_fake_executable(tmp_path: Path) -> None:
    wrapper = _make_fake_wrapper(tmp_path)
    installation = check_vivado(str(wrapper), timeout_seconds=10)
    assert installation.version == "2023.1"
    assert installation.executable == wrapper.resolve()


def _make_fake_wrapper(tmp_path: Path) -> Path:
    fake = Path(__file__).resolve().parents[1] / "fixtures" / "fake_vivado.py"
    wrapper = tmp_path / "vivado.bat"
    wrapper.write_text(f'@echo off\n"{sys.executable}" "{fake}" %*\n', encoding="utf-8")
    return wrapper

