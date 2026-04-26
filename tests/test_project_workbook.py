from __future__ import annotations

from pathlib import Path

import pytest


WORKBOOK_HEADER = "# Project page workbook\n\n"


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_export_workbook_collects_only_incomplete_projects(tmp_path: Path) -> None:
    from diablaq_site.project_workbook import export_workbook

    root = tmp_path

    _write_file(
        root / "content" / "projects" / "alpha" / "project.md",
        """\
---
title: Alpha
line: diablaq
summary: Alpha summary
cover_image: /img/alpha.jpg
# legacy_path:
---
""",
    )
    _write_file(
        root / "content" / "projects" / "alpha" / "editions" / "01.md",
        """\
---
title: "Alpha #1"
release_date: 2026-02-01
creators:
  - role: Scenariusz
    name: Jan Kowalski
---
Pierwszy zeszyt testowy.
""",
    )
    _write_file(
        root / "content" / "projects" / "beta" / "project.md",
        """\
---
title: Beta
line: studio
summary: Beta summary
cover_image: /img/beta.jpg
---
Pierwszy akapit.

Drugi akapit.

Trzeci akapit.
""",
    )
    _write_file(root / "content" / "projects" / "gamma" / "project.md", "")

    workbook_path = root / "project-page-workbook.md"
    entries = export_workbook(root, workbook_path)
    workbook = workbook_path.read_text(encoding="utf-8")

    assert {entry.slug for entry in entries} == {"alpha", "gamma"}
    assert "## alpha" in workbook
    assert "## gamma" in workbook
    assert "## beta" not in workbook
    assert "# legacy_path:" in workbook
    assert '<!-- FRONTMATTER START: gamma -->' in workbook
    assert 'title: "Gamma"' in workbook
    assert "Alpha #1" in workbook
    assert "Jan Kowalski" in workbook


def test_apply_workbook_leaves_untouched_exported_templates_alone(tmp_path: Path) -> None:
    from diablaq_site.project_workbook import apply_workbook, export_workbook

    root = tmp_path
    project_path = root / "content" / "projects" / "gamma" / "project.md"
    _write_file(project_path, "")

    workbook_path = root / "project-page-workbook.md"
    export_workbook(root, workbook_path)

    updated_paths = apply_workbook(root, workbook_path)

    assert updated_paths == []
    assert project_path.read_text(encoding="utf-8") == ""


def test_apply_workbook_writes_updated_project_files(tmp_path: Path) -> None:
    from diablaq_site.project_workbook import apply_workbook

    root = tmp_path
    project_path = root / "content" / "projects" / "gamma" / "project.md"
    _write_file(project_path, "")

    workbook_path = root / "project-page-workbook.md"
    workbook_path.write_text(
        WORKBOOK_HEADER
        + """\
## gamma
<!-- FRONTMATTER START: gamma -->
---
title: "Gamma"
line: studio
summary: Krótki opis serii.
cover_image: /img/gamma.jpg
---
<!-- FRONTMATTER END: gamma -->

<!-- BODY START: gamma -->
Pierwszy akapit.

Drugi akapit.
<!-- BODY END: gamma -->
""",
        encoding="utf-8",
    )

    updated_paths = apply_workbook(root, workbook_path)

    assert updated_paths == [project_path]
    assert project_path.read_text(encoding="utf-8") == (
        "---\n"
        'title: "Gamma"\n'
        "line: studio\n"
        "summary: Krótki opis serii.\n"
        "cover_image: /img/gamma.jpg\n"
        "---\n\n"
        "Pierwszy akapit.\n\n"
        "Drugi akapit.\n"
    )


def test_apply_workbook_aborts_before_writing_when_frontmatter_is_invalid(tmp_path: Path) -> None:
    from diablaq_site.project_workbook import apply_workbook

    root = tmp_path
    alpha_path = root / "content" / "projects" / "alpha" / "project.md"
    beta_path = root / "content" / "projects" / "beta" / "project.md"
    _write_file(alpha_path, "")
    _write_file(beta_path, "")

    workbook_path = root / "project-page-workbook.md"
    workbook_path.write_text(
        WORKBOOK_HEADER
        + """\
## alpha
<!-- FRONTMATTER START: alpha -->
---
title: Alpha
line: diablaq
summary: Poprawne dane
cover_image: /img/alpha.jpg
---
<!-- FRONTMATTER END: alpha -->

<!-- BODY START: alpha -->
Poprawny opis.
<!-- BODY END: alpha -->

## beta
<!-- FRONTMATTER START: beta -->
---
title: Beta
summary: zepsute: YAML
---
<!-- FRONTMATTER END: beta -->

<!-- BODY START: beta -->
Te dane nie powinny zostać zapisane.
<!-- BODY END: beta -->
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="beta"):
        apply_workbook(root, workbook_path)

    assert alpha_path.read_text(encoding="utf-8") == ""
    assert beta_path.read_text(encoding="utf-8") == ""


def test_main_exports_workbook_to_default_path(monkeypatch, capsys, tmp_path: Path) -> None:
    from diablaq_site import project_workbook

    _write_file(
        tmp_path / "content" / "projects" / "delta" / "project.md",
        """\
---
title: Delta
line: diablaq
summary: Delta summary
cover_image: /img/delta.jpg
---
""",
    )

    monkeypatch.setattr(
        "sys.argv",
        ["diablaq-project-workbook", "export", "--root", str(tmp_path)],
    )

    project_workbook.main()

    workbook_path = tmp_path / "project-page-workbook.md"
    captured = capsys.readouterr()

    assert workbook_path.exists()
    assert "Zapisano skoroszyt" in captured.out
