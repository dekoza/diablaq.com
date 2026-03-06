"""Parsing functions for diablaq.com content — frontmatter, dates, metadata validation."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import frontmatter
from markdown import markdown

from diablaq_site.models import BuyLink, Creator, EditionVariant, ImageRef
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
    post = frontmatter.load(str(path))
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

    return creators, names


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
