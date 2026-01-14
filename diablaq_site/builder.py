from __future__ import annotations

import os
import re
import shutil
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import quote

import frontmatter
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown import markdown
from PIL import Image


# Lista polskich spójników i przyimków, które nie powinny zostawać na końcu linii
_ORPHAN_WORDS = {
    # Spójniki
    "a", "i", "o", "u", "w", "z", "k",
    # Przyimki
    "do", "na", "od", "po", "za", "ze", "we", "ku",
    # Inne krótkie słowa
    "to", "co", "że", "by", "są", "je", "go", "mu", "ją", "mi", "ty", "on", "my", "wy",
}

# Regex pattern: spacja + słowo z listy + spacja (case insensitive)
_ORPHAN_PATTERN = re.compile(
    r'(\s)(' + '|'.join(re.escape(w) for w in _ORPHAN_WORDS) + r')(\s)',
    re.IGNORECASE
)


def _fix_orphans(text: str) -> str:
    """Zamienia spację po spójnikach/przyimkach na &nbsp; aby uniknąć zawieszek.

    Przykład: "W tym tygodniu o godzinie" -> "W&nbsp;tym tygodniu o&nbsp;godzinie"
    """
    def replace_orphan(match: re.Match) -> str:
        before_space = match.group(1)
        word = match.group(2)
        # Zamieniamy spację PO słowie na &nbsp;
        return f'{before_space}{word}&nbsp;'

    # Iterujemy wielokrotnie, bo pattern może się nakładać
    prev_text = None
    while prev_text != text:
        prev_text = text
        text = _ORPHAN_PATTERN.sub(replace_orphan, text)

    return text


@dataclass(frozen=True)
class BuyLink:
    label: str
    url: str


@dataclass(frozen=True)
class EditionVariant:
    """Pojedynczy wariant wydania bez osobnej podstrony.

    Wariant może opisywać oprawę (miękka/twarda) albo wersję (elektroniczna).

    Dane w frontmatter (docelowo):

    variants:
      - binding: miekka
        isbn13: "..."
        buy_links: [...]

      - version: elektroniczna
        isbn13: "..."
        buy_links: [...]

    Dla kompatybilności wspieramy też legacy:
      - kind: miekka|twarda|elektroniczna
    """

    binding: str | None  # miekka | twarda
    version: str | None  # elektroniczna
    isbn13: str
    limited_print_run: int | None
    numbered: bool
    buy_links: list[BuyLink]


@dataclass(frozen=True)
class Creator:
    role: str | None
    name: str
    person_slug: str | None


@dataclass(frozen=True)
class ImageRef:
    image: str
    alt: str | None
    caption: str | None


@dataclass(frozen=True)
class Edition:
    url: str
    title: str
    project_slug: str
    release: str | None
    release_date: date
    is_new: bool
    is_announcement: bool
    presale_url: str | None
    legacy_anchor: str | None
    cover_image: str | None
    cover_alt: str | None
    cover_aspect_class: str
    covers: list[ImageRef]
    previews: list[ImageRef]
    creators: list[Creator]
    creator_names: list[str]
    specs: dict[str, str]
    buy_links: list[BuyLink]
    variants: list[EditionVariant]
    html_body: str
    standalone: bool
    subseries: str | None
    issue_number: int | None
    issue_number_display: str | None


@dataclass(frozen=True)
class Project:
    slug: str
    title: str
    line: str
    summary: str | None
    legacy_path: str | None
    url: str
    legacy_landing: bool
    cover_image: str | None
    cover_aspect_class: str
    html_body: str


@dataclass(frozen=True)
class Person:
    slug: str
    name: str
    photo: str | None
    photo_thumb: str | None
    html_bio: str
    related_editions: list[Edition]


@dataclass(frozen=True)
class Page:
    slug: str
    title: str
    html_body: str


@dataclass(frozen=True)
class BlogPost:
    url: str
    slug: str
    title: str
    date: date
    summary: str | None
    cover_image: str | None
    cover_alt: str | None
    tags: list[str]
    html_body: str


