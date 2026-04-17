"""Template rendering helpers — Jinja2 environment and context injection."""

from __future__ import annotations

from datetime import date as _date

from jinja2 import Environment  # noqa: F811 (re-export used by builder)


_MONTHS_PL = [
    "stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
    "lipca", "sierpnia", "września", "października", "listopada", "grudnia",
]


def format_date_pl(d: _date | None) -> str:
    """Format a Python date as a Polish genitive string: '15 listopada 2024'.

    Returns 'Wkrótce' for year 9999 (TBA placeholder) and '' for None.
    """
    if d is None:
        return ""
    if d.year == 9999:
        return "Wkrótce"
    return f"{d.day} {_MONTHS_PL[d.month - 1]} {d.year}"


def _render(env: Environment, template_name: str, **ctx):
    """Internal renderer: fetch template and render with context."""
    template = env.get_template(template_name)
    return template.render(**ctx)


def abs_url(site_url: str):
    """Return a function that constructs absolute URLs from site_url.

    Args:
        site_url: Base URL (e.g., "http://example.com")

    Returns:
        Callable that takes a relative path and returns absolute URL.
    """

    def _abs_url_fn(path: str) -> str:
        # Normalize path: ensure leading slash
        path = "/" + path.lstrip("/")
        return f"{site_url}{path}" if site_url else path

    return _abs_url_fn


def render_template(env: Environment, template_name: str, *, nav_projects, site_url, **ctx) -> str:
    """Render a Jinja2 template with standard context injection.

    Args:
        env: Jinja2 Environment instance
        template_name: Name of the template to render
        nav_projects: Navigation projects list (injected into context)
        site_url: Base site URL for absolute URL construction
        **ctx: Additional context variables

    Returns:
        Rendered HTML string

    Raises:
        jinja2.TemplateNotFound: If template_name does not exist
    """
    # Build abs_url callable with site_url captured
    abs_url_fn = abs_url(site_url)

    # Combine standard context with user-provided context
    combined_context = {
        "nav_projects": nav_projects,
        "abs_url": abs_url_fn,
        **ctx,
    }

    return _render(env, template_name, **combined_context)


def render_home_page(
    env: Environment,
    out_dir,
    site_url: str,
    nav_projects,
    projects,
    new_editions,
    announcements,
    newest_anytime,
    _render_fn,
    _write_html_fn,
) -> None:
    """Render home page."""
    _write_html_fn(
        out_dir / "index.html",
        _render_fn(
            env,
            "home.html",
            nav_projects=nav_projects,
            site_url=site_url,
            canonical_url=(site_url + "/"),
            projects=projects,
            new_editions=newest_anytime,
            announcements=announcements[:12],
        ),
    )


def render_listing_pages(
    env: Environment,
    out_dir,
    site_url: str,
    nav_projects,
    new_editions,
    announcements,
    newest_anytime,
    _render_fn,
    _write_html_fn,
) -> None:
    """Render listing pages (nowe, zapowiedzi)."""
    _write_html_fn(
        out_dir / "nowe" / "index.html",
        _render_fn(
            env,
            "listing.html",
            nav_projects=nav_projects,
            site_url=site_url,
            canonical_url=(site_url + "/nowe/"),
            title="Nowości",
            description="Najnowsze publikacje.",
            items=new_editions if new_editions else newest_anytime,
        ),
    )
    _write_html_fn(
        out_dir / "zapowiedzi" / "index.html",
        _render_fn(
            env,
            "listing.html",
            nav_projects=nav_projects,
            site_url=site_url,
            canonical_url=(site_url + "/zapowiedzi/"),
            title="Zapowiedzi",
            description="Co nowego nadchodzi w Diablaq.",
            items=announcements,
            empty_message="Już wkrótce ogłosimy kolejne zapowiedzi. Zajrzyj ponownie za jakiś czas."
            if not announcements
            else None,
        ),
    )


def render_content_pages(
    env: Environment,
    out_dir,
    site_url: str,
    nav_projects,
    pages,
    _render_fn,
    _write_html_fn,
) -> None:
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


def render_people_pages(
    env: Environment,
    out_dir,
    site_url: str,
    nav_projects,
    people_with_editions,
    _render_fn,
    _write_html_fn,
) -> None:
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


