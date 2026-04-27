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
    apply_person_credit_names,
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
    render_catalog_page,
    render_content_pages,
    render_people_pages,
    render_blog_pages,
    render_project_pages,
    render_template,
    format_date_pl,
    _build_home_per_line_sections,
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
    env.filters["format_date_pl"] = format_date_pl
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
        [e for e in editions if not e.is_announcement and e.release_date.year < 9999 and e.release_date <= today],
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

    # Hero carousel: all featured editions (sorted by featured_order), or
    # fallback to the single latest past release with a cover image.
    # Announcements never auto-promote — they have their own section.
    featured_slides = sorted(
        [e for e in editions if e.featured and e.cover_image],
        key=lambda e: e.featured_order,
    )
    if featured_slides:
        hero_slides = featured_slides
    else:
        past_with_cover = sorted(
            [e for e in editions
             if not e.is_announcement and e.release_date.year < 9999 and e.cover_image],
            key=lambda e: e.release_date,
            reverse=True,
        )
        hero_slides = past_with_cover[:1]

    hero_edition = hero_slides[0] if hero_slides else None

    per_line_sections = _build_home_per_line_sections(
        projects, editions, hero_slides, newest_anytime
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
        hero_slides,
        per_line_sections,
        _render,
        _write_html,
    )
    render_catalog_page(
        env,
        out_dir,
        site_url,
        nav_projects,
        projects,
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
    render_project_pages(
        env,
        out_dir,
        site_url,
        nav_projects,
        projects,
        editions,
        _render,
        _write_html,
    )


def _generate_redirects(out_dir: Path, projects: list[Project], editions: list[Edition]) -> None:
    """Generate _redirects file for legacy URLs (Netlify/Cloudflare Pages format)."""
    lines = [
        "# Legacy section redirects",
        "/publikacje/*  /komiksy/:splat  301",
        "/dobre-licho/*  /komiksy/:splat  301",
        "/mecenat/*  /komiksy/:splat  301",
        "/studio/*  /komiksy/:splat  301",
        "/nowe/  /  301",
        "/zapowiedzi/  /  301",
        "",
        "# Legacy project slug redirects",
    ]
    seen: set[str] = set()

    def _add(src: str, dst: str) -> None:
        entry = f"{src}*  {dst}:splat  301"
        if entry not in seen:
            seen.add(entry)
            lines.append(entry)

    for pr in projects:
        canonical = pr.url
        if pr.legacy_path and pr.legacy_path.rstrip("/") != canonical.rstrip("/"):
            _add(pr.legacy_path, canonical)
        slug_path = f"/{pr.slug}/"
        if slug_path.rstrip("/") != canonical.rstrip("/"):
            _add(slug_path, canonical)

    for edition in editions:
        if edition.legacy_path and edition.legacy_path.rstrip("/") != edition.url.rstrip("/"):
            _add(edition.legacy_path, edition.url)

    lines.append("/zvyrke/  /ludzie/zvyrke/  301")
    (out_dir / "_redirects").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _generate_sitemap(out_dir: Path, site_url: str, pages: list[str]) -> None:
    """Generate sitemap.xml with all canonical URLs."""
    entries = "\n".join(
        f"  <url><loc>{site_url}{p}</loc></url>"
        for p in pages
    )
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{entries}
</urlset>
"""
    (out_dir / "sitemap.xml").write_text(xml, encoding="utf-8")


def _finalize(
    root: Path,
    out_dir: Path,
    people: list[Person],
    projects: list[Project],
    editions: list[Edition],
    site_url: str,
    env: Environment,
) -> None:
    _copy_tree(root / "img", out_dir / "img")
    _copy_tree(root / "css", out_dir / "css")
    # Copy fonts if self-hosted
    fonts_dir = root / "fonts"
    if fonts_dir.exists():
        _copy_tree(fonts_dir, out_dir / "fonts")
    for person in people:
        if person.photo:
            src_photo = root / person.photo.lstrip("/")
            if src_photo.exists():
                generate_thumbnail(
                    src_photo, out_dir / thumb_path_from_photo(person.photo).lstrip("/")
                )
    for file_name in ["CNAME", ".nojekyll", "robots.txt"]:
        src = root / file_name
        if src.exists():
            shutil.copy2(src, out_dir / file_name)
    _generate_redirects(out_dir, projects, editions)
    # 404 page
    _write_html(
        out_dir / "404.html",
        render_template(env, "404.html", nav_projects=[], site_url=site_url, canonical_url=""),
    )


def build_site(*, root: Path, out_dir: Path) -> None:
    env, content_dir, out_dir, site_url = _init_environment(root, out_dir)
    projects, editions, people, pages, blog_posts = _load_content(content_dir, root)
    editions = apply_person_credit_names(editions, people)
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
    _finalize(root, out_dir, people_with_editions, projects, editions, site_url, env)
