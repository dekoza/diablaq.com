from __future__ import annotations

import os
import shutil
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Callable, cast

from jinja2 import Environment, FileSystemLoader, select_autoescape

import diablaq_site.io as site_io
from diablaq_site.images import get_cover_aspect_class, generate_thumbnail, thumb_path_from_photo
from diablaq_site.models import BlogPost, Edition, Page, Person, Project
from diablaq_site.parsing import (
    coerce_str_list,
    derive_flags,
    parse_buy_links,
    parse_creators,
    parse_date,
    parse_image_list,
    parse_optional_date,
    parse_specs,
    parse_variants,
    pick_cover,
    read_markdown_file,
)
from diablaq_site.rendering import render_template
from diablaq_site.urls import canonical_edition_url, canonical_project_url, slugify_tag

_write_html: Callable[[Path, str], None] = cast(
    Callable[[Path, str], None], getattr(site_io, "_write_html")
)
_copy_tree: Callable[[Path, Path], None] = cast(
    Callable[[Path, Path], None], getattr(site_io, "_copy_tree")
)


def _read_markdown_file(path: Path) -> tuple[dict[str, object], str]:
    meta, body = read_markdown_file(path)
    return cast(dict[str, object], meta), body


def _render(
    env: Environment,
    template_name: str,
    *,
    nav_projects: list[Project],
    site_url: str,
    **ctx: object,
) -> str:
    return render_template(env, template_name, nav_projects=nav_projects, site_url=site_url, **ctx)


def _build_nav_projects(projects: list[Project]) -> list[Project]:
    return sorted(projects, key=lambda p: p.title.lower())


def _build_tags_index(posts: list[BlogPost]) -> dict[str, list[BlogPost]]:
    tag_map: dict[str, list[BlogPost]] = {}
    for post in posts:
        for tag in post.tags:
            clean = tag.strip()
            if clean:
                tag_map.setdefault(clean, []).append(post)
    return tag_map


