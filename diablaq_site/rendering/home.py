"""Home page renderer."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from diablaq_site.models import Edition, Project
from diablaq_site.rendering._constants import _HOME_CATALOG_CAP, _LINE_META


def _build_home_per_line_sections(
    projects,
    editions,
    hero_slides: list,
    newest_anytime,
) -> list[dict]:
    """Build per-line edition sections for the homepage mini-catalog.

    Each section shows up to _HOME_CATALOG_CAP of the most recently released
    editions for that line, sorted newest first.  Excludes:
    - all hero carousel slides
    - editions already shown in newest_anytime ("Ostatnio wydane")
    - announcements (is_announcement=True)
    - TBA editions (release_date.year == 9999)

    Returns a list of dicts with keys: id, label, url, editions, has_more.
    Only lines that have at least one remaining edition after exclusions are included.
    """
    excluded = set()
    for slide in hero_slides:
        excluded.add(slide.url)
    for e in newest_anytime:
        excluded.add(e.url)

    slug_to_line = {p.slug: p.line for p in projects}

    by_line: dict[str, list] = {}
    for e in editions:
        if e.is_announcement or e.release_date.year == 9999 or e.url in excluded:
            continue
        line = slug_to_line.get(e.project_slug)
        if line is None:
            continue
        by_line.setdefault(line, []).append(e)

    for line in by_line:
        by_line[line].sort(key=lambda e: e.release_date, reverse=True)

    lines_order = ["diablaq", "dobre-licho", "mecenat", "studio"]
    seen_lines: set[str] = set()
    sections = []

    for line in lines_order + [l for l in by_line if l not in lines_order]:
        if line in seen_lines or line not in by_line:
            continue
        seen_lines.add(line)
        meta = _LINE_META.get(line, {"label": line, "url_slug": line, "description": ""})
        all_eds = by_line[line]
        sections.append({
            "id": line,
            "label": meta["label"],
            "url": f"/komiksy/{meta['url_slug']}/",
            "editions": all_eds[:_HOME_CATALOG_CAP],
            "has_more": len(all_eds) > _HOME_CATALOG_CAP,
        })

    return sections


def render_home_page(
    env,
    out_dir,
    site_url,
    nav_projects,
    projects,
    new_editions,
    announcements,
    newest_anytime,
    hero_slides,
    per_line_sections,
    _render_fn,
    _write_html_fn,
) -> None:
    """Render home page."""
    hero_edition = hero_slides[0] if hero_slides else None
    _write_html_fn(
        out_dir / "index.html",
        _render_fn(
            env,
            "home.html",
            nav_projects=nav_projects,
            site_url=site_url,
            canonical_url=(site_url + "/"),
            announcements=announcements,
            newest_anytime=newest_anytime,
            hero_slides=hero_slides,
            hero_edition=hero_edition,
            per_line_sections=per_line_sections,
        ),
    )
