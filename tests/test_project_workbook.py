from __future__ import annotations

from pathlib import Path

import pytest


WORKBOOK_HEADER = "# Project page workbook\n\n"


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_export_workbook_collects_projects_with_incomplete_editions(tmp_path: Path) -> None:
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
---
Pierwszy akapit.

Drugi akapit.

Trzeci akapit.
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
    _write_file(
        root / "content" / "projects" / "beta" / "editions" / "01.md",
        """\
---
title: "Beta #1"
release_date: 2026-02-01
creators:
  - role: Rysunki
    name: Anna Nowak
specs:
  Liczba stron: "24"
buy_links:
  - label: Kup
    url: https://example.com/beta-1
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

    assert workbook.startswith("<!-- markdownlint-disable-file -->\n")
    assert {entry.slug for entry in entries} == {"alpha", "gamma"}
    assert "## alpha" in workbook
    assert "## gamma" in workbook
    assert "## beta" not in workbook
    assert "<!-- EDITION FRONTMATTER START: alpha/01 -->" in workbook
    assert "<!-- EDITION BODY START: alpha/01 -->" in workbook
    assert "Jan Kowalski" in workbook
    assert "# draft: true | false" in workbook
    assert "# products:" in workbook
    assert "#   - format: zeszyt | miekka | twarda | ebook" in workbook
    assert "alpha/__new_edition__" in workbook


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
    assert not (root / "content" / "projects" / "gamma" / "editions").exists()


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


def test_apply_workbook_writes_updated_edition_files_and_creates_new_ones(tmp_path: Path) -> None:
    from diablaq_site.project_workbook import apply_workbook

    root = tmp_path
    existing_edition_path = root / "content" / "projects" / "alpha" / "editions" / "01.md"
    new_edition_path = root / "content" / "projects" / "alpha" / "editions" / "02.md"

    _write_file(
        root / "content" / "projects" / "alpha" / "project.md",
        """\
---
title: Alpha
line: diablaq
summary: Alpha summary
cover_image: /img/alpha.jpg
---
Pierwszy akapit.

Drugi akapit.

Trzeci akapit.
""",
    )
    _write_file(existing_edition_path, "")

    workbook_path = root / "project-page-workbook.md"
    workbook_path.write_text(
        WORKBOOK_HEADER
        + """\
## alpha
<!-- EDITION FRONTMATTER START: alpha/01 -->
---
title: "Alpha #1"
release_date: 2026-02-01
---
<!-- EDITION FRONTMATTER END: alpha/01 -->

<!-- EDITION BODY START: alpha/01 -->
Pierwszy akapit.

Drugi akapit.
<!-- EDITION BODY END: alpha/01 -->

<!-- EDITION FRONTMATTER START: alpha/02 -->
---
title: "Alpha #2"
release_date: 2026-06-01
---
<!-- EDITION FRONTMATTER END: alpha/02 -->

<!-- EDITION BODY START: alpha/02 -->
Nowe wydanie.
<!-- EDITION BODY END: alpha/02 -->
""",
        encoding="utf-8",
    )

    updated_paths = apply_workbook(root, workbook_path)

    assert updated_paths == [existing_edition_path, new_edition_path]
    assert existing_edition_path.read_text(encoding="utf-8") == (
        "---\n"
        'title: "Alpha #1"\n'
        "release_date: 2026-02-01\n"
        "---\n\n"
        "Pierwszy akapit.\n\n"
        "Drugi akapit.\n"
    )
    assert new_edition_path.read_text(encoding="utf-8") == (
        "---\n"
        'title: "Alpha #2"\n'
        "release_date: 2026-06-01\n"
        "---\n\n"
        "Nowe wydanie.\n"
    )


def test_apply_workbook_rejects_modified_new_edition_template_without_renaming_marker(
    tmp_path: Path,
) -> None:
    from diablaq_site.project_workbook import apply_workbook

    root = tmp_path
    _write_file(
        root / "content" / "projects" / "alpha" / "project.md",
        """\
---
title: Alpha
line: diablaq
summary: Alpha summary
cover_image: /img/alpha.jpg
---
Pierwszy akapit.

Drugi akapit.

Trzeci akapit.
""",
    )

    workbook_path = root / "project-page-workbook.md"
    workbook_path.write_text(
        WORKBOOK_HEADER
        + """\
## alpha
<!-- EDITION FRONTMATTER START: alpha/__new_edition__ -->
---
title: "Alpha #99"
---
<!-- EDITION FRONTMATTER END: alpha/__new_edition__ -->

<!-- EDITION BODY START: alpha/__new_edition__ -->
To nie powinno zostać zapisane.
<!-- EDITION BODY END: alpha/__new_edition__ -->
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="alpha/__new_edition__"):
        apply_workbook(root, workbook_path)

    assert not (root / "content" / "projects" / "alpha" / "editions").exists()


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


