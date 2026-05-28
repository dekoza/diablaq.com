from __future__ import annotations

from pathlib import Path

from diablaq_site.builder import build_site


def test_build_renders_products_and_cover_artist_credit(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    work_root = tmp_path / "repo"
    work_root.mkdir(parents=True, exist_ok=True)

    (work_root / "templates").symlink_to(repo_root / "templates")
    (work_root / "css").symlink_to(repo_root / "css")
    (work_root / "img").symlink_to(repo_root / "img")
    (work_root / "content" / "people").mkdir(parents=True, exist_ok=True)

    project_dir = work_root / "content" / "projects" / "alpha"
    (project_dir / "editions").mkdir(parents=True)
    (project_dir / "project.md").write_text(
        """\
---
title: Alpha
line: diablaq
summary: Alpha summary
cover_image: /img/spz2a.jpg
---
Alpha body.
""",
        encoding="utf-8",
    )
    (project_dir / "editions" / "index.md").write_text(
        """\
---
title: Alpha
release_date: 2026-02-01
standalone: true
primary_cover:
  label: Standardowa
  image: /img/spz2a.jpg
  alt: Alpha standard
  artist_name: Weronika Dobrowolska
  person_slug: werka-dobro
alternate_covers:
  - id: limitowana
    label: Limitowana
    image: /img/spz2b.jpg
    alt: Alpha limited
    artist_name: Dawid Malik
    person_slug: dawid-malik
products:
  - format: zeszyt
    cover_id: primary
    price: "19,99 zł"
    buy_links:
      - label: Strefa Komiksu
        url: https://example.com/alpha-standard
  - format: zeszyt
    cover_id: limitowana
    price: "24,99 zł"
    limited: true
    numbered_copies: 333
    buy_links:
      - label: Gildia
        url: https://example.com/alpha-limited
---
Alpha edition body.
""",
        encoding="utf-8",
    )
    (work_root / "content" / "people" / "werka-dobro.md").write_text(
        """\
---
name: Weronika Dobrowolska
credit_name: Werka Dobro
---
Bio.
""",
        encoding="utf-8",
    )
    (work_root / "content" / "people" / "dawid-malik.md").write_text(
        """\
---
name: Dawid Malik
---
Bio.
""",
        encoding="utf-8",
    )

    out_dir = tmp_path / "dist"
    build_site(root=work_root, out_dir=out_dir)

    edition_html = (out_dir / "komiksy" / "alpha" / "index.html").read_text(encoding="utf-8")
    person_html = (out_dir / "ludzie" / "werka-dobro" / "index.html").read_text(encoding="utf-8")

    assert "Alternatywne okładki" in edition_html
    assert "Werka Dobro" in edition_html
    assert "Limitowana" in edition_html
    assert "Gildia" in edition_html
    assert "333" in edition_html
    assert "Okładka standardowa" in person_html or "Okładka" in person_html


def test_build_uses_first_edition_primary_cover_as_project_fallback(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    work_root = tmp_path / "repo"
    work_root.mkdir(parents=True, exist_ok=True)

    (work_root / "templates").symlink_to(repo_root / "templates")
    (work_root / "css").symlink_to(repo_root / "css")
    (work_root / "img").symlink_to(repo_root / "img")
    (work_root / "content" / "people").mkdir(parents=True, exist_ok=True)

    project_dir = work_root / "content" / "projects" / "fallback"
    (project_dir / "editions").mkdir(parents=True)
    (project_dir / "project.md").write_text(
        """\
---
title: Fallback
line: diablaq
summary: Fallback summary
---
Fallback body.
""",
        encoding="utf-8",
    )
    (project_dir / "editions" / "01.md").write_text(
        """\
---
title: Fallback #1
release_date: 2024-01-01
primary_cover:
  image: /img/lunatyk1.jpg
  alt: Fallback first cover
products:
  - format: zeszyt
---
Issue one.
""",
        encoding="utf-8",
    )
    (project_dir / "editions" / "02.md").write_text(
        """\
---
title: Fallback #2
release_date: 2025-01-01
primary_cover:
  image: /img/lunatyk2.jpg
  alt: Fallback second cover
products:
  - format: zeszyt
---
Issue two.
""",
        encoding="utf-8",
    )

    out_dir = tmp_path / "dist"
    build_site(root=work_root, out_dir=out_dir)

    catalog_html = (out_dir / "komiksy" / "index.html").read_text(encoding="utf-8")
    project_html = (out_dir / "komiksy" / "fallback" / "index.html").read_text(encoding="utf-8")

    assert "/img/lunatyk2.jpg" in catalog_html
    assert "/img/lunatyk2.jpg" in project_html
