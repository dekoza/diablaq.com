"""Field-level parsers and validators for diablaq.com frontmatter.

Pure functions that parse, validate, and transform individual frontmatter
field values. No filesystem I/O, no orchestration — just data in, data out.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import frontmatter
from markdown import markdown

from diablaq_site.frontmatter_errors import format_frontmatter_error
from diablaq_site.models import (
    BuyLink,
    Creator,
    EditionCover,
    EditionProduct,
    ImageRef,
)
from diablaq_site.text import _fix_orphans
from diablaq_site.validation import _is_valid_isbn13


def read_markdown_file(path: Path) -> tuple[dict, str]:
    """Read and parse a Markdown file with YAML frontmatter.

    Returns:
        (metadata_dict, html_body_string) tuple
    """
    try:
        post = frontmatter.load(str(path))
    except Exception as exc:  # noqa: BLE001 - preserve parser detail for authors
        source_text = ""
        try:
            source_text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            pass
        details = format_frontmatter_error(exc, source_text=source_text)
        raise ValueError(f"Nie udało się wczytać frontmatter w {path}:\n{details}") from exc
    meta = dict(post.metadata or {})
    body_md = post.content or ""
    body_html = markdown(body_md, extensions=["extra", "sane_lists"])
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
    """Pick the primary cover image used for cards, OG tags, and hero slots."""
    primary_cover = meta.get("primary_cover")
    if not isinstance(primary_cover, dict):
        return None, None

    image = str(primary_cover.get("image") or "").strip() or None
    alt = str(primary_cover.get("alt") or "").strip() or None
    return image, alt


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
    return "".join(ch for ch in value if ch.isdigit())


_ALLOWED_PROJECT_KINDS = {"title", "universe"}
_ALLOWED_PRODUCT_FORMATS = {"zeszyt", "miekka", "twarda", "ebook"}
_LEGACY_EDITION_FIELDS = {"cover_image", "cover_alt", "covers", "specs", "buy_links", "variants"}


def _parse_optional_bool(value: object, *, default: bool, field_name: str, source_path: Path) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "on"}:
        return True
    if text in {"false", "0", "no", "off", ""}:
        return False
    raise ValueError(f"{field_name} musi być wartością bool w {source_path}")


def _parse_optional_positive_int(value: object, *, field_name: str, source_path: Path) -> int | None:
    if value is None or value == "":
        return None
    try:
        parsed = int(str(value).strip())
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"{field_name} musi być liczbą całkowitą w {source_path}") from exc
    if parsed <= 0:
        raise ValueError(f"{field_name} musi być > 0 w {source_path}")
    return parsed


def _parse_optional_ean2(value: object, *, field_name: str, source_path: Path) -> str | None:
    if value is None or value == "":
        return None
    text = str(value).strip()
    if not text.isdigit() or len(text) not in {1, 2}:
        raise ValueError(f"{field_name} musi być 1- lub 2-cyfrowym dodatkiem EAN-2 w {source_path}")
    return text.zfill(2)


def ensure_no_legacy_edition_fields(meta: dict, *, source_path: Path) -> None:
    legacy_keys = sorted(key for key in _LEGACY_EDITION_FIELDS if key in meta)
    if legacy_keys:
        raise ValueError(
            "Wydanie używa legacy fields "
            f"({', '.join(legacy_keys)}) w {source_path}. "
            "Użyj primary_cover, alternate_covers, edition_specs i products."
        )


def _parse_cover_entry(
    item: object,
    *,
    source_path: Path,
    field_name: str,
    default_id: str | None = None,
    require_id: bool = False,
) -> EditionCover:
    if not isinstance(item, dict):
        raise ValueError(f"{field_name} musi być dict w {source_path}")

    cover_id = as_str(item.get("id") or "") or default_id
    if require_id and not cover_id:
        raise ValueError(f"{field_name}.id jest wymagane w {source_path}")
    if not cover_id:
        raise ValueError(f"{field_name}.id jest wymagane w {source_path}")

    image = as_str(item.get("image") or "")
    if not image:
        raise ValueError(f"{field_name}.image jest wymagane w {source_path}")

    label = as_str(item.get("label") or "") or None
    alt = as_str(item.get("alt") or "") or None
    artist_name = as_str(item.get("artist_name") or "") or None
    person_slug = as_str(item.get("person_slug") or "") or None
    return EditionCover(
        id=cover_id,
        label=label,
        image=image,
        alt=alt,
        artist_name=artist_name,
        person_slug=person_slug,
    )


def parse_primary_cover(meta: dict, *, source_path: Path) -> EditionCover | None:
    raw = meta.get("primary_cover")
    if raw is None:
        return None
    return _parse_cover_entry(
        raw,
        source_path=source_path,
        field_name="primary_cover",
        default_id="primary",
    )


def parse_cover_list(meta: dict, key: str, *, source_path: Path) -> list[EditionCover]:
    raw = meta.get(key)
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError(f"{key} musi być listą w {source_path}")

    covers: list[EditionCover] = []
    seen_ids: set[str] = set()
    for i, item in enumerate(raw):
        cover = _parse_cover_entry(
            item,
            source_path=source_path,
            field_name=f"{key}[{i}]",
            require_id=True,
        )
        if cover.id == "primary":
            raise ValueError(f"{key}[{i}].id nie może mieć wartości 'primary' w {source_path}")
        if cover.id in seen_ids:
            raise ValueError(f"duplicate id={cover.id!r} in {key} w {source_path}")
        seen_ids.add(cover.id)
        covers.append(cover)

    return covers


def parse_products(
    meta: dict,
    *,
    source_path: Path,
    primary_cover: EditionCover | None,
    alternate_covers: list[EditionCover],
) -> list[EditionProduct]:
    raw = meta.get("products")
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError(f"products musi być listą w {source_path}")

    available_cover_ids = {cover.id for cover in alternate_covers}
    if primary_cover is not None:
        available_cover_ids.add("primary")

    products: list[EditionProduct] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"products[{i}] musi być dict w {source_path}")

        format_name = as_str(item.get("format") or "")
        if format_name not in _ALLOWED_PRODUCT_FORMATS:
            raise ValueError(
                f"products[{i}].format musi być jednym z {sorted(_ALLOWED_PRODUCT_FORMATS)} w {source_path}"
            )

        cover_id = as_str(item.get("cover_id") or "") or None
        if cover_id is None and primary_cover is not None:
            cover_id = "primary"
        if cover_id is not None and cover_id not in available_cover_ids:
            raise ValueError(f"products[{i}].cover_id={cover_id!r} nie istnieje w {source_path}")

        raw_isbn13 = as_str(item.get("isbn13") or "")
        isbn13 = _normalize_isbn13(raw_isbn13) or None
        if isbn13 and not _is_valid_isbn13(isbn13):
            raise ValueError(
                f"products[{i}].isbn13={item.get('isbn13')!r} nie wygląda jak poprawny ISBN-13 w {source_path}"
            )

        limited = _parse_optional_bool(
            item.get("limited"),
            default=False,
            field_name=f"products[{i}].limited",
            source_path=source_path,
        )
        numbered_copies = _parse_optional_positive_int(
            item.get("numbered_copies"),
            field_name=f"products[{i}].numbered_copies",
            source_path=source_path,
        )
        if numbered_copies is not None and not limited:
            raise ValueError(
                f"products[{i}].numbered_copies wymaga limited=true w {source_path}"
            )

        products.append(
            EditionProduct(
                format=format_name,
                cover_id=cover_id,
                label=as_str(item.get("label") or "") or None,
                isbn13=isbn13,
                ean2=_parse_optional_ean2(
                    item.get("ean2"),
                    field_name=f"products[{i}].ean2",
                    source_path=source_path,
                ),
                price=as_str(item.get("price") or "") or None,
                limited=limited,
                numbered_copies=numbered_copies,
                buy_links=parse_buy_links(
                    {"buy_links": item.get("buy_links")},
                    source_path=source_path,
                ),
                specs=parse_specs(item),
            )
        )

    return products


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
        if name not in names:
            names.append(name)

    return creators, names


def parse_specs(meta: dict, key: str = "specs") -> dict[str, str]:
    """Parse a specs dictionary from metadata.

    Invalid or missing values are treated as an empty mapping to keep authoring forgiving.
    """
    raw = meta.get(key)
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        return {}

    out: dict[str, str] = {}
    for item_key, item_value in raw.items():
        if item_value is None:
            continue
        normalized_key = as_str(item_key)
        normalized_value = as_str(item_value)
        if normalized_key and normalized_value:
            out[normalized_key] = normalized_value
    return out
