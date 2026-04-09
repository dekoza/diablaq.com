"""Parsing functions for diablaq.com content — frontmatter, dates, metadata validation."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import frontmatter
from markdown import markdown

from diablaq_site.models import (
    BlogPost,
    BuyLink,
    Creator,
    Edition,
    EditionVariant,
    ImageRef,
    Person,
    Project,
)
from diablaq_site.text import _fix_orphans
from diablaq_site.validation import (
    _ALLOWED_VARIANT_KINDS,
    _is_valid_isbn13,
)


def read_markdown_file(path: Path) -> tuple[dict, str]:
    """Read and parse a Markdown file with YAML frontmatter.

    Returns:
        (metadata_dict, html_body_string) tuple
    """
    try:
        post = frontmatter.load(str(path))
    except Exception as exc:  # noqa: BLE001 - preserve parser detail for authors
        raise ValueError(f"Nie udało się wczytać frontmatter w {path}: {exc}") from exc
    meta = dict(post.metadata or {})
    body_md = post.content or ""
    body_html = markdown(body_md, extensions=["extra", "sane_lists"])
    # Napraw zawieszki typograficzne (spójniki na końcu linii)
    body_html = _fix_orphans(body_html)
    return meta, body_html


def parse_date(value: str, *, source_path: Path) -> date:
    """Parse YYYY-MM-DD date string with keyword-only source_path for error messages."""
    try:
        yyyy, mm, dd = value.split("-")
        return date(int(yyyy), int(mm), int(dd))
    except Exception as exc:  # noqa: BLE001 - want a clear error
        raise ValueError(
            f"Nieprawidłowe release_date={value!r} w {source_path}. Oczekiwany format YYYY-MM-DD."
        ) from exc


def parse_optional_date(value: object, *, source_path: Path) -> date | None:
    """Parse optional date field — returns None for None or empty string."""
    if value is None:
        return None
    if value == "":
        return None
    return parse_date(str(value), source_path=source_path)


def derive_flags(*, release_date: date | None, today: date) -> tuple[bool, bool]:
    """Wylicza (is_new, is_announcement) bez ręcznych flag.

    Zasady:
    1) brak daty -> ani nowość, ani zapowiedź
    2) przyszła data -> zapowiedź
    3) data dziś lub przeszła -> nowość przez 6 tygodni od premiery
    """

    if release_date is None:
        return False, False

    if release_date > today:
        return False, True

    # release_date <= today
    if today <= (release_date + timedelta(weeks=6)):
        return True, False

    return False, False


def coerce_str_list(value) -> list[str]:
    """Convert value to list of stripped non-empty strings."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return [str(value).strip()] if str(value).strip() else []


def pick_cover(meta: dict) -> tuple[str | None, str | None]:
    """Wybiera okładkę do skrótu (listing/home).

    Obsługiwane formaty:
    - `cover_image` / `cover_alt`
    - `covers: [{image, alt, caption}, ...]`
    """

    cover_image = meta.get("cover_image")
    cover_alt = meta.get("cover_alt")
    if cover_image:
        return str(cover_image), str(cover_alt) if cover_alt else None

    covers = meta.get("covers")
    if isinstance(covers, list) and covers:
        first = covers[0]
        if isinstance(first, dict) and first.get("image"):
            return str(first.get("image")), str(first.get("alt") or "") or None

    return None, None


def parse_image_list(meta: dict, key: str, *, source_path: Path) -> list[ImageRef]:
    """Parse list of image references from metadata with keyword-only source_path."""
    raw = meta.get(key)
    if raw is None:
        return []

    if not isinstance(raw, list):
        raise ValueError(f"{key} musi być listą w {source_path}")

    out: list[ImageRef] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"{key}[{i}] musi być dict w {source_path}")
        image = str(item.get("image") or "").strip()
        if not image:
            raise ValueError(f"{key}[{i}] musi mieć image w {source_path}")
        alt = str(item.get("alt") or "").strip() or None
        caption = str(item.get("caption") or "").strip() or None
        out.append(ImageRef(image=image, alt=alt, caption=caption))

    return out


def as_str(value) -> str:
    """Convert any value to stripped string."""
    return str(value).strip()