def _slugify_tag(tag: str) -> str:
    # Do URL-i tagów stosujemy quote (w UTF-8) i zachowujemy spacje jako %20.
    return quote(tag.strip(), safe="")


def _parse_date(value: str, *, source_path: Path) -> date:
    try:
        yyyy, mm, dd = value.split("-")
        return date(int(yyyy), int(mm), int(dd))
    except Exception as exc:  # noqa: BLE001 - want a clear error
        raise ValueError(
            f"Nieprawidłowe release_date={value!r} w {source_path}. Oczekiwany format YYYY-MM-DD."
        ) from exc


def _parse_optional_date(value: object, *, source_path: Path) -> date | None:
    if value is None:
        return None
    if value == "":
        return None
    return _parse_date(str(value), source_path=source_path)


def _derive_flags(*, release_date: date | None, today: date) -> tuple[bool, bool]:
    """Wylicza (is_new, is_announcement) bez ręcznych flag.

    Zasady:
    1) brak daty -> zapowiedź
    2) przyszła data -> zapowiedź
    3) data dziś lub przeszła -> nowość przez 6 tygodni od premiery
    """

    if release_date is None:
        return False, True

    if release_date > today:
        return False, True

    # release_date <= today
    if today <= (release_date + timedelta(weeks=6)):
        return True, False

    return False, False


def _read_markdown_file(path: Path) -> tuple[dict, str]:
    post = frontmatter.load(str(path))
    meta = dict(post.metadata or {})
    body_md = post.content or ""
    body_html = markdown(body_md, extensions=["extra", "sane_lists"])
    # Napraw zawieszki typograficzne (spójniki na końcu linii)
    body_html = _fix_orphans(body_html)
    return meta, body_html


