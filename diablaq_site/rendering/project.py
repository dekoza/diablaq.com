"""Project and edition page renderer."""

from __future__ import annotations

from pathlib import Path


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

        index_edition = next((e for e in pr_editions if e.url == pr.url), None)

        if index_edition:
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

        for e in pr_editions:
            if e.url == pr.url:
                continue
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
