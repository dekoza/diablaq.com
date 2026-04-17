"""Template rendering helpers — Jinja2 environment and context injection."""

from __future__ import annotations

from datetime import date as _date

from jinja2 import Environment  # noqa: F811 (re-export used by builder)


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


def render_home_page(
    env,
    out_dir,
    site_url,
    nav_projects,
    projects,
    new_editions,
    announcements,
    newest_anytime,
    hero_edition,
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
            new_editions=new_editions,
            announcements=announcements[:12],
            newest_anytime=newest_anytime,
            hero_edition=hero_edition,
        ),
    )


def render_catalog_page(
    env,
    out_dir,
    site_url,
    nav_projects,
    projects,
    _render_fn,
    _write_html_fn,
) -> None:
    """Render the unified catalog page (/komiksy/) with projects grouped by line."""
    lines_order = ["diablaq", "dobre-licho", "mecenat", "studio"]
    lines_labels = {
        "diablaq": "Główna linia",
        "dobre-licho": "Dobre Licho",
        "mecenat": "Mecenat",
        "studio": "Studio",
    }
    groups = []
    for line in lines_order:
        line_projects = [p for p in projects if p.line == line]
        if line_projects:
            groups.append({
                "id": line,
                "label": lines_labels.get(line, line),
                "projects": line_projects,
            })
    # Any unlisted lines
    used = set(lines_order)
    for p in projects:
        if p.line not in used:
            used.add(p.line)
            groups.append({
                "id": p.line,
                "label": p.line,
                "projects": [pp for pp in projects if pp.line == p.line],
            })

    _write_html_fn(
        out_dir / "komiksy" / "index.html",
        _render_fn(
            env,
            "catalog.html",
            nav_projects=nav_projects,
            site_url=site_url,
            canonical_url=(site_url + "/komiksy/"),
            groups=groups,
        ),
    )


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


def render_blog_pages(
    env, out_dir, site_url, nav_projects, sorted_blog,
    _render_fn, _write_html_fn, _build_tags_index_fn, slugify_tag_fn,
) -> None:
    """Render blog index, posts, and tag pages."""
    _write_html_fn(
        out_dir / "blog" / "index.html",
        _render_fn(
            env, "blog_index.html",
            nav_projects=nav_projects, site_url=site_url,
            canonical_url=(site_url + "/blog/"),
            posts=sorted_blog,
        ),
    )
    for post in sorted_blog:
        _write_html_fn(
            out_dir / post.url.strip("/") / "index.html",
            _render_fn(
                env, "blog_post.html",
                nav_projects=nav_projects, site_url=site_url,
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
                env, "blog_index.html",
                nav_projects=nav_projects, site_url=site_url,
                canonical_url=(site_url + f"/blog/tag/{tag_slug}/"),
                posts=sorted(items, key=lambda p: p.date, reverse=True),
            ),
        )


def render_project_pages(
    env, out_dir, site_url, nav_projects, projects, editions, _render_fn, _write_html_fn,
) -> None:
    """Render project pages and all edition pages.

    One-shot comics (edition_slug='index') render at the project URL using edition.html.
    Multi-edition projects render a project page + individual edition pages.
    Legacy path redirects are no longer HTML pages — handled by _redirects file.
    """
    for pr in projects:
        pr_editions = sorted(
            [e for e in editions if e.project_slug == pr.slug],
            key=lambda e: e.release_date,
            reverse=True,
        )

        # Check if this project has an index edition (collapses to project URL)
        index_edition = next((e for e in pr_editions if e.url == pr.url), None)

        if index_edition:
            # One-shot: render edition.html at the project URL
            _write_html_fn(
                out_dir / pr.url.strip("/") / "index.html",
                _render_fn(
                    env, "edition.html",
                    nav_projects=nav_projects, site_url=site_url,
                    canonical_url=(site_url + pr.url),
                    edition=index_edition,
                    project=pr,
                    breadcrumb=[
                        {"label": "Komiksy", "url": "/komiksy/"},
                    ],
                ),
            )
        else:
            # Multi-edition project page
            _write_html_fn(
                out_dir / pr.url.strip("/") / "index.html",
                _render_fn(
                    env, "project.html",
                    nav_projects=nav_projects, site_url=site_url,
                    canonical_url=(site_url + pr.url),
                    project=pr,
                    editions=pr_editions,
                    breadcrumb=[
                        {"label": "Komiksy", "url": "/komiksy/"},
                    ],
                ),
            )

        # Render individual edition pages (skip those with URL == project URL = already rendered)
        for e in pr_editions:
            if e.url == pr.url:
                continue  # already rendered as project page above
            _write_html_fn(
                out_dir / e.url.strip("/") / "index.html",
                _render_fn(
                    env, "edition.html",
                    nav_projects=nav_projects, site_url=site_url,
                    canonical_url=(site_url + e.url),
                    edition=e,
                    project=pr,
                    breadcrumb=[
                        {"label": "Komiksy", "url": "/komiksy/"},
                        {"label": pr.title, "url": pr.url},
                    ],
                ),
            )