def _copy_tree(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    shutil.copytree(src, dst, dirs_exist_ok=True)


def _get_cover_aspect_class(cover_path: str | None, root: Path) -> str:
    """Zwraca klasę CSS na podstawie proporcji okładki.

    - cover--tall: ratio < 0.6 (wysoka okładka) -> object-position: top
    - cover--wide: ratio > 0.75 (szeroka okładka) -> object-fit: contain
    - cover--standard: pozostałe -> object-position: center
    """
    if not cover_path:
        return "cover--standard"

    # Usuń leading slash i znajdź plik
    relative_path = cover_path.lstrip("/")
    full_path = root / relative_path

    if not full_path.exists():
        return "cover--standard"

    try:
        with Image.open(full_path) as img:
            ratio = img.width / img.height
            if ratio > 0.75:
                return "cover--wide"
            elif ratio < 0.6:
                return "cover--tall"
            return "cover--standard"
    except Exception:
        return "cover--standard"


def _generate_thumbnail(src: Path, dst: Path, size: tuple[int, int] = (300, 300)) -> None:
    """Generuje miniaturę zdjęcia o podanym rozmiarze (domyślnie 300x300)."""
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as img:
        # Konwersja do RGB jeśli potrzeba (np. dla RGBA/PNG)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        # Thumbnail zachowuje proporcje i mieści się in podanym rozmiarze
        img.thumbnail(size, Image.Resampling.LANCZOS)
        img.save(dst, "JPEG", quality=85, optimize=True)


def _thumb_path_from_photo(photo_path: str) -> str:
    """Generuje ścieżkę do miniatury na podstawie ścieżki do zdjęcia."""
    p = Path(photo_path)
    return str(p.parent / f"{p.stem}_thumb.jpg")


def _write_html(path: Path, html: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def _render(env: Environment, template_name: str, **ctx):
    template = env.get_template(template_name)
    return template.render(**ctx)


def _coerce_str_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _pick_cover(meta: dict) -> tuple[str | None, str | None]:
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


def _parse_image_list(meta: dict, key: str, *, source_path: Path) -> list[ImageRef]:
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


def _as_str(value) -> str:
    return str(value).strip()


def _parse_buy_links(meta: dict, *, source_path: Path) -> list[BuyLink]:
    raw = meta.get("buy_links")
    if raw is None:
        return []

    if not isinstance(raw, list):
        raise ValueError(f"buy_links musi być listą w {source_path}")

    links: list[BuyLink] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"buy_links[{i}] musi być dict w {source_path}")

        label = _as_str(item.get("label") or "")
        url = _as_str(item.get("url") or "")
        if not label or not url:
            raise ValueError(f"buy_links[{i}] musi mieć label i url w {source_path}")
        links.append(BuyLink(label=label, url=url))

    return links


def _normalize_isbn13(value: str) -> str:
    # Akceptujemy zapis z myślnikami/spacjami, ale przechodzimy na ciąg cyfr.
    return "".join(ch for ch in value if ch.isdigit())


def _is_valid_isbn13(isbn13: str) -> bool:
    """Walidacja checksum ISBN-13.

    Zasada: (suma cyfr na pozycjach parzystych*3 + nieparzystych) % 10 == 0.
    """

    if len(isbn13) != 13 or not isbn13.isdigit():
        return False

    total = 0
    for idx, ch in enumerate(isbn13):
        digit = int(ch)
        total += digit * 3 if (idx % 2 == 1) else digit

    return total % 10 == 0


_ALLOWED_BINDINGS = {"miekka", "twarda"}
_ALLOWED_VERSIONS = {"elektroniczna"}
_ALLOWED_VARIANT_KINDS = _ALLOWED_BINDINGS | _ALLOWED_VERSIONS


def _parse_variants(meta: dict, *, source_path: Path) -> list[EditionVariant]:
    raw = meta.get("variants")
    if raw is None:
        return []

    if not isinstance(raw, list):
        raise ValueError(f"variants musi być listą w {source_path}")

    out: list[EditionVariant] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"variants[{i}] musi być dict w {source_path}")

        # Nowy format: binding/version; fallback: legacy kind
        binding = _as_str(item.get("binding") or "") or None
        version = _as_str(item.get("version") or "") or None

        legacy_kind = _as_str(item.get("kind") or "") or None
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

        isbn13 = _normalize_isbn13(_as_str(item.get("isbn13") or ""))
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
                raise ValueError(
                    f"variants[{i}].limited_print_run musi być > 0 w {source_path}"
                )

        numbered_raw = item.get("numbered")
        numbered = bool(numbered_raw) if numbered_raw is not None else False
        if numbered and limited_print_run is None:
            raise ValueError(
                f"variants[{i}].numbered=true wymaga podania limited_print_run w {source_path}"
            )

        buy_links = _parse_buy_links({"buy_links": item.get("buy_links")}, source_path=source_path)
        if not buy_links:
            raise ValueError(
                f"variants[{i}].buy_links jest wymagane (lista linków zakupowych per wariant) w {source_path}"
            )

        out.append(
            EditionVariant(
                binding=binding,
                version=version,
                isbn13=isbn13,
                limited_print_run=limited_print_run,
                numbered=numbered,
                buy_links=buy_links,
            )
        )

    return out


def _parse_creators(meta: dict, *, source_path: Path) -> tuple[list[Creator], list[str]]:
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

    return creators, names


def _parse_specs(meta: dict) -> dict[str, str]:
    raw = meta.get("specs")
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        return {}

    out: dict[str, str] = {}
    for k, v in raw.items():
        if v is None:
            continue
        key = _as_str(k)
        val = _as_str(v)
        if key and val:
            out[key] = val
    return out


def _canonical_project_url(*, line: str, slug: str) -> str:
    if line == "diablaq":
        return f"/publikacje/{slug}/"
    if line == "dobre-licho":
        return f"/dobre-licho/{slug}/"
    if line in {"mecenat", "studio"}:
        return f"/{line}/{slug}/"
    # fallback: traktuj jak publikacje
    return f"/publikacje/{slug}/"


