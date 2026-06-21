"""Template rendering — Jinja2 environment, context injection, and page renderers.

Infrastructure (format_date_pl, abs_url, render_template, display constants)
lives here. Page-type renderers live in sub-modules.
"""

from __future__ import annotations

from datetime import date
from datetime import date as _date

from jinja2 import Environment  # noqa: F811 (re-export used by builder)

from diablaq_site.rendering.blog import render_blog_pages
from diablaq_site.rendering.catalog import render_catalog_page
from diablaq_site.rendering.home import _build_home_per_line_sections, render_home_page
from diablaq_site.rendering.pages import render_content_pages
from diablaq_site.rendering.people import render_people_pages
from diablaq_site.rendering.project import _group_editions_by_subseries, render_project_pages

from diablaq_site.rendering._constants import (
    _CATALOG_PREVIEW_LIMIT,
    _HOME_CATALOG_CAP,
    _LINE_META,
)

_MONTHS_PL = [
    "stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
    "lipca", "sierpnia", "września", "października", "listopada", "grudnia",
]


def format_date_pl(d: _date | None) -> str:
    """Format a Python date as Polish genitive string: '15 listopada 2024'.

    Returns 'Wkrótce' for year 9999 (TBA placeholder) and '' for None.
    """
    if d is None:
        return ""
    if d.year == 9999:
        return "Wkrótce"
    return f"{d.day} {_MONTHS_PL[d.month - 1]} {d.year}"


def _render(env: Environment, template_name: str, **ctx):
    template = env.get_template(template_name)
    return template.render(**ctx)


def abs_url(site_url: str):
    """Return a function that constructs absolute URLs from site_url."""
    def _abs_url_fn(path: str) -> str:
        path = "/" + path.lstrip("/")
        return f"{site_url}{path}" if site_url else path
    return _abs_url_fn


def render_template(env: Environment, template_name: str, *, nav_projects, site_url, **ctx) -> str:
    """Render a Jinja2 template with standard context injection."""
    abs_url_fn = abs_url(site_url)
    combined_context = {
        "nav_projects": nav_projects,
        "abs_url": abs_url_fn,
        **ctx,
    }
    return _render(env, template_name, **combined_context)


__all__ = [
    "format_date_pl",
    "render_template",
    "render_home_page",
    "render_catalog_page",
    "render_content_pages",
    "render_people_pages",
    "render_blog_pages",
    "render_project_pages",
]