def test_apply_workbook_aborts_before_writing_when_edition_frontmatter_is_invalid(
    tmp_path: Path,
) -> None:
    from diablaq_site.project_workbook import apply_workbook

    root = tmp_path
    valid_edition_path = root / "content" / "projects" / "alpha" / "editions" / "01.md"
    invalid_edition_path = root / "content" / "projects" / "alpha" / "editions" / "02.md"

    _write_file(
        root / "content" / "projects" / "alpha" / "project.md",
        """\
---
title: Alpha
line: diablaq
summary: Alpha summary
cover_image: /img/alpha.jpg
---
Pierwszy akapit.

Drugi akapit.

Trzeci akapit.
""",
    )
    _write_file(valid_edition_path, "")

    workbook_path = root / "project-page-workbook.md"
    workbook_path.write_text(
        WORKBOOK_HEADER
        + """\
## alpha
<!-- EDITION FRONTMATTER START: alpha/01 -->
---
title: "Alpha #1"
release_date: 2026-02-01
---
<!-- EDITION FRONTMATTER END: alpha/01 -->

<!-- EDITION BODY START: alpha/01 -->
Poprawny opis.
<!-- EDITION BODY END: alpha/01 -->

<!-- EDITION FRONTMATTER START: alpha/02 -->
---
title: "Alpha #2"
release: zepsute: YAML
---
<!-- EDITION FRONTMATTER END: alpha/02 -->

<!-- EDITION BODY START: alpha/02 -->
Te dane nie powinny zostać zapisane.
<!-- EDITION BODY END: alpha/02 -->
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="alpha/02"):
        apply_workbook(root, workbook_path)

    assert valid_edition_path.read_text(encoding="utf-8") == ""
    assert not invalid_edition_path.exists()


def test_apply_workbook_reports_workbook_lines_and_excerpt_for_invalid_frontmatter(
    tmp_path: Path,
) -> None:
    from diablaq_site.project_workbook import apply_workbook

    root = tmp_path
    _write_file(
        root / "content" / "projects" / "alpha" / "project.md",
        """\
---
title: Alpha
line: diablaq
summary: Alpha summary
cover_image: /img/alpha.jpg
---
""",
    )

    workbook_text = (
        WORKBOOK_HEADER
        + """\
## alpha
<!-- EDITION FRONTMATTER START: alpha/02 -->
---
title: "Alpha #2"
release_date 2026-02-01
summary: "Alpha summary"
---
<!-- EDITION FRONTMATTER END: alpha/02 -->

<!-- EDITION BODY START: alpha/02 -->
Te dane nie powinny zostać zapisane.
<!-- EDITION BODY END: alpha/02 -->
"""
    )
    workbook_path = root / "project-page-workbook.md"
    workbook_path.write_text(workbook_text, encoding="utf-8")

    with pytest.raises(ValueError) as exc_info:
        apply_workbook(root, workbook_path)

    message = str(exc_info.value)
    release_line = workbook_text.splitlines().index("release_date 2026-02-01") + 1
    summary_line = workbook_text.splitlines().index('summary: "Alpha summary"') + 1

    assert "Wydanie alpha/02 ma nieprawidłowy frontmatter" in message
    assert "Kontekst parsera: while scanning a simple key" in message
    assert (
        f"Problem YAML: could not find expected ':' (linia 4, kolumna 1; skoroszyt linia {summary_line})"
        in message
    )
    assert f"linia 3, kolumna 1; skoroszyt linia {release_line}" in message
    assert "Fragment:" in message
    assert "3 | release_date 2026-02-01" in message
    assert '4 | summary: "Alpha summary"' in message
    assert "<unicode string>" not in message


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
