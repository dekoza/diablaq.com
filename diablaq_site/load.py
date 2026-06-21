"""Content loading orchestration for diablaq.com.

Filesystem I/O, content assembly, and cross-entity linking.
Depends on fields.py for all field-level parsing.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from dataclasses import replace
from datetime import date
from pathlib import Path

from diablaq_site.fields import (
    _ALLOWED_PROJECT_KINDS,
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
from diablaq_site.images import get_cover_aspect_class, thumb_path_from_photo
from diablaq_site.models import BlogPost, Creator, Edition, EditionCover, Page, Person, Project
from diablaq_site.urls import canonical_edition_url, canonical_project_url


def load_pages(pages_dir: Path) -> list:
    """Load all pages from content/pages/."""
    pages: list[Page] = []
    for page_md in sorted(pages_dir.glob("*.md")):
        meta, body_html = read_markdown_file(page_md)
        slug = page_md.stem
        pages.append(Page(slug=slug, title=str(meta.get("title") or slug), html_body=body_html))
    return pages


def load_projects_and_editions(projects_dir: Path, root: Path) -> tuple[list, list]:
    """Load all projects and their editions, skipping those with draft: true."""
    projects: list[Project] = []
    editions: list[Edition] = []

    for project_dir in sorted(projects_dir.glob("*/")):
        project_md = project_dir / "project.md"
        if not project_md.exists():
            continue
        meta, body_html = read_markdown_file(project_md)

        if bool(meta.get("draft", False)):
            continue

        slug, line = project_dir.name, str(meta.get("line") or "diablaq")
        kind = str(meta.get("kind") or "title").strip() or "title"
        if kind not in _ALLOWED_PROJECT_KINDS:
            raise ValueError(
                f"Nieprawidłowe kind={kind!r} w {project_md}. Dozwolone: title, universe."
            )

        universe_slug = (
            str(meta["universe_slug"]).strip() if meta.get("universe_slug") is not None else None
        )
        if kind == "universe" and universe_slug:
            raise ValueError(f"Projekt ma universe_slug, ale kind=universe w {project_md}.")
        if universe_slug == slug:
            raise ValueError(f"Projekt nie może wskazywać samego siebie jako universe_slug: {project_md}")

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
                cover_image=cover_image,
                cover_aspect_class=get_cover_aspect_class(cover_image, root),
                html_body=body_html,
                draft=False,
                kind=kind,
                universe_slug=universe_slug,
            )
        )

        drafts: list[tuple[dict[str, object], str, date, str]] = []
        for edition_md in sorted((project_dir / "editions").glob("*.md")):
            emeta, ebody_html = read_markdown_file(edition_md)
            release_date = parse_optional_date(emeta.get("release_date"), source_path=edition_md)
            drafts.append((emeta, ebody_html, release_date or date(9999, 12, 31), edition_md.stem))

        grouped: dict[str | None, list[tuple[dict[str, object], str, date, str]]] = defaultdict(list)
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
            ensure_no_legacy_edition_fields(emeta, source_path=source)

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
                release_date=release_date,
                today=date.today(),
            )
            cover_image, _cover_alt = pick_cover(emeta)
            primary_cover = parse_primary_cover(emeta, source_path=source)
            alternate_covers = parse_cover_list(emeta, "alternate_covers", source_path=source)
            creators, creator_names = parse_creators(emeta, source_path=source)
            standalone = bool(emeta.get("standalone", False))
            issue_number = None if standalone else issue_numbers.get(ed_slug)
            presale_url = (
                str(emeta["presale_url"]) if emeta.get("presale_url") is not None else None
            )
            legacy_anchor = (
                str(emeta["legacy_anchor"]) if emeta.get("legacy_anchor") is not None else None
            )
            edition_legacy_path = (
                str(emeta["legacy_path"]) if emeta.get("legacy_path") is not None else None
            )
            featured = bool(emeta.get("featured", False))
            featured_img = str(emeta["featured_img"]).strip() if emeta.get("featured_img") else None
            featured_img_alt = (
                str(emeta["featured_img_alt"]).strip() if emeta.get("featured_img_alt") else None
            )
            featured_order = int(emeta.get("featured_order") or 0)
            featured_duration = max(6, min(20, int(emeta.get("featured_duration") or 10)))
            edition_summary = (
                str(emeta["summary"]).strip() if emeta.get("summary") else None
            )
            products = parse_products(
                emeta,
                source_path=source,
                primary_cover=primary_cover,
                alternate_covers=alternate_covers,
            )

            edition = Edition(
                url=canonical_edition_url(line=line, project_slug=slug, edition_slug=ed_slug),
                title=str(emeta.get("title") or ed_slug),
                project_slug=slug,
                release=str(emeta.get("release") or "") or None,
                release_date=sort_date,
                is_new=force_new or (auto_is_new and not force_announcement),
                is_announcement=force_announcement or (auto_is_announcement and not force_new),
                presale_url=presale_url,
                legacy_anchor=legacy_anchor,
                primary_cover=primary_cover,
                cover_aspect_class=get_cover_aspect_class(cover_image, root),
                alternate_covers=alternate_covers,
                previews=parse_image_list(emeta, "previews", source_path=source),
                creators=creators,
                creator_names=creator_names,
                edition_specs=parse_specs(emeta, key="edition_specs"),
                products=products,
                html_body=ebody_html,
                standalone=standalone,
                subseries=str(emeta.get("subseries") or "").strip() or None,
                issue_number=issue_number,
                issue_number_display=f"{issue_number:02d}" if issue_number is not None else None,
                featured=featured,
                legacy_path=edition_legacy_path,
                featured_img=featured_img,
                featured_img_alt=featured_img_alt,
                featured_order=featured_order,
                featured_duration=featured_duration,
                summary=edition_summary,
            )

            if (
                not edition.is_announcement
                and edition.release_date.year < 9999
                and not any(product.buy_links for product in edition.products)
            ):
                print(f"WARNING: {source} has no buy_links", file=sys.stderr)

            editions.append(edition)

    projects_with_fallbacks: list[Project] = []
    for project in projects:
        cover_image = project.cover_image
        if not cover_image:
            fallback_cover = next(
                (
                    edition.hero.cover_image
                    for edition in sorted(
                        [item for item in editions if item.project_slug == project.slug and item.hero.cover_image],
                        key=lambda item: (item.release_date, item.url),
                    )
                ),
                None,
            )
            cover_image = fallback_cover

        if not cover_image:
            project_md = projects_dir / project.slug / "project.md"
            print(f"WARNING: {project_md} has no cover_image", file=sys.stderr)
        elif not (root / cover_image.lstrip("/")).exists():
            project_md = projects_dir / project.slug / "project.md"
            print(f"WARNING: {project_md} cover_image not found: {cover_image}", file=sys.stderr)

        if not project.summary:
            project_md = projects_dir / project.slug / "project.md"
            print(f"WARNING: {project_md} has no summary", file=sys.stderr)

        projects_with_fallbacks.append(
            replace(
                project,
                cover_image=cover_image,
                cover_aspect_class=get_cover_aspect_class(cover_image, root),
            )
        )

    projects = projects_with_fallbacks
    projects_by_slug = {project.slug: project for project in projects}
    for project in projects:
        if not project.universe_slug:
            continue
        universe = projects_by_slug.get(project.universe_slug)
        if universe is None:
            raise ValueError(
                f"Projekt {project.slug} wskazuje nieistniejące universe_slug={project.universe_slug!r}."
            )
        if universe.kind != "universe":
            raise ValueError(
                f"Projekt {project.slug} wskazuje universe_slug={project.universe_slug!r}, ale ten projekt nie ma kind=universe."
            )

    return projects, editions


def load_people(people_dir: Path) -> list:
    """Load all people from content/people/."""
    root = people_dir.parent.parent
    people: list[Person] = []
    for person_md in sorted(people_dir.glob("*.md")):
        meta, body_html = read_markdown_file(person_md)
        slug = person_md.stem
        name = str(meta.get("name") or "").strip() or None
        credit_name = str(meta.get("credit_name") or "").strip() or None
        if not name and not credit_name:
            raise ValueError(f"Person must define name or credit_name in {person_md}")
        photo = str(meta.get("photo") or "").strip() or None
        if photo:
            photo_path = root / photo.lstrip("/")
            if not photo_path.exists():
                print(
                    f"WARNING: Person photo not found: {photo_path}",
                    file=sys.stderr,
                )
                photo = None
        people.append(
            Person(
                slug=slug,
                name=name,
                photo=photo,
                photo_thumb=thumb_path_from_photo(photo) if photo else None,
                html_bio=body_html,
                related_editions=[],
                credit_name=credit_name,
            )
        )
    return people


def load_blog_posts(blog_dir: Path) -> list:
    """Load all blog posts from content/blog/."""
    blog_posts: list[BlogPost] = []
    for post_md in sorted(blog_dir.glob("*.md")):
        meta, body_html = read_markdown_file(post_md)
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
    return blog_posts


def build_people_index(people: list[Person], editions: list[Edition]) -> list[Person]:
    """Link people to their related editions."""
    out: list[Person] = []
    for person in people:
        related = [
            edition
            for edition in editions
            if any(
                (contributor.person_slug and contributor.person_slug == person.slug)
                or (
                    not contributor.person_slug
                    and contributor.name.strip().lower() in person.match_names
                )
                for contributor in edition.all_contributors
            )
        ]
        out.append(
            Person(
                slug=person.slug,
                name=person.name,
                photo=person.photo,
                photo_thumb=person.photo_thumb,
                html_bio=person.html_bio,
                related_editions=sorted(related, key=lambda edition: edition.release_date, reverse=True),
                credit_name=person.credit_name,
            )
        )
    return out


def build_tags_index(posts: list[BlogPost]) -> dict[str, list[BlogPost]]:
    """Build index of blog posts by tag."""
    tag_map: dict[str, list[BlogPost]] = {}
    for post in posts:
        for tag in post.tags:
            clean = tag.strip()
            if clean:
                tag_map.setdefault(clean, []).append(post)
    return tag_map


def apply_person_credit_names(editions: list[Edition], people: list[Person]) -> list[Edition]:
    """Replace linked contributor names with the person's publication credit."""
    people_by_slug = {person.slug: person for person in people}
    resolved_editions: list[Edition] = []

    for edition in editions:
        resolved_creators: list[Creator] = []
        for creator in edition.creators:
            if creator.person_slug:
                person = people_by_slug.get(creator.person_slug)
                if person is not None:
                    resolved_creators.append(
                        Creator(
                            role=creator.role,
                            name=person.publication_name,
                            person_slug=creator.person_slug,
                        )
                    )
                    continue
            resolved_creators.append(creator)

        def _resolve_cover(cover: EditionCover | None) -> EditionCover | None:
            if cover is None or not cover.person_slug:
                return cover
            person = people_by_slug.get(cover.person_slug)
            if person is None:
                return cover
            return replace(cover, artist_name=person.publication_name)

        resolved_alternate_covers = [
            resolved_cover
            for resolved_cover in (_resolve_cover(cover) for cover in edition.alternate_covers)
            if resolved_cover is not None
        ]

        resolved_editions.append(
            replace(
                edition,
                primary_cover=_resolve_cover(edition.primary_cover),
                alternate_covers=resolved_alternate_covers,
                creators=resolved_creators,
                creator_names=[creator.name for creator in resolved_creators],
            )
        )

    return resolved_editions


def build_nav_projects(projects: list[Project]) -> list[Project]:
    """Sort projects by title for navigation menu."""
    return sorted(projects, key=lambda p: p.title.lower())
