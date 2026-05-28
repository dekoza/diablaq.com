"""Template rendering helpers — Jinja2 environment and context injection."""

from __future__ import annotations

from datetime import date
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


_LINE_META: dict[str, dict[str, str]] = {
    "diablaq": {
        "label": "Główna linia",
        "url_slug": "diablaq",
        "description": "Autorskie komiksy dla dorosłych.",
    },
    "dobre-licho": {
        "label": "Dobre Licho",
        "url_slug": "dobre-licho",
        "description": "Komiksy dla dzieci i młodzieży.",
    },
    "mecenat": {
        "label": "Mecenat",
        "url_slug": "mecenat",
        "description": "Publikacje rozwijane w formule mecenatu.",
    },
    "studio": {
        "label": "Studio",
        "url_slug": "studio",
        "description": "Produkcje komiksowe dla innych wydawców.",
    },
}

_CATALOG_PREVIEW_LIMIT = 4


def _group_editions_by_subseries(editions) -> list[tuple[str | None, list]]:
    """Group editions by subseries, preserving within-group order.

    The None-subseries group (main series) always comes first.
    Named subseries groups follow in alphabetical order.
    """
    if not editions:
        return []

    groups: dict[str | None, list] = {}
    for edition in editions:
        groups.setdefault(edition.subseries, []).append(edition)

    ordered: list[tuple[str | None, list]] = []
    if None in groups:
        ordered.append((None, groups[None]))
    for key in sorted(k for k in groups if k is not None):
        ordered.append((key, groups[key]))
    return ordered


_HOME_CATALOG_CAP = 8


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
    Sub-line pages (/komiksy/{slug}/): also limited to _CATALOG_PREVIEW_LIMIT newest
    projects, with a link back to the overview to see everything.
    """
    # Build a mapping: project_slug → latest edition release_date
    project_latest_date: dict[str, date] = {}
    for e in editions:
        slug = e.project_slug
        if slug not in project_latest_date or e.release_date > project_latest_date[slug]:
            project_latest_date[slug] = e.release_date

    def _project_sort_key(p: Project) -> date:
        return project_latest_date.get(p.slug, date.min)

    lines_order = ["diablaq", "dobre-licho", "mecenat", "studio"]
    display_projects = [p for p in projects if p.kind == "title"]

    # Build a full group list (known lines first, then any unlisted lines)
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

    # Overview: each group gets at most _CATALOG_PREVIEW_LIMIT projects
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

    # Sub-line pages: also limited to _CATALOG_PREVIEW_LIMIT newest projects
    for group in all_groups:
        url_slug = _LINE_META.get(group["id"], {"url_slug": group["id"]})["url_slug"]
        _write_html_fn(
            out_dir / "komiksy" / url_slug / "index.html",
            _render_fn(
                env,
                "catalog_line.html",
                nav_projects=nav_projects,
                site_url=site_url,
                canonical_url=(site_url + f"/komiksy/{url_slug}/"),
                group={**group, "projects": group["projects"][:_CATALOG_PREVIEW_LIMIT]},
                breadcrumb=[{"label": "Komiksy", "url": "/komiksy/"}],
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
    """Render universe pages, title pages, and all edition pages.

    One-shot comics (edition_slug='index') render at the project URL using edition.html.
    Multi-edition title projects render a project page + individual edition pages.
    Universe projects render a dedicated universe landing page with related titles.
    Legacy path redirects are no longer HTML pages — handled by _redirects file.
    """
    projects_by_slug = {project.slug: project for project in projects}
    titles_by_universe: dict[str, list] = {}
    for project in projects:
        if project.kind != "title" or not project.universe_slug:
            continue
        titles_by_universe.setdefault(project.universe_slug, []).append(project)
    for related_titles in titles_by_universe.values():
        related_titles.sort(key=lambda project: project.title.lower())

    for pr in projects:
        if pr.kind == "universe":
            _write_html_fn(
                out_dir / pr.url.strip("/") / "index.html",
                _render_fn(
                    env,
                    "universe.html",
                    nav_projects=nav_projects,
                    site_url=site_url,
                    canonical_url=(site_url + pr.url),
                    project=pr,
                    related_titles=titles_by_universe.get(pr.slug, []),
                    breadcrumb=[
                        {"label": "Komiksy", "url": "/komiksy/"},
                    ],
                ),
            )
            continue

        universe = projects_by_slug.get(pr.universe_slug) if pr.universe_slug else None
        breadcrumb = [{"label": "Komiksy", "url": "/komiksy/"}]
        if universe is not None:
            breadcrumb.append({"label": universe.title, "url": universe.url})

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
                    universe=universe,
                    breadcrumb=breadcrumb,
                ),
            )
        else:
            # Multi-edition project page
            edition_groups = _group_editions_by_subseries(pr_editions)
            _write_html_fn(
                out_dir / pr.url.strip("/") / "index.html",
                _render_fn(
                    env, "project.html",
                    nav_projects=nav_projects, site_url=site_url,
                    canonical_url=(site_url + pr.url),
                    project=pr,
                    universe=universe,
                    editions=pr_editions,
                    edition_groups=edition_groups,
                    breadcrumb=breadcrumb,
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
                    universe=universe,
                    breadcrumb=breadcrumb + [
                        {"label": pr.title, "url": pr.url},
                    ],
                ),
            )
