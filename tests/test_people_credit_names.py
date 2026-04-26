from __future__ import annotations

from pathlib import Path

from diablaq_site.builder import build_site


def _write_one_shot(
    projects_dir: Path,
    *,
    slug: str,
    title: str,
    summary: str,
    creator_name: str,
    person_slug: str,
    featured: bool = False,
) -> None:
    project_dir = projects_dir / slug
    (project_dir / "editions").mkdir(parents=True, exist_ok=True)
    (project_dir / "project.md").write_text(
        (
            "---\n"
            f'title: "{title}"\n'
            "line: diablaq\n"
            f'summary: "{summary}"\n'
            "cover_image: /img/mg_cudowni_1.jpg\n"
            "---\n"
            "\n"
            f"{summary}\n"
        ),
        encoding="utf-8",
    )
    (project_dir / "editions" / "index.md").write_text(
        (
            "---\n"
            f'title: "{title}"\n'
            "release_date: 2024-11-01\n"
            "standalone: true\n"
            f"featured: {'true' if featured else 'false'}\n"
            "primary_cover:\n"
            "  image: /img/mg_cudowni_1.jpg\n"
            f'  alt: "{title} – okładka"\n'
            "creators:\n"
            "  - role: Rysunki\n"
            f'    name: "{creator_name}"\n'
            f'    person_slug: "{person_slug}"\n'
            "products:\n"
            "  - format: zeszyt\n"
            "    buy_links:\n"
            '      - label: "Kup"\n'
            '        url: "https://example.com/kup"\n'
            "---\n"
            "\n"
            f"Opis wydania {title}.\n"
        ),
        encoding="utf-8",
    )



def _build_fixture_site(tmp_path: Path) -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    work_root = tmp_path / "repo"
    work_root.mkdir(parents=True, exist_ok=True)

    (work_root / "templates").symlink_to(repo_root / "templates")
    (work_root / "css").symlink_to(repo_root / "css")
    (work_root / "img").symlink_to(repo_root / "img")

    projects_dir = work_root / "content" / "projects"
    people_dir = work_root / "content" / "people"
    people_dir.mkdir(parents=True, exist_ok=True)

    _write_one_shot(
        projects_dir,
        slug="werka-dobro-test",
        title="Werka Dobro Test",
        summary="Komiks przypisany do Werki Dobro.",
        creator_name="Weronika Dobrowolska",
        person_slug="werka-dobro",
        featured=True,
    )
    _write_one_shot(
        projects_dir,
        slug="zvyrke-test",
        title="Zvyrke Test",
        summary="Komiks przypisany do Zvyrke.",
        creator_name="Zvyrke",
        person_slug="zvyrke",
    )

    (people_dir / "werka-dobro.md").write_text(
        """\
---
name: Weronika Dobrowolska
credit_name: Werka Dobro
---

Bio Werki.
""",
        encoding="utf-8",
    )
    (people_dir / "zvyrke.md").write_text(
        """\
---
credit_name: Zvyrke
---

Bio Zvyrke.
""",
        encoding="utf-8",
    )

    out_dir = tmp_path / "dist"
    build_site(root=work_root, out_dir=out_dir)
    return out_dir



def test_builder_uses_credit_names_on_comic_pages_and_person_pages(tmp_path: Path) -> None:
    """Credit names should render on works, while person pages keep full names when available."""
    out_dir = _build_fixture_site(tmp_path)

    home_html = (out_dir / "index.html").read_text(encoding="utf-8")
    edition_html = (
        out_dir / "komiksy" / "werka-dobro-test" / "index.html"
    ).read_text(encoding="utf-8")
    werka_html = (out_dir / "ludzie" / "werka-dobro" / "index.html").read_text(
        encoding="utf-8"
    )
    zvyrke_html = (out_dir / "ludzie" / "zvyrke" / "index.html").read_text(
        encoding="utf-8"
    )
    people_index_html = (out_dir / "ludzie" / "index.html").read_text(encoding="utf-8")

    assert "Werka Dobro" in home_html
    assert "Weronika Dobrowolska" not in home_html
    assert '<a href="/ludzie/werka-dobro/">Werka Dobro</a>' in edition_html
    assert "<h1>Weronika Dobrowolska</h1>" in werka_html
    assert "Publikuje jako: Werka Dobro" in werka_html
    assert "<h1>Zvyrke</h1>" in zvyrke_html
    assert "Pseudonim artystyczny: Zvyrke" in zvyrke_html
    assert '>Weronika Dobrowolska<' in people_index_html
    assert '>Zvyrke<' in people_index_html
