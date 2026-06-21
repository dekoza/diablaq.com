"""Catalog page renderer — /komiksy/ overview and sub-line pages."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from diablaq_site.models import Project
from diablaq_site.rendering._constants import _CATALOG_PREVIEW_LIMIT, _LINE_META


def render_catalog_page(
    env,
    out_dir,
    site_url,
    nav_projects,
    projects,
    editions,
    _render_fn,
    _write_html_fn,
) -> None:
    """Render the /komiksy/ overview and one sub-line page per publication line.

    Overview (/komiksy/): each line shows up to _CATALOG_PREVIEW_LIMIT projects
    sorted by newest edition date (descending), with a link to the full sub-line page.
    Sub-line pages (/komiksy/{slug}/): show ALL projects, grouped into two sections:
    "Zapowiedzi" (TBA projects first) and released projects sorted by date descending.
    """
    project_latest_date: dict[str, date] = {}
    for e in editions:
        if e.release_date.year == 9999:
            continue
        slug = e.project_slug
        if slug not in project_latest_date or e.release_date > project_latest_date[slug]:
            project_latest_date[slug] = e.release_date

    def _project_sort_key(p: Project) -> date:
        return project_latest_date.get(p.slug, date.min)

    lines_order = ["diablaq", "dobre-licho", "mecenat", "studio"]
    display_projects = [p for p in projects if p.kind == "title"]

    all_line_ids: list[str] = list(lines_order)
    used = set(lines_order)
    for p in display_projects:
        if p.line not in used:
            used.add(p.line)
            all_line_ids.append(p.line)

    all_groups: list[dict] = []
    for line in all_line_ids:
        line_projects = sorted(
            [p for p in display_projects if p.line == line],
            key=_project_sort_key,
            reverse=True,
        )
        if not line_projects:
            continue
        meta = _LINE_META.get(line, {"label": line, "url_slug": line, "description": ""})
        url_slug = meta["url_slug"]
        all_groups.append({
            "id": line,
            "label": meta["label"],
            "description": meta["description"],
            "url": f"/komiksy/{url_slug}/",
            "projects": line_projects,
            "total": len(line_projects),
        })

    overview_groups = [
        {**g, "projects": g["projects"][:_CATALOG_PREVIEW_LIMIT]}
        for g in all_groups
    ]
    _write_html_fn(
        out_dir / "komiksy" / "index.html",
        _render_fn(
            env,
            "catalog.html",
            nav_projects=nav_projects,
            site_url=site_url,
            canonical_url=(site_url + "/komiksy/"),
            groups=overview_groups,
        ),
    )

    for group in all_groups:
        url_slug = _LINE_META.get(group["id"], {"url_slug": group["id"]})["url_slug"]
        tba_projects = [p for p in group["projects"] if project_latest_date.get(p.slug) is None]
        released_projects = [p for p in group["projects"] if project_latest_date.get(p.slug) is not None]
        _write_html_fn(
            out_dir / "komiksy" / url_slug / "index.html",
            _render_fn(
                env,
                "catalog_line.html",
                nav_projects=nav_projects,
                site_url=site_url,
                canonical_url=(site_url + f"/komiksy/{url_slug}/"),
                group={**group, "tba_projects": tba_projects, "released_projects": released_projects},
                breadcrumb=[{"label": "Komiksy", "url": "/komiksy/"}],
            ),
        )