def _build_people_index(people: list[Person], editions: list[Edition]) -> list[Person]:
    out: list[Person] = []
    for person in people:
        related = [
            e
            for e in editions
            if any(
                (c.person_slug and c.person_slug == person.slug)
                or (not c.person_slug and c.name.strip().lower() == person.name.strip().lower())
                for c in e.creators
            )
        ]
        out.append(
            Person(
                slug=person.slug,
                name=person.name,
                photo=person.photo,
                photo_thumb=person.photo_thumb,
                html_bio=person.html_bio,
                related_editions=sorted(related, key=lambda e: e.release_date, reverse=True),
            )
        )
    return out


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
    projects: list[Project] = []
    editions: list[Edition] = []
    people: list[Person] = []
    pages: list[Page] = []
    blog_posts: list[BlogPost] = []

    for page_md in sorted((content_dir / "pages").glob("*.md")):
        meta, body_html = _read_markdown_file(page_md)
        slug = page_md.stem
        pages.append(Page(slug=slug, title=str(meta.get("title") or slug), html_body=body_html))

    for project_dir in sorted((content_dir / "projects").glob("*/")):
        project_md = project_dir / "project.md"
        if not project_md.exists():
            continue
        meta, body_html = _read_markdown_file(project_md)
        slug, line = project_dir.name, str(meta.get("line") or "diablaq")
        cover_image = str(meta.get("cover_image") or "").strip() or None
        summary = str(meta["summary"]) if meta.get("summary") is not None else None
        legacy_path = str(meta["legacy_path"]) if meta.get("legacy_path") is not None else None
        projects.append(
            Project(
                slug=slug,
                title=str(meta.get("title") or slug),
                line=line,
                summary=summary,
                legacy_path=legacy_path,
                url=canonical_project_url(line=line, slug=slug),
                legacy_landing=bool(meta.get("legacy_landing", False)),
                cover_image=cover_image,
                cover_aspect_class=get_cover_aspect_class(cover_image, root),
                html_body=body_html,
            )
        )

        drafts: list[tuple[dict[str, object], str, date, str]] = []
        for edition_md in sorted((project_dir / "editions").glob("*.md")):
            emeta, ebody_html = _read_markdown_file(edition_md)
            release_date = parse_optional_date(emeta.get("release_date"), source_path=edition_md)
            drafts.append((emeta, ebody_html, release_date or date(9999, 12, 31), edition_md.stem))

        grouped: dict[str | None, list[tuple[dict[str, object], str, date, str]]] = defaultdict(
            list
        )
        for emeta, ebody_html, sort_date, ed_slug in drafts:
            if not emeta.get("standalone", False):
                subseries = str(emeta["subseries"]).strip() if emeta.get("subseries") else None
                grouped[subseries].append((emeta, ebody_html, sort_date, ed_slug))

        issue_numbers: dict[str, int] = {}
        for items in grouped.values():
            for idx, (emeta, _, _, ed_slug) in enumerate(
                sorted(items, key=lambda item: item[2]), start=1
            ):
                issue_numbers[ed_slug] = (
                    int(str(emeta["issue_number"]))
                    if emeta.get("issue_number") is not None
                    else idx
                )

        for emeta, ebody_html, sort_date, ed_slug in drafts:
            source = project_dir / "editions" / f"{ed_slug}.md"
            release_date = parse_optional_date(emeta.get("release_date"), source_path=source)
            force_new = bool(emeta.get("force_new", False) or emeta.get("is_new", False))
            force_announcement = bool(
                emeta.get("force_announcement", False) or emeta.get("is_announcement", False)
            )
            if force_new and force_announcement:
                raise ValueError(
                    f"Pozycja nie może mieć jednocześnie force_new i force_announcement: {source}"
                )
            auto_is_new, auto_is_announcement = derive_flags(
                release_date=release_date, today=date.today()
            )
            cover_image, cover_alt = pick_cover(emeta)
            creators, creator_names = parse_creators(emeta, source_path=source)
            standalone = bool(emeta.get("standalone", False))
            issue_number = None if standalone else issue_numbers.get(ed_slug)
            presale_url = (
                str(emeta["presale_url"]) if emeta.get("presale_url") is not None else None
            )
            legacy_anchor = (
                str(emeta["legacy_anchor"]) if emeta.get("legacy_anchor") is not None else None
            )
            editions.append(
                Edition(
                    url=canonical_edition_url(line=line, project_slug=slug, edition_slug=ed_slug),
                    title=str(emeta.get("title") or ed_slug),
                    project_slug=slug,
                    release=str(emeta.get("release") or "") or None,
                    release_date=sort_date,
                    is_new=force_new or (auto_is_new and not force_announcement),
                    is_announcement=force_announcement or (auto_is_announcement and not force_new),
                    presale_url=presale_url,
                    legacy_anchor=legacy_anchor,
                    cover_image=cover_image,
                    cover_alt=cover_alt,
                    cover_aspect_class=get_cover_aspect_class(cover_image, root),
                    covers=parse_image_list(emeta, "covers", source_path=source),
                    previews=parse_image_list(emeta, "previews", source_path=source),
                    creators=creators,
                    creator_names=creator_names,
                    specs=parse_specs(emeta),
                    buy_links=parse_buy_links(emeta, source_path=source),
                    variants=parse_variants(emeta, source_path=source),
                    html_body=ebody_html,
                    standalone=standalone,
                    subseries=str(emeta.get("subseries") or "").strip() or None,
                    issue_number=issue_number,
                    issue_number_display=f"{issue_number:02d}"
                    if issue_number is not None
                    else None,
                )
            )

    for person_md in sorted((content_dir / "people").glob("*.md")):
        meta, body_html = _read_markdown_file(person_md)
        slug = person_md.stem
        photo = str(meta.get("photo") or "").strip() or None
        people.append(
            Person(
                slug=slug,
                name=str(meta.get("name") or slug),
                photo=photo,
                photo_thumb=thumb_path_from_photo(photo) if photo else None,
                html_bio=body_html,
                related_editions=[],
            )
        )

    blog_root = content_dir / "blog"
    if blog_root.exists():
        for post_md in sorted(blog_root.glob("*.md")):
            meta, body_html = _read_markdown_file(post_md)
            if bool(meta.get("draft", False)):
                continue
            if "date" not in meta:
                raise ValueError(f"Brak date w {post_md}")
            raw_slug = str(meta.get("slug") or post_md.stem)
            parts = raw_slug.split("-", 3)
            slug = parts[3] if len(parts) >= 4 and all(p.isdigit() for p in parts[:3]) else raw_slug
            blog_posts.append(
                BlogPost(
                    url=f"/blog/{slug}/",
                    slug=slug,
                    title=str(meta.get("title") or post_md.stem),
                    date=parse_date(str(meta["date"]), source_path=post_md),
                    summary=str(meta.get("summary") or "").strip() or None,
                    cover_image=str(meta.get("cover_image") or "").strip() or None,
                    cover_alt=str(meta.get("cover_alt") or "").strip() or None,
                    tags=coerce_str_list(meta.get("tags")),
                    html_body=body_html,
                )
            )

    return projects, editions, people, pages, blog_posts


