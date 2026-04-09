from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest


def test_main_exits_with_clear_message_for_invalid_content(monkeypatch, capsys, tmp_path: Path):
    from diablaq_site import cli

    broken_path = tmp_path / "content" / "projects" / "demo" / "project.md"
    broken_path.parent.mkdir(parents=True)
    broken_path.write_text(
        """\
---
title: Demo
summary: Invalid: YAML: value
---
""",
        encoding="utf-8",
    )

    def fake_build_site(*, root: Path, out_dir: Path) -> None:
        raise ValueError(
            f"Nie udało się wczytać frontmatter w {broken_path}: did not find expected key"
        )

    fake_builder = types.SimpleNamespace(build_site=fake_build_site)
    monkeypatch.setitem(sys.modules, "diablaq_site.builder", fake_builder)
    monkeypatch.setattr(
        "sys.argv",
        ["diablaq-build", "--root", str(tmp_path), "--out", str(tmp_path / "dist")],
    )

    with pytest.raises(SystemExit, match="1"):
        cli.main()

    captured = capsys.readouterr()
    assert "Błąd treści wejściowych:" in captured.err
    assert str(broken_path) in captured.err
    assert "did not find expected key" in captured.err
