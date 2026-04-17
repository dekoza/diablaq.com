"""Canonical URL generation and tag slugification for diablaq.com static site.

All projects and editions live under /komiksy/ regardless of publication line.
"""

from urllib.parse import quote


def canonical_project_url(*, line: str, slug: str) -> str:
    """Generate canonical URL for a project.

    All lines map to /komiksy/{slug}/ — line is a display grouping, not a URL namespace.
    """
    return f"/komiksy/{slug}/"


def canonical_edition_url(*, line: str, project_slug: str, edition_slug: str) -> str:
    """Generate canonical URL for an edition/issue.

    Special case: edition_slug='index' collapses to the project URL (no /index/ segment).
    This handles the convention where a project with a single volume uses index.md.
    """
    if edition_slug == "index":
        return canonical_project_url(line=line, slug=project_slug)
    return f"/komiksy/{project_slug}/{edition_slug}/"


def slugify_tag(tag: str) -> str:
    """Convert tag text to URL-safe slug using percent-encoding."""
    return quote(tag.strip(), safe="")