def _process_content(
    projects: list[Project],
    editions: list[Edition],
    people: list[Person],
    blog_posts: list[BlogPost],
) -> tuple[
    list[Edition], list[Edition], list[Edition], list[Person], list[Project], list[BlogPost]
]:
    new_editions = sorted(
        [e for e in editions if e.is_new], key=lambda e: e.release_date, reverse=True
    )
    announcements = sorted(
        [e for e in editions if e.is_announcement], key=lambda e: e.release_date, reverse=True
    )
    newest_anytime = sorted(
        [e for e in editions if e.release_date.year < 9999],
        key=lambda e: e.release_date,
        reverse=True,
    )[:4]
    return (
        new_editions,
        announcements,
        newest_anytime,
        _build_people_index(people, editions),
        _build_nav_projects(projects),
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
    _write_html(
        out_dir / "index.html",
        _render(
            env,
            "home.html",
            nav_projects=nav_projects,
            site_url=site_url,
            canonical_url=(site_url + "/"),
            projects=projects,
            new_editions=new_editions[:12],
            announcements=announcements[:12],
        ),
    )
    _write_html(
        out_dir / "nowe" / "index.html",
        _render(
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
    _write_html(
        out_dir / "zapowiedzi" / "index.html",
        _render(
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
    for page in pages:
        _write_html(
            out_dir / page.slug / "index.html",
            _render(
                env,
                "page.html",
                nav_projects=nav_projects,
                site_url=site_url,
                canonical_url=(site_url + f"/{page.slug}/"),
                page=page,
            ),
        )
    _write_html(
        out_dir / "ludzie" / "index.html",
        _render(
            env,
            "people_index.html",
            nav_projects=nav_projects,
            site_url=site_url,
            canonical_url=(site_url + "/ludzie/"),
            people=people_with_editions,
        ),
    )
    for p in people_with_editions:
        _write_html(
            out_dir / "ludzie" / p.slug / "index.html",
            _render(
                env,
                "person.html",
                nav_projects=nav_projects,
                site_url=site_url,
                canonical_url=(site_url + f"/ludzie/{p.slug}/"),
                person=p,
            ),
        )
    _write_html(
        out_dir / "blog" / "index.html",
        _render(
            env,
            "blog_index.html",
            nav_projects=nav_projects,
            site_url=site_url,
            canonical_url=(site_url + "/blog/"),
            posts=sorted_blog,
        ),
    )
    for post in sorted_blog:
        _write_html(
            out_dir / post.url.strip("/") / "index.html",
            _render(
                env,
                "blog_post.html",
                nav_projects=nav_projects,
                site_url=site_url,
                canonical_url=(site_url + post.url),
                post=post,
                post_tags=[{"name": t, "url": f"/blog/tag/{slugify_tag(t)}/"} for t in post.tags],
            ),
        )
    for tag, items in sorted(_build_tags_index(sorted_blog).items(), key=lambda kv: kv[0].lower()):
        tag_slug = slugify_tag(tag)
        _write_html(
            out_dir / "blog" / "tag" / tag_slug / "index.html",
            _render(
                env,
                "blog_index.html",
                nav_projects=nav_projects,
                site_url=site_url,
                canonical_url=(site_url + f"/blog/tag/{tag_slug}/"),
                posts=sorted(items, key=lambda p: p.date, reverse=True),
            ),
        )
    for pr in projects:
        pr_editions = sorted(
            [e for e in editions if e.project_slug == pr.slug],
            key=lambda e: e.release_date,
            reverse=True,
        )
        project_html = _render(
            env,
            "project.html",
            nav_projects=nav_projects,
            site_url=site_url,
            canonical_url=(site_url + pr.url),
            project=pr,
            editions=pr_editions,
        )
        _write_html(out_dir / pr.url.strip("/") / "index.html", project_html)
        if (
            pr.legacy_landing
            and pr.legacy_path
            and pr.legacy_path.rstrip("/") != pr.url.rstrip("/")
        ):
            _write_html(out_dir / pr.legacy_path.strip("/") / "index.html", project_html)
        legacy_slug_path = f"/{pr.slug}/"
        if legacy_slug_path.rstrip("/") != pr.url.rstrip("/") and not (
            pr.legacy_landing and legacy_slug_path.rstrip("/") == (pr.legacy_path or "").rstrip("/")
        ):
            _write_html(
                out_dir / pr.slug / "index.html",
                _render(
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
            _write_html(
                out_dir / pr.legacy_path.strip("/") / "index.html",
                _render(
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
                _write_html(
                    out_dir / e.url.strip("/") / "index.html",
                    _render(
                        env,
                        "edition.html",
                        nav_projects=nav_projects,
                        site_url=site_url,
                        canonical_url=(site_url + e.url),
                        edition=e,
                        project=pr,
                    ),
                )
    zv = next((p for p in people_with_editions if p.slug == "zvyrke"), None)
    if zv is not None:
        _write_html(
            out_dir / "zvyrke" / "index.html",
            _render(
                env,
                "redirect.html",
                nav_projects=nav_projects,
                site_url=site_url,
                canonical_url=(site_url + f"/ludzie/{zv.slug}/"),
                to_url=f"/ludzie/{zv.slug}/",
            ),
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

    _write_section(
        "publikacje",
        title="Publikacje",
        line="diablaq",
        description="Główna linia wydawnicza Diablaq.",
    )
    _write_section(
        "dobre-licho", title="Dobre Licho", line="dobre-licho", description="Imprint dla dzieci."
    )
    _write_section(
        "mecenat",
        title="Mecenat",
        line="mecenat",
        description="Publikacje rozwijane w formule mecenatu.",
    )
    if any(p.line == "studio" for p in projects):
        _write_section(
            "studio",
            title="Studio",
            line="studio",
            description="Produkcje komiksowe dla innych wydawnictw/klientów.",
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
