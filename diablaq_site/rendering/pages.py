"""Static content page renderer."""

from __future__ import annotations

from pathlib import Path


def render_content_pages(env, out_dir, site_url, nav_projects, pages, _render_fn, _write_html_fn) -> None:
    """Render static content pages."""
    for page in pages:
        _write_html_fn(
            out_dir / page.slug / "index.html",
            _render_fn(
                env,
                "page.html",
                nav_projects=nav_projects,
                site_url=site_url,
                canonical_url=(site_url + f"/{page.slug}/"),
                page=page,
            ),
        )
