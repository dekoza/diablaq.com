"""Template rendering helpers — Jinja2 environment and context injection.

This module is a re-export barrel. Infrastructure (format_date_pl, abs_url,
render_template) lives in rendering/__init__.py. Page-type renderers live in
rendering/home.py, rendering/catalog.py, etc.
"""

from __future__ import annotations

from diablaq_site.rendering import (
    format_date_pl,
    render_blog_pages,
    render_catalog_page,
    render_content_pages,
    render_home_page,
    render_people_pages,
    render_project_pages,
    render_template,
)
from diablaq_site.rendering.home import _build_home_per_line_sections
from diablaq_site.rendering.project import _group_editions_by_subseries

__all__ = [
    "format_date_pl",
    "render_template",
    "_build_home_per_line_sections",
    "_group_editions_by_subseries",
    "render_home_page",
    "render_catalog_page",
    "render_content_pages",
    "render_people_pages",
    "render_blog_pages",
    "render_project_pages",
]