def parse_buy_links(meta: dict, *, source_path: Path) -> list[BuyLink]:
    """Parse list of buy links from metadata with keyword-only source_path."""
    raw = meta.get("buy_links")
    if raw is None:
        return []

    if not isinstance(raw, list):
        raise ValueError(f"buy_links musi być listą w {source_path}")

    links: list[BuyLink] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"buy_links[{i}] musi być dict w {source_path}")

        label = as_str(item.get("label") or "")
        url = as_str(item.get("url") or "")
        if not label or not url:
            raise ValueError(f"buy_links[{i}] musi mieć label i url w {source_path}")
        links.append(BuyLink(label=label, url=url))

    return links


def _normalize_isbn13(value: str) -> str:
    """Normalize ISBN-13 by removing hyphens and spaces."""
    # Akceptujemy zapis z myślnikami/spacjami, ale przechodzimy na ciąg cyfr.
    return "".join(ch for ch in value if ch.isdigit())


# These constants must be available locally for parse_variants
_ALLOWED_BINDINGS = {"miekka", "twarda"}
_ALLOWED_VERSIONS = {"elektroniczna"}


def parse_variants(meta: dict, *, source_path: Path) -> list[EditionVariant]:
    """Parse edition variants from metadata with keyword-only source_path.

    CRITICAL: Calls parse_buy_links with synthetic dict wrapper exactly as-is.
    """
    raw = meta.get("variants")
    if raw is None:
        return []

    if not isinstance(raw, list):
        raise ValueError(f"variants musi być listą w {source_path}")

    # Fallback migracyjny: jeśli ktoś jeszcze trzyma specs na poziomie wydania,
    # a ma już variants, to dopniemy je do wariantów, o ile wariant nie ma własnych specs.
    edition_specs_fallback = parse_specs(meta)

    out: list[EditionVariant] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"variants[{i}] musi być dict w {source_path}")

        # Nowy format: binding/version; fallback: legacy kind
        binding = as_str(item.get("binding") or "") or None
        version = as_str(item.get("version") or "") or None

        legacy_kind = as_str(item.get("kind") or "") or None
        if legacy_kind and (binding or version):
            raise ValueError(
                f"variants[{i}] nie może mieć jednocześnie (binding/version) i kind w {source_path}"
            )

        if legacy_kind:
            if legacy_kind not in _ALLOWED_VARIANT_KINDS:
                raise ValueError(
                    f"variants[{i}].kind musi być jednym z {_ALLOWED_VARIANT_KINDS} w {source_path}"
                )
            if legacy_kind in _ALLOWED_BINDINGS:
                binding = legacy_kind
                version = None
            else:
                binding = None
                version = legacy_kind

        # Walidacja osi: dokładnie jedno z (binding, version)
        if not binding and not version:
            raise ValueError(
                f"variants[{i}] musi mieć binding albo version (lub legacy kind) w {source_path}"
            )
        if binding and version:
            raise ValueError(
                f"variants[{i}] nie może mieć jednocześnie binding i version w {source_path}"
            )
        if binding and binding not in _ALLOWED_BINDINGS:
            raise ValueError(
                f"variants[{i}].binding musi być jednym z {_ALLOWED_BINDINGS} w {source_path}"
            )
        if version and version not in _ALLOWED_VERSIONS:
            raise ValueError(
                f"variants[{i}].version musi być jednym z {_ALLOWED_VERSIONS} w {source_path}"
            )

        isbn13 = _normalize_isbn13(as_str(item.get("isbn13") or ""))
        if not isbn13:
            raise ValueError(f"variants[{i}].isbn13 jest wymagane w {source_path}")
        if not _is_valid_isbn13(isbn13):
            raise ValueError(
                f"variants[{i}].isbn13={item.get('isbn13')!r} nie wygląda jak poprawny ISBN-13 w {source_path}"
            )

        limited_print_run_raw = item.get("limited_print_run")
        limited_print_run: int | None
        if limited_print_run_raw is None or limited_print_run_raw == "":
            limited_print_run = None
        else:
            try:
                limited_print_run = int(limited_print_run_raw)
            except Exception as exc:  # noqa: BLE001
                raise ValueError(
                    f"variants[{i}].limited_print_run musi być liczbą całkowitą w {source_path}"
                ) from exc
            if limited_print_run <= 0:
                raise ValueError(f"variants[{i}].limited_print_run musi być > 0 w {source_path}")

        numbered_raw = item.get("numbered")
        numbered = bool(numbered_raw) if numbered_raw is not None else False
        if numbered and limited_print_run is None:
            raise ValueError(
                f"variants[{i}].numbered=true wymaga podania limited_print_run w {source_path}"
            )

        # CRITICAL: Preserve synthetic dict wrapper exactly as-is (per plan line 768)
        buy_links = parse_buy_links({"buy_links": item.get("buy_links")}, source_path=source_path)
        # if not buy_links:
        #     raise ValueError(
        #         f"variants[{i}].buy_links jest wymagane (lista linków zakupowych per wariant) w {source_path}"
        #     )

        specs = parse_specs(item)
        if not specs and edition_specs_fallback:
            specs = dict(edition_specs_fallback)

        out.append(
            EditionVariant(
                binding=binding,
                version=version,
                isbn13=isbn13,
                limited_print_run=limited_print_run,
                numbered=numbered,
                buy_links=buy_links,
                specs=specs,
            )
        )

    return out