def render_blog_pages(
    env: Environment,
    out_dir,
    site_url: str,
    nav_projects,
    sorted_blog,
    _render_fn,
    _write_html_fn,
    _build_tags_index_fn,
    slugify_tag_fn,
) -> None:
    """Render blog index, posts, and tag pages."""
    _write_html_fn(
        out_dir / "blog" / "index.html",
        _render_fn(
            env,
            "blog_index.html",
            nav_projects=nav_projects,
            site_url=site_url,
            canonical_url=(site_url + "/blog/"),
            posts=sorted_blog,
        ),
    )
    for post in sorted_blog:
        _write_html_fn(
            out_dir / post.url.strip("/") / "index.html",
            _render_fn(
                env,
                "blog_post.html",
                nav_projects=nav_projects,
                site_url=site_url,
                canonical_url=(site_url + post.url),
                post=post,
                post_tags=[{"name": t, "url": f"/blog/tag/{slugify_tag_fn(t)}/"} for t in post.tags],
            ),
        )
    for tag, items in sorted(_build_tags_index_fn(sorted_blog).items(), key=lambda kv: kv[0].lower()):
        tag_slug = slugify_tag_fn(tag)
        _write_html_fn(
            out_dir / "blog" / "tag" / tag_slug / "index.html",
            _render_fn(
                env,
                "blog_index.html",
                nav_projects=nav_projects,
                site_url=site_url,
                canonical_url=(site_url + f"/blog/tag/{tag_slug}/"),
                posts=sorted(items, key=lambda p: p.date, reverse=True),
            ),
        )


def render_project_pages(
    env: Environment,
    out_dir,
    site_url: str,
    nav_projects,
    projects,
    editions,
    _render_fn,
    _write_html_fn,
    _write_section_fn,
) -> None:
    """Render project pages, editions, and redirects."""
    for pr in projects:
        pr_editions = sorted(
            [e for e in editions if e.project_slug == pr.slug],
            key=lambda e: e.release_date,
            reverse=True,
        )
        project_html = _render_fn(
            env,
            "project.html",
            nav_projects=nav_projects,
            site_url=site_url,
            canonical_url=(site_url + pr.url),
            project=pr,
            editions=pr_editions,
        )
        _write_html_fn(out_dir / pr.url.strip("/") / "index.html", project_html)
        if (
            pr.legacy_landing
            and pr.legacy_path
            and pr.legacy_path.rstrip("/") != pr.url.rstrip("/")
        ):
            _write_html_fn(out_dir / pr.legacy_path.strip("/") / "index.html", project_html)
        legacy_slug_path = f"/{pr.slug}/"
        if legacy_slug_path.rstrip("/") != pr.url.rstrip("/") and not (
            pr.legacy_landing and legacy_slug_path.rstrip("/") == (pr.legacy_path or "").rstrip("/")
        ):
            _write_html_fn(
                out_dir / pr.slug / "index.html",
                _render_fn(
                    env,
                    "redirect.html",
                    nav_projects=nav_projects,
                    site_url=site_url,
                    canonical_url=(site_url + pr.url),
                    to_url=pr.url,
                ),
            )
        if (
            pr.legacy_path
            and pr.legacy_path.rstrip("/") != pr.url.rstrip("/")
            and not pr.legacy_landing
            and pr.legacy_path.rstrip("/") != legacy_slug_path.rstrip("/")
        ):
            _write_html_fn(
                out_dir / pr.legacy_path.strip("/") / "index.html",
                _render_fn(
                    env,
                    "redirect.html",
                    nav_projects=nav_projects,
                    site_url=site_url,
                    canonical_url=(site_url + pr.url),
                    to_url=pr.url,
                ),
            )
        for e in pr_editions:
            if not e.url.endswith("/index/"):
                _write_html_fn(
                    out_dir / e.url.strip("/") / "index.html",
                    _render_fn(
                        env,
                        "edition.html",
                        nav_projects=nav_projects,
                        site_url=site_url,
                        canonical_url=(site_url + e.url),
                        edition=e,
                        project=pr,
                    ),
                )
    _write_section_fn(
        "publikacje",
        title="Publikacje",
        line="diablaq",
        description="Główna linia wydawnicza Diablaq.",
    )
    _write_section_fn(
        "dobre-licho", title="Dobre Licho", line="dobre-licho", description="Imprint dla dzieci."
    )
    _write_section_fn(
        "mecenat",
        title="Mecenat",
        line="mecenat",
        description="Publikacje rozwijane w formule mecenatu.",
    )
    if any(p.line == "studio" for p in projects):
        _write_section_fn(
            "studio",
            title="Studio",
            line="studio",
            description="Produkcje komiksowe dla innych wydawnictw/klientów.",
        )
