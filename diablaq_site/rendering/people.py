"""People page renderer — index and individual profiles."""

from __future__ import annotations

from pathlib import Path


def render_people_pages(env, out_dir, site_url, nav_projects, people_with_editions, _render_fn, _write_html_fn) -> None:
    """Render people index and individual person pages."""
    _write_html_fn(
        out_dir / "ludzie" / "index.html",
        _render_fn(
            env,
            "people_index.html",
            nav_projects=nav_projects,
            site_url=site_url,
            canonical_url=(site_url + "/ludzie/"),
            people=people_with_editions,
        ),
    )
    for p in people_with_editions:
        _write_html_fn(
            out_dir / "ludzie" / p.slug / "index.html",
            _render_fn(
                env,
                "person.html",
                nav_projects=nav_projects,
                site_url=site_url,
                canonical_url=(site_url + f"/ludzie/{p.slug}/"),
                person=p,
            ),
        )
    zv = next((p for p in people_with_editions if p.slug == "zvyrke"), None)
    if zv is not None:
        _write_html_fn(
            out_dir / "zvyrke" / "index.html",
            _render_fn(
                env,
                "redirect.html",
                nav_projects=nav_projects,
                site_url=site_url,
                canonical_url=(site_url + f"/ludzie/{zv.slug}/"),
                to_url=f"/ludzie/{zv.slug}/",
            ),
        )