def parse_creators(meta: dict, *, source_path: Path) -> tuple[list[Creator], list[str]]:
    """Obsługuje:

    - `creators: ["A", "B"]` (wstecznie)
    - `creators: [{role, name, person_slug}, ...]` (docelowo)

    Zwraca: (lista obiektów Creator, lista nazw do skrótów)
    """

    raw = meta.get("creators")
    if raw is None:
        return [], []

    if isinstance(raw, list) and all(not isinstance(x, dict) for x in raw):
        names = [str(x).strip() for x in raw if str(x).strip()]
        creators = [Creator(role=None, name=n, person_slug=None) for n in names]
        return creators, names

    if not isinstance(raw, list):
        raise ValueError(f"creators musi być listą w {source_path}")

    creators: list[Creator] = []
    names: list[str] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"creators[{i}] musi być obiektem (dict) w {source_path}")

        name = str(item.get("name") or "").strip()
        role = str(item.get("role") or "").strip() or None
        person_slug = str(item.get("person_slug") or "").strip() or None

        if not name:
            raise ValueError(f"creators[{i}] musi mieć name w {source_path}")

        creators.append(Creator(role=role, name=name, person_slug=person_slug))
        names.append(name)

    return creators, list(set(names))


def parse_specs(meta: dict) -> dict[str, str]:
    """Parse specs dictionary from metadata — NO source_path parameter."""
    raw = meta.get("specs")
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        return {}

    out: dict[str, str] = {}
    for k, v in raw.items():
        if v is None:
            continue
        key = as_str(k)
        val = as_str(v)
        if key and val:
            out[key] = val
    return out


def load_pages(pages_dir: Path) -> list:
    """Load all pages from content/pages/."""
    from diablaq_site.models import Page

    pages: list[Page] = []
    for page_md in sorted(pages_dir.glob("*.md")):
        meta, body_html = read_markdown_file(page_md)
        slug = page_md.stem
        pages.append(Page(slug=slug, title=str(meta.get("title") or slug), html_body=body_html))
    return pages


def load_projects_and_editions(projects_dir: Path, root: Path) -> tuple[list, list]:
    """Load all projects and their editions."""
    from collections import defaultdict
    from diablaq_site.models import Edition, Project
    from diablaq_site.images import get_cover_aspect_class
    from diablaq_site.urls import canonical_edition_url, canonical_project_url

    projects: list[Project] = []
    editions: list[Edition] = []

    for project_dir in sorted(projects_dir.glob("*/")):
        project_md = project_dir / "project.md"
        if not project_md.exists():
            continue
        meta, body_html = read_markdown_file(project_md)
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
            emeta, ebody_html = read_markdown_file(edition_md)
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

    return projects, editions


def load_people(people_dir: Path) -> list:
    """Load all people from content/people/."""
    from diablaq_site.models import Person
    from diablaq_site.images import thumb_path_from_photo

    people: list[Person] = []
    for person_md in sorted(people_dir.glob("*.md")):
        meta, body_html = read_markdown_file(person_md)
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
    return people


def load_blog_posts(blog_dir: Path) -> list:
    """Load all blog posts from content/blog/."""
    from diablaq_site.models import BlogPost

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


def build_tags_index(posts: list[BlogPost]) -> dict[str, list[BlogPost]]:
    """Build index of blog posts by tag."""
    tag_map: dict[str, list[BlogPost]] = {}
    for post in posts:
        for tag in post.tags:
            clean = tag.strip()
            if clean:
                tag_map.setdefault(clean, []).append(post)
    return tag_map


def build_nav_projects(projects: list[Project]) -> list[Project]:
    """Sort projects by title for navigation menu."""
    return sorted(projects, key=lambda p: p.title.lower())