def _canonical_edition_url(*, line: str, project_slug: str, edition_slug: str) -> str:
    # Specjalny przypadek: index.md -> URL projektu (bez /index/)
    if edition_slug == "index":
        return _canonical_project_url(line=line, slug=project_slug)

    if line == "diablaq":
        return f"/publikacje/{project_slug}/{edition_slug}/"
    if line == "dobre-licho":
        return f"/dobre-licho/{project_slug}/{edition_slug}/"
    if line in {"mecenat", "studio"}:
        return f"/{line}/{project_slug}/{edition_slug}/"
    return f"/publikacje/{project_slug}/{edition_slug}/"


def build_site(*, root: Path, out_dir: Path) -> None:
    templates_dir = root / "templates"
    content_dir = root / "content"

    if not templates_dir.exists():
        raise FileNotFoundError(f"Brak katalogu templates/: {templates_dir}")

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )

    # Bazowy URL strony do canonical (opcjonalny, ale zalecany na produkcji).
    # Jeśli nie ustawisz, canonical będzie ścieżką absolutną (np. /publikacje/spolka-zlo/01/).
    site_url = os.environ.get("DIABLAQ_SITE_URL", "").rstrip("/")

    # --- load content
    projects: list[Project] = []
    editions: list[Edition] = []
    people: list[Person] = []
    pages: list[Page] = []
    blog_posts: list[BlogPost] = []

    # Pages (content/pages/*.md)
    pages_root = content_dir / "pages"
    for page_md in sorted(pages_root.glob("*.md")):
        meta, body_html = _read_markdown_file(page_md)
        slug = page_md.stem
        title = str(meta.get("title") or slug)
        pages.append(Page(slug=slug, title=title, html_body=body_html))

    # Projects (content/projects/<slug>/project.md)
    projects_root = content_dir / "projects"
    for project_dir in sorted(projects_root.glob("*/")):
        project_md = project_dir / "project.md"
        if not project_md.exists():
            continue

        meta, body_html = _read_markdown_file(project_md)
        slug = project_dir.name
        title = str(meta.get("title") or slug)
        line = str(meta.get("line") or "diablaq")
        summary = meta.get("summary")
        legacy_path = meta.get("legacy_path")
        legacy_landing = bool(meta.get("legacy_landing", False))
        cover_image = str(meta.get("cover_image") or "").strip() or None
        cover_aspect_class = _get_cover_aspect_class(cover_image, root)

        url = _canonical_project_url(line=line, slug=slug)

        projects.append(
            Project(
                slug=slug,
                title=title,
                line=line,
                summary=summary,
                legacy_path=legacy_path,
                url=url,
                legacy_landing=legacy_landing,
                cover_image=cover_image,
                cover_aspect_class=cover_aspect_class,
                html_body=body_html,
            )
        )

        # Editions - zbieramy tymczasowo dane, potem nadajemy numerację
        project_editions_data: list[tuple[dict, str, date, str]] = []  # (emeta, ebody_html, sort_date, ed_slug)

        for edition_md in sorted((project_dir / "editions").glob("*.md")):
            emeta, ebody_html = _read_markdown_file(edition_md)

            # release_date może być brak/None: wtedy to zapowiedź
            release_date = _parse_optional_date(
                emeta.get("release_date"),
                source_path=edition_md,
            )

            ed_slug = edition_md.stem

            # Jeśli release_date jest None, do sortowania/listingów przyjmujemy bardzo odległą przyszłość.
            sort_date = release_date or date(9999, 12, 31)

            project_editions_data.append((emeta, ebody_html, sort_date, ed_slug))

        # Automatyczna numeracja dla nie-standalone wydań, grupowana po subseries
        # Każda podseria (lub brak = główna) ma własną niezależną numerację
        subseries_editions: dict[str | None, list[tuple[dict, str, date, str]]] = defaultdict(list)
        for emeta, ebody_html, sort_date, ed_slug in project_editions_data:
            if not emeta.get("standalone", False):
                subseries_key = emeta.get("subseries")  # None = seria główna
                subseries_editions[subseries_key].append((emeta, ebody_html, sort_date, ed_slug))

        # Mapuj slug -> numer (tylko dla nie-standalone, per subseries)
        slug_to_number: dict[str, int] = {}
        slug_to_subseries: dict[str, str | None] = {}

        for subseries_key, items in subseries_editions.items():
            # Sortuj chronologicznie (od najstarszych) dla przypisania numerów
            items_sorted = sorted(items, key=lambda x: x[2])  # sort by sort_date
            for idx, (emeta, _, _, ed_slug) in enumerate(items_sorted, start=1):
                # Ręczny numer ma priorytet
                manual_number = emeta.get("issue_number")
                if manual_number is not None:
                    slug_to_number[ed_slug] = int(manual_number)
                else:
                    slug_to_number[ed_slug] = idx
                slug_to_subseries[ed_slug] = subseries_key

        # Teraz twórz obiekty Edition z numeracją
        for emeta, ebody_html, sort_date, ed_slug in project_editions_data:
            release_date = _parse_optional_date(
                emeta.get("release_date"),
                source_path=project_dir / "editions" / f"{ed_slug}.md",
            )

            force_new = bool(emeta.get("force_new", False) or emeta.get("is_new", False))
            force_announcement = bool(
                emeta.get("force_announcement", False) or emeta.get("is_announcement", False)
            )
            if force_new and force_announcement:
                raise ValueError(
                    f"Pozycja nie może mieć jednocześnie force_new i force_announcement: {project_dir / 'editions' / ed_slug}.md"
                )

            auto_is_new, auto_is_announcement = _derive_flags(release_date=release_date, today=date.today())

            is_new = force_new or (auto_is_new and not force_announcement)
            is_announcement = force_announcement or (auto_is_announcement and not force_new)

            # Kanoniczne URL-e dla wydań (wg planu):
            ed_url = _canonical_edition_url(line=line, project_slug=slug, edition_slug=ed_slug)

            cover_image, cover_alt = _pick_cover(emeta)
            cover_aspect_class = _get_cover_aspect_class(cover_image, root)
            covers = _parse_image_list(emeta, "covers", source_path=project_dir / "editions" / f"{ed_slug}.md")
            previews = _parse_image_list(emeta, "previews", source_path=project_dir / "editions" / f"{ed_slug}.md")
            creators, creator_names = _parse_creators(emeta, source_path=project_dir / "editions" / f"{ed_slug}.md")
            specs = _parse_specs(emeta)
            buy_links = _parse_buy_links(emeta, source_path=project_dir / "editions" / f"{ed_slug}.md")
            variants = _parse_variants(emeta, source_path=project_dir / "editions" / f"{ed_slug}.md")

            # Standalone, subseries i numeracja
            is_standalone = bool(emeta.get("standalone", False))
            subseries = str(emeta.get("subseries") or "").strip() or None
            if is_standalone:
                issue_number = None
                issue_number_display = None
            else:
                issue_number = slug_to_number.get(ed_slug)
                issue_number_display = f"{issue_number:02d}" if issue_number is not None else None

            editions.append(
                Edition(
                    url=ed_url,
                    title=str(emeta.get("title") or ed_slug),
                    project_slug=slug,
                    release=str(emeta.get("release") or "") or None,
                    release_date=sort_date,
                    is_new=is_new,
                    is_announcement=is_announcement,
                    presale_url=emeta.get("presale_url"),
                    legacy_anchor=emeta.get("legacy_anchor"),
                    cover_image=cover_image,
                    cover_alt=cover_alt,
                    cover_aspect_class=cover_aspect_class,
                    covers=covers,
                    previews=previews,
                    creators=creators,
                    creator_names=creator_names,
                    specs=specs,
                    buy_links=buy_links,
                    variants=variants,
                    html_body=ebody_html,
                    standalone=is_standalone,
                    subseries=subseries,
                    issue_number=issue_number,
                    issue_number_display=issue_number_display,
                )
            )

    # People (content/people/*.md)
    people_root = content_dir / "people"
    for person_md in sorted(people_root.glob("*.md")):
        meta, body_html = _read_markdown_file(person_md)
        slug = person_md.stem
        name = str(meta.get("name") or slug)
        photo = str(meta.get("photo") or "").strip() or None
        # Automatycznie generuj ścieżkę miniatury jeśli jest zdjęcie
        if photo:
            photo_thumb = _thumb_path_from_photo(photo)
        else:
            photo_thumb = None
        people.append(Person(slug=slug, name=name, photo=photo, photo_thumb=photo_thumb, html_bio=body_html, related_editions=[]))

    # Blog posts (content/blog/*.md)
    blog_root = content_dir / "blog"
    if blog_root.exists():
        for post_md in sorted(blog_root.glob("*.md")):
            meta, body_html = _read_markdown_file(post_md)

            if bool(meta.get("draft", False)):
                continue

            title = str(meta.get("title") or post_md.stem)
            if "date" not in meta:
                raise ValueError(f"Brak date w {post_md}")

            post_date = _parse_date(str(meta["date"]), source_path=post_md)
            summary = str(meta.get("summary") or "").strip() or None
            cover_image = str(meta.get("cover_image") or "").strip() or None
            cover_alt = str(meta.get("cover_alt") or "").strip() or None
            tags = _coerce_str_list(meta.get("tags"))

            # slug: prefer frontmatter, fallback: filename without leading date prefix
            raw_slug = str(meta.get("slug") or post_md.stem)
            # if looks like YYYY-MM-DD-..., strip date prefix
            parts = raw_slug.split("-", 3)
            if len(parts) >= 4 and all(p.isdigit() for p in parts[:3]):
                slug = parts[3]
            else:
                slug = raw_slug

            url = f"/blog/{slug}/"

            blog_posts.append(
                BlogPost(
                    url=url,
                    slug=slug,
                    title=title,
                    date=post_date,
                    summary=summary,
                    cover_image=cover_image,
                    cover_alt=cover_alt,
                    tags=tags,
                    html_body=body_html,
                )
            )

    # --- derived lists
    new_editions = sorted(
        [e for e in editions if e.is_new], key=lambda e: e.release_date, reverse=True
    )
    announcements = sorted(
        [e for e in editions if e.is_announcement],
        key=lambda e: e.release_date,
        reverse=True,
    )

    # Fallback: 4 najnowsze wydania niezależnie od klasyfikacji (ignorujemy datę 9999-12-31)
    all_editions_sorted = sorted(
        [e for e in editions if e.release_date.year < 9999],
        key=lambda e: e.release_date,
        reverse=True,
    )
    newest_anytime = all_editions_sorted[:4]

    blog_posts_sorted = sorted(blog_posts, key=lambda p: p.date, reverse=True)

    # Powiązane publikacje dla ludzi (po person_slug + fallback po nazwie)
    people_with_editions: list[Person] = []
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
        related_sorted = sorted(related, key=lambda e: e.release_date, reverse=True)
        people_with_editions.append(
            Person(
                slug=person.slug,
                name=person.name,
                photo=person.photo,
                photo_thumb=person.photo_thumb,
                html_bio=person.html_bio,
                related_editions=related_sorted,
            )
        )

    people = people_with_editions

    nav_projects = sorted(projects, key=lambda p: p.title.lower())

    def render(template_name: str, **ctx) -> str:
        return _render(
            env,
            template_name,
            nav_projects=nav_projects,
            site_url=site_url,
            **ctx,
        )

    def _abs_url(path: str) -> str:
        path = "/" + path.lstrip("/")
        return f"{site_url}{path}" if site_url else path

    # --- render pages
    # Home
    html = render(
        "home.html",
        canonical_url=_abs_url("/"),
        projects=projects,
        new_editions=new_editions[:12],
        announcements=announcements[:12],
    )
    _write_html(out_dir / "index.html", html)

    # Listing pages
    # /nowe/ – jeśli puste, pokaż 4 najnowsze wydania niezależnie od daty
    nowe_items = new_editions if new_editions else newest_anytime
    nowe_desc = (
        "Najnowsze wydania Diablaq. \n"
        "Jeśli w tej chwili nie ma aktywnych 'nowości' (okno 6 tygodni), pokazujemy ostatnie publikacje."
    )
    html = render(
        "listing.html",
        canonical_url=_abs_url("/nowe/"),
        title="Nowości",
        description=nowe_desc,
        items=nowe_items,
    )
    _write_html(out_dir / "nowe" / "index.html", html)

    # /zapowiedzi/ – jeśli puste, pokaż komunikat
    zap_empty = "Już wkrótce ogłosimy kolejne zapowiedzi. Zajrzyj ponownie za jakiś czas."
    html = render(
        "listing.html",
        canonical_url=_abs_url("/zapowiedzi/"),
        title="Zapowiedzi",
        description="Co nowego nadchodzi w Diablaq.",
        items=announcements,
        empty_message=zap_empty if not announcements else None,
    )
    _write_html(out_dir / "zapowiedzi" / "index.html", html)

    # Pages
    for page in pages:
        html = render("page.html", canonical_url=_abs_url(f"/{page.slug}/"), page=page)
        _write_html(out_dir / page.slug / "index.html", html)

    # People
    html = render("people_index.html", canonical_url=_abs_url("/ludzie/"), people=people)
    _write_html(out_dir / "ludzie" / "index.html", html)

    for p in people:
        html = render(
            "person.html",
            canonical_url=_abs_url(f"/ludzie/{p.slug}/"),
            person=p,
        )
        _write_html(out_dir / "ludzie" / p.slug / "index.html", html)

    # Blog
    html = render("blog_index.html", canonical_url=_abs_url("/blog/"), posts=blog_posts_sorted)
    _write_html(out_dir / "blog" / "index.html", html)

    for post in blog_posts_sorted:
        tags = [{"name": t, "url": f"/blog/tag/{_slugify_tag(t)}/"} for t in post.tags]
        html = render(
            "blog_post.html",
            canonical_url=_abs_url(post.url),
            post=post,
            post_tags=tags,
        )
        _write_html(out_dir / post.url.strip("/") / "index.html", html)

    # Tag listing pages
    tag_map: dict[str, list[BlogPost]] = {}
    for post in blog_posts_sorted:
        for tag in post.tags:
            t = tag.strip()
            if not t:
                continue
            tag_map.setdefault(t, []).append(post)

    for tag, items in sorted(tag_map.items(), key=lambda kv: kv[0].lower()):
        tag_slug = _slugify_tag(tag)
        html = render(
            "blog_index.html",
            canonical_url=_abs_url(f"/blog/tag/{tag_slug}/"),
            posts=sorted(items, key=lambda p: p.date, reverse=True),
        )
        _write_html(out_dir / "blog" / "tag" / tag_slug / "index.html", html)

    # Projects and editions pages
    for pr in projects:
        pr_editions = [e for e in editions if e.project_slug == pr.slug]
        pr_editions_sorted = sorted(pr_editions, key=lambda e: e.release_date, reverse=True)

        # Jeśli jest wydanie o slugu `index`, traktujemy je jako treść jednotomówki
        # pod URL projektu (bez /index/).
        index_edition = next((e for e in pr_editions_sorted if e.url.endswith("/index/")), None)

        # Render kanoniczna strona projektu
        html = render(
            "project.html",
            canonical_url=_abs_url(pr.url),
            project=pr,
            editions=pr_editions_sorted,
        )
        _write_html(out_dir / pr.url.strip("/") / "index.html", html)

        # Legacy landing: generuj dodatkowo stronę pod legacy_path (te same treści)
        if (
            pr.legacy_landing
            and pr.legacy_path
            and pr.legacy_path.rstrip("/") != pr.url.rstrip("/")
        ):
            _write_html(out_dir / pr.legacy_path.strip("/") / "index.html", html)

        # Legacy alias 1: alias /<slug>/ (jeśli kanoniczny URL jest inny)
        legacy_slug_path = f"/{pr.slug}/"
        if legacy_slug_path.rstrip("/") != pr.url.rstrip("/"):
            if pr.legacy_landing and legacy_slug_path.rstrip("/") == (pr.legacy_path or "").rstrip(
                "/"
            ):
                pass
            else:
                legacy_html = render(
                    "redirect.html",
                    canonical_url=_abs_url(pr.url),
                    to_url=pr.url,
                )
                _write_html(out_dir / pr.slug / "index.html", legacy_html)

        # Legacy alias 2: jeśli legacy_path jest inny niż kanoniczny i NIE jest landingiem
        if (
            pr.legacy_path
            and pr.legacy_path.rstrip("/") != pr.url.rstrip("/")
            and not pr.legacy_landing
            and pr.legacy_path.rstrip("/") != legacy_slug_path.rstrip("/")
        ):
            legacy_html = render(
                "redirect.html",
                canonical_url=_abs_url(pr.url),
                to_url=pr.url,
            )
            _write_html(out_dir / pr.legacy_path.strip("/") / "index.html", legacy_html)

        for e in pr_editions_sorted:
            # Jeśli jednotomówka siedzi w `index.md`, to jej podstrona to URL projektu.
            # Nie generujemy więc /.../index/.
            if e.url.endswith("/index/"):
                continue

            html = render(
                "edition.html",
                canonical_url=_abs_url(e.url),
                edition=e,
                project=pr,
            )
            out_path = out_dir / e.url.strip("/") / "index.html"
            _write_html(out_path, html)

    # Special legacy alias rules (minimal): /zvyrke/ -> /ludzie/zvyrke/
    zv = next((p for p in people if p.slug == "zvyrke"), None)
    if zv is not None:
        html = render(
            "redirect.html",
            canonical_url=_abs_url(f"/ludzie/{zv.slug}/"),
            to_url=f"/ludzie/{zv.slug}/",
        )
        _write_html(out_dir / "zvyrke" / "index.html", html)

    # --- sections (landing pages)
    def _write_section(path_slug: str, *, title: str, line: str, description: str | None = None) -> None:
        items = [p for p in projects if p.line == line]
        html = render(
            "section.html",
            canonical_url=_abs_url(f"/{path_slug}/"),
            title=title,
            description=description,
            projects=items,
        )
        _write_html(out_dir / path_slug / "index.html", html)

    _write_section(
        "publikacje",
        title="Publikacje",
        line="diablaq",
        description="Główna linia wydawnicza Diablaq.",
    )
    _write_section(
        "dobre-licho",
        title="Dobre Licho",
        line="dobre-licho",
        description="Imprint dla dzieci.",
    )
    _write_section(
        "mecenat",
        title="Mecenat",
        line="mecenat",
        description="Publikacje rozwijane w formule mecenatu.",
    )

    # Studio generujemy tylko, jeśli w ogóle są projekty studio
    if any(p.line == "studio" for p in projects):
        _write_section(
            "studio",
            title="Studio",
            line="studio",
            description="Produkcje komiksowe dla innych wydawnictw/klientów.",
        )

    # --- copy static assets
    _copy_tree(root / "img", out_dir / "img")
    _copy_tree(root / "css", out_dir / "css")

    # --- generate thumbnails for people photos
    for person in people:
        if person.photo:
            # photo jest ścieżką URL np. "/img/people/qrjusz.jpg"
            # musimy znaleźć plik źródłowy i wygenerować miniaturę
            src_photo = root / person.photo.lstrip("/")
            if src_photo.exists():
                thumb_path = _thumb_path_from_photo(person.photo)
                dst_thumb = out_dir / thumb_path.lstrip("/")
                _generate_thumbnail(src_photo, dst_thumb)

    for file_name in ["CNAME", ".nojekyll"]:
        src = root / file_name
        if src.exists():
            shutil.copy2(src, out_dir / file_name)
