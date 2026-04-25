from __future__ import annotations

from pathlib import Path

from diablaq_site.builder import build_site


def _write_project(
    projects_dir: Path,
    *,
    slug: str,
    project_md: str,
    edition_slug: str | None = None,
    edition_md: str | None = None,
) -> None:
    project_dir = projects_dir / slug
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "project.md").write_text(project_md, encoding="utf-8")
    if edition_slug is None or edition_md is None:
        return
    editions_dir = project_dir / "editions"
    editions_dir.mkdir(exist_ok=True)
    (editions_dir / f"{edition_slug}.md").write_text(edition_md, encoding="utf-8")


def _build_fixture_site(tmp_path: Path) -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    work_root = tmp_path / "repo"
    work_root.mkdir(parents=True, exist_ok=True)

    (work_root / "templates").symlink_to(repo_root / "templates")
    (work_root / "css").symlink_to(repo_root / "css")
    (work_root / "img").symlink_to(repo_root / "img")

    projects_dir = work_root / "content" / "projects"
    _write_project(
        projects_dir,
        slug="midguard",
        project_md=(
            "---\n"
            'title: "MidGuard™"\n'
            "line: diablaq\n"
            "kind: universe\n"
            'summary: "Mroczne uniwersum science fantasy."\n'
            "cover_image: /img/midguard-logo.webp\n"
            "---\n"
            "\n"
            "Uniwersum **MidGuard™** skupia niezależne tytuły.\n"
        ),
    )
    _write_project(
        projects_dir,
        slug="cudowni",
        project_md=(
            "---\n"
            'title: "Cudowni"\n'
            "line: diablaq\n"
            "kind: title\n"
            "universe_slug: midguard\n"
            'summary: "Pierwsza opowieść z tego świata."\n'
            "cover_image: /img/mg_cudowni_1.jpg\n"
            "---\n"
            "\n"
            "Jednotomowa historia osadzona w MidGuard™.\n"
        ),
        edition_slug="index",
        edition_md=(
            "---\n"
            'title: "Cudowni"\n'
            "release_date: 2024-11-01\n"
            "standalone: true\n"
            "cover_image: /img/mg_cudowni_1.jpg\n"
            'cover_alt: "Cudowni – okładka"\n'
            "buy_links:\n"
            '  - label: "Kup"\n'
            '    url: "https://example.com/cudowni"\n'
            "---\n"
            "\n"
            "Pierwszy tom Cudownych.\n"
        ),
    )

    out_dir = tmp_path / "dist"
    build_site(root=work_root, out_dir=out_dir)
    return out_dir


def test_catalog_lists_titles_but_not_universes(tmp_path: Path) -> None:
    """Universes should disappear from catalog cards; titles remain."""
    out_dir = _build_fixture_site(tmp_path)

    catalog_html = (out_dir / "komiksy" / "index.html").read_text(encoding="utf-8")

    assert "Cudowni" in catalog_html
    assert "Pierwsza opowieść z tego świata." in catalog_html
    assert "MidGuard™" not in catalog_html


def test_universe_page_lists_related_titles(tmp_path: Path) -> None:
    """Universe pages should render dedicated copy and related title cards."""
    out_dir = _build_fixture_site(tmp_path)

    universe_html = (out_dir / "komiksy" / "midguard" / "index.html").read_text(encoding="utf-8")

    assert "Uniwersum" in universe_html
    assert "Tytuły w uniwersum" in universe_html
    assert "Cudowni" in universe_html
    assert "/komiksy/cudowni/" in universe_html
    assert "Wydania" not in universe_html


def test_title_page_links_back_to_universe(tmp_path: Path) -> None:
    """Title pages should expose the universe relationship in navigation/meta."""
    out_dir = _build_fixture_site(tmp_path)

    title_html = (out_dir / "komiksy" / "cudowni" / "index.html").read_text(encoding="utf-8")

    assert "MidGuard™" in title_html
    assert "/komiksy/midguard/" in title_html
    assert "Uniwersum" in title_html
