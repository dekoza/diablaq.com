from __future__ import annotations

import os
import shutil
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from diablaq_site.io import _write_html, _copy_tree
from diablaq_site.images import get_cover_aspect_class, generate_thumbnail, thumb_path_from_photo
from diablaq_site.models import BlogPost, Edition, Page, Person, Project
from diablaq_site.parsing import (
    build_nav_projects,
    build_people_index,
    build_tags_index,
    load_blog_posts,
    load_pages,
    load_people,
    load_projects_and_editions,
    read_markdown_file,
)
from diablaq_site.rendering import (
    render_home_page,
    render_listing_pages,
    render_content_pages,
    render_people_pages,
    render_blog_pages,
    render_project_pages,
    render_template,
)
from diablaq_site.urls import canonical_edition_url, canonical_project_url, slugify_tag


def _init_environment(root: Path, out_dir: Path) -> tuple[Environment, Path, Path, str]:
    templates_dir, content_dir = root / "templates", root / "content"
    if not templates_dir.exists():
        raise FileNotFoundError(f"Brak katalogu templates/: {templates_dir}")
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)), autoescape=select_autoescape(["html", "xml"])
    )
    return env, content_dir, out_dir, os.environ.get("DIABLAQ_SITE_URL", "").rstrip("/")


def _load_content(
    content_dir: Path, root: Path
) -> tuple[list[Project], list[Edition], list[Person], list[Page], list[BlogPost]]:
    pages = load_pages(content_dir / "pages")
    projects, editions = load_projects_and_editions(content_dir / "projects", root)
    people = load_people(content_dir / "people")
    blog_posts = load_blog_posts(content_dir / "blog") if (content_dir / "blog").exists() else []
    return projects, editions, people, pages, blog_posts


def _process_content(
    projects: list[Project],
    editions: list[Edition],
    people: list[Person],
    blog_posts: list[BlogPost],
    today: date | None = None,
) -> tuple[
    list[Edition], list[Edition], list[Edition], list[Person], list[Project], list[BlogPost]
]:
    today = today or date.today()
    new_editions = sorted(
        [e for e in editions if e.is_new], key=lambda e: e.release_date, reverse=True
    )
    announcements = sorted(
        [e for e in editions if e.is_announcement], key=lambda e: e.release_date, reverse=True
    )
    newest_anytime = sorted(
        [e for e in editions if e.release_date.year < 9999 and e.release_date <= today],
        key=lambda e: e.release_date,
        reverse=True,
    )[:8]
    return (
        new_editions,
        announcements,
        newest_anytime,
        build_people_index(people, editions),
        build_nav_projects(projects),
        sorted(blog_posts, key=lambda p: p.date, reverse=True),
    )


def _render_all(
    env: Environment,
    out_dir: Path,
    site_url: str,
    nav_projects: list[Project],
    projects: list[Project],
    editions: list[Edition],
    pages: list[Page],
    new_editions: list[Edition],
    announcements: list[Edition],
    newest_anytime: list[Edition],
    people_with_editions: list[Person],
    sorted_blog: list[BlogPost],
) -> None:
    _render = lambda env, template, **ctx: render_template(
        env,
        template,
        nav_projects=ctx.pop("nav_projects", nav_projects),
        site_url=ctx.pop("site_url", site_url),
        **ctx,
    )

    render_home_page(
        env,
        out_dir,
        site_url,
        nav_projects,
        projects,
        new_editions,
        announcements,
        newest_anytime,
        _render,
        _write_html,
    )
    render_listing_pages(
        env,
        out_dir,
        site_url,
        nav_projects,
        new_editions,
        announcements,
        newest_anytime,
        _render,
        _write_html,
    )
    render_content_pages(env, out_dir, site_url, nav_projects, pages, _render, _write_html)
    render_people_pages(
        env, out_dir, site_url, nav_projects, people_with_editions, _render, _write_html
    )
    render_blog_pages(
        env,
        out_dir,
        site_url,
        nav_projects,
        sorted_blog,
        _render,
        _write_html,
        build_tags_index,
        slugify_tag,
    )

    def _write_section(
        path_slug: str, *, title: str, line: str, description: str | None = None
    ) -> None:
        _write_html(
            out_dir / path_slug / "index.html",
            _render(
                env,
                "section.html",
                nav_projects=nav_projects,
                site_url=site_url,
                canonical_url=(site_url + f"/{path_slug}/"),
                title=title,
                description=description,
                projects=[p for p in projects if p.line == line],
            ),
        )

    render_project_pages(
        env,
        out_dir,
        site_url,
        nav_projects,
        projects,
        editions,
        _render,
        _write_html,
        _write_section,
    )


def _finalize(root: Path, out_dir: Path, people: list[Person]) -> None:
    _copy_tree(root / "img", out_dir / "img")
    _copy_tree(root / "css", out_dir / "css")
    for person in people:
        if person.photo:
            src_photo = root / person.photo.lstrip("/")
            if src_photo.exists():
                generate_thumbnail(
                    src_photo, out_dir / thumb_path_from_photo(person.photo).lstrip("/")
                )
    for file_name in ["CNAME", ".nojekyll"]:
        src = root / file_name
        if src.exists():
            shutil.copy2(src, out_dir / file_name)


def build_site(*, root: Path, out_dir: Path) -> None:
    env, content_dir, out_dir, site_url = _init_environment(root, out_dir)
    projects, editions, people, pages, blog_posts = _load_content(content_dir, root)
    new_editions, announcements, newest_anytime, people_with_editions, nav_projects, sorted_blog = (
        _process_content(projects, editions, people, blog_posts)
    )
    _render_all(
        env,
        out_dir,
        site_url,
        nav_projects,
        projects,
        editions,
        pages,
        new_editions,
        announcements,
        newest_anytime,
        people_with_editions,
        sorted_blog,
    )
    _finalize(root, out_dir, people_with_editions)
