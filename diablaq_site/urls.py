"""
Canonical URL generation and tag slugification for diablaq.com static site.

Functions:
- canonical_project_url: Generate project listing URLs by line/slug
- canonical_edition_url: Generate edition/issue URLs with special index handling
- slugify_tag: URL-safe tag encoding (UTF-8 percent-encoding)
"""

from urllib.parse import quote


def canonical_project_url(*, line: str, slug: str) -> str:
    """Generate canonical URL for a project by publication line.

    Args:
        line: Publication line type (diablaq, dobre-licho, mecenat, studio)
        slug: Project slug (URL-safe identifier)

    Returns:
        Project listing URL with trailing slash (e.g. /publikacje/belzebubs/)
    """
    if line == "diablaq":
        return f"/publikacje/{slug}/"
    if line == "dobre-licho":
        return f"/dobre-licho/{slug}/"
    if line in {"mecenat", "studio"}:
        return f"/{line}/{slug}/"
    # fallback: traktuj jak publikacje
    return f"/publikacje/{slug}/"


def canonical_edition_url(*, line: str, project_slug: str, edition_slug: str) -> str:
    """Generate canonical URL for an edition/issue.

    Special case: edition_slug='index' returns the project URL (no /index/ segment).
    This handles the convention where each project can have an index.md that serves
    as the project's landing page.

    Args:
        line: Publication line type
        project_slug: Project slug
        edition_slug: Edition/issue slug (use 'index' for project landing page)

    Returns:
        Edition URL with trailing slash (e.g. /publikacje/belzebubs/vol-1/)
    """
    # Specjalny przypadek: index.md -> URL projektu (bez /index/)
    if edition_slug == "index":
        return canonical_project_url(line=line, slug=project_slug)

    if line == "diablaq":
        return f"/publikacje/{project_slug}/{edition_slug}/"
    if line == "dobre-licho":
        return f"/dobre-licho/{project_slug}/{edition_slug}/"
    if line in {"mecenat", "studio"}:
        return f"/{line}/{project_slug}/{edition_slug}/"
    return f"/publikacje/{project_slug}/{edition_slug}/"


def slugify_tag(tag: str) -> str:
    """Convert tag text to URL-safe slug using percent-encoding.

    Strips leading/trailing whitespace and applies UTF-8 percent-encoding
    (quote with safe=""). Used for tag URLs where each space becomes %20
    and other special characters are encoded.

    Args:
        tag: Tag name (may contain spaces, special chars, Unicode)

    Returns:
        URL-safe percent-encoded tag slug
    """
    # Do URL-i tagów stosujemy quote (w UTF-8) i zachowujemy spacje jako %20.
    return quote(tag.strip(), safe="")
