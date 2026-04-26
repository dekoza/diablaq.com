from __future__ import annotations

from pathlib import Path

from diablaq_site.project_workbook import apply_workbook, export_workbook


WORKBOOK_HEADER = "# Project page workbook\n\n"


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_export_workbook_renders_primary_cover_and_products_templates(tmp_path: Path) -> None:
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
Project body.
""",
    )
    _write_file(
        root / "content" / "projects" / "alpha" / "editions" / "01.md",
        """\
---
title: Alpha #1
release_date: 2026-02-01
primary_cover:
  image: /img/alpha-1.jpg
products:
  - format: zeszyt
---
Edition body.
""",
    )

    workbook_path = root / "project-page-workbook.md"
    export_workbook(root, workbook_path, include_complete=True)
    workbook = workbook_path.read_text(encoding="utf-8")

    assert "primary_cover:" in workbook
    assert "alternate_covers:" in workbook
    assert "products:" in workbook
    assert "cover_id:" in workbook
    assert "numbered_copies:" in workbook
    assert "edition_specs:" in workbook


def test_apply_workbook_writes_new_schema_fields_to_edition_file(tmp_path: Path) -> None:
    root = tmp_path
    project_path = root / "content" / "projects" / "alpha" / "project.md"
    edition_path = root / "content" / "projects" / "alpha" / "editions" / "01.md"
    _write_file(
        project_path,
        """\
---
title: Alpha
line: diablaq
summary: Alpha summary
cover_image: /img/alpha.jpg
---
Project body.
""",
    )
    _write_file(edition_path, "")

    workbook_path = root / "project-page-workbook.md"
    workbook_path.write_text(
        WORKBOOK_HEADER
        + """\
## alpha
<!-- EDITION FRONTMATTER START: alpha/01 -->
---
title: "Alpha #1"
release_date: 2026-02-01
primary_cover:
  label: Standardowa
  image: /img/alpha-1.jpg
  alt: Alpha standard
alternate_covers:
  - id: alt
    label: Limitowana
    image: /img/alpha-1b.jpg
    alt: Alpha limited
creators:
  - role: Rysunki
    name: Alpha Artist
edition_specs:
  "Liczba stron": "24"
products:
  - format: zeszyt
    cover_id: primary
    price: "19,99 zł"
    buy_links:
      - label: Strefa Komiksu
        url: https://example.com/alpha-standard
  - format: zeszyt
    cover_id: alt
    limited: true
    numbered_copies: 333
    buy_links:
      - label: Gildia
        url: https://example.com/alpha-limited
---
<!-- EDITION FRONTMATTER END: alpha/01 -->

<!-- EDITION BODY START: alpha/01 -->
Alpha edition body.
<!-- EDITION BODY END: alpha/01 -->
""",
        encoding="utf-8",
    )

    updated_paths = apply_workbook(root, workbook_path)

    assert updated_paths == [edition_path]
    written = edition_path.read_text(encoding="utf-8")
    assert "primary_cover:" in written
    assert "alternate_covers:" in written
    assert "edition_specs:" in written
    assert "products:" in written
    assert "numbered_copies: 333" in written
