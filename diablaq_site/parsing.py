"""Parsing functions for diablaq.com content — frontmatter, dates, metadata validation.

This module is a re-export barrel. Field-level parsers live in fields.py;
content-loading orchestration lives in load.py.
"""

from __future__ import annotations

# ── Field-level parsers (pure functions over dicts) ──────────────────────
from diablaq_site.fields import (
    _ALLOWED_PRODUCT_FORMATS,
    _ALLOWED_PROJECT_KINDS,
    _normalize_isbn13,
    as_str,
    coerce_str_list,
    derive_flags,
    ensure_no_legacy_edition_fields,
    parse_buy_links,
    parse_cover_list,
    parse_creators,
    parse_date,
    parse_image_list,
    parse_optional_date,
    parse_primary_cover,
    parse_products,
    parse_specs,
    pick_cover,
    read_markdown_file,
)

# ── Content loaders (filesystem I/O + orchestration) ─────────────────────
from diablaq_site.load import (
    apply_person_credit_names,
    build_nav_projects,
    build_people_index,
    build_tags_index,
    load_blog_posts,
    load_pages,
    load_people,
    load_projects_and_editions,
)

__all__ = [
    # Field parsers
    "_ALLOWED_PRODUCT_FORMATS",
    "_ALLOWED_PROJECT_KINDS",
    "_normalize_isbn13",
    "as_str",
    "coerce_str_list",
    "derive_flags",
    "ensure_no_legacy_edition_fields",
    "parse_buy_links",
    "parse_cover_list",
    "parse_creators",
    "parse_date",
    "parse_image_list",
    "parse_optional_date",
    "parse_primary_cover",
    "parse_products",
    "parse_specs",
    "pick_cover",
    "read_markdown_file",
    # Content loaders
    "apply_person_credit_names",
    "build_nav_projects",
    "build_people_index",
    "build_tags_index",
    "load_blog_posts",
    "load_pages",
    "load_people",
    "load_projects_and_editions",
]
