"""Batch-edit project and edition copy through a single workbook file."""

from __future__ import annotations

import argparse
import re
import sys
import textwrap
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import frontmatter


DEFAULT_WORKBOOK_NAME = "project-page-workbook.md"
_NEW_EDITION_PLACEHOLDER = "__new_edition__"
_LINE_OPTIONS = ("diablaq", "dobre-licho", "mecenat", "studio")
_PROJECT_KIND_OPTIONS = ("title", "universe")
_PRODUCT_FORMAT_OPTIONS = ("zeszyt", "miekka", "twarda", "ebook")
_BOOL_OPTIONS = ("true", "false")
_PROJECT_STATUS_ORDER = {
    "missing-project-file": 0,
    "empty-file": 1,
    "missing-frontmatter": 2,
    "invalid-frontmatter": 3,
    "missing-body": 4,
    "missing-summary": 5,
    "short-body": 6,
}
_EDITION_STATUS_ORDER = {
    "empty-file": 0,
    "missing-frontmatter": 1,
    "invalid-frontmatter": 2,
    "missing-title": 3,
    "missing-body": 4,
    "short-body": 5,
}
_STATUS_LABELS = {
    "missing-project-file": "brak pliku project.md",
    "empty-file": "pusty plik",
    "missing-frontmatter": "brak frontmatter",
    "invalid-frontmatter": "zepsuty frontmatter",
    "missing-body": "brak opisu",
    "missing-summary": "brak summary",
    "short-body": "krótki opis",
    "missing-title": "brak title",
}
_FRONTMATTER_BLOCK_RE = re.compile(
    r"<!-- FRONTMATTER START: (?P<slug>[a-z0-9-]+) -->\n"
    r"(?P<content>.*?)\n"
    r"<!-- FRONTMATTER END: (?P=slug) -->",
    re.DOTALL,
)
_BODY_BLOCK_RE = re.compile(
    r"<!-- BODY START: (?P<slug>[a-z0-9-]+) -->\n"
    r"(?P<content>.*?)\n"
    r"<!-- BODY END: (?P=slug) -->",
    re.DOTALL,
)
_EDITION_FRONTMATTER_BLOCK_RE = re.compile(
    r"<!-- EDITION FRONTMATTER START: (?P<project>[a-z0-9-]+)/(?P<edition>[a-z0-9_][a-z0-9_-]*) -->\n"
    r"(?P<content>.*?)\n"
    r"<!-- EDITION FRONTMATTER END: (?P=project)/(?P=edition) -->",
    re.DOTALL,
)
_EDITION_BODY_BLOCK_RE = re.compile(
    r"<!-- EDITION BODY START: (?P<project>[a-z0-9-]+)/(?P<edition>[a-z0-9_][a-z0-9_-]*) -->\n"
    r"(?P<content>.*?)\n"
    r"<!-- EDITION BODY END: (?P=project)/(?P=edition) -->",
    re.DOTALL,
)
_SIMPLE_SCALAR_RE = re.compile(r"^[A-Za-z0-9_./-]+$")
_INTEGER_RE = re.compile(r"^-?\d+$")


@dataclass(frozen=True)
class EditionEntry:
    project_slug: str
    slug: str
    path: Path
    frontmatter_block: str
    body: str
    statuses: tuple[str, ...]
    title: str
    release_label: str | None
    creators: tuple[str, ...]
    cover_image: str | None
    teaser: str | None
    parse_error: str | None
    is_template: bool = False

    @property
    def workbook_id(self) -> str:
        return f"{self.project_slug}/{self.slug}"

    @property
    def filename(self) -> str:
        return f"{self.slug}.md"


@dataclass(frozen=True)
class ProjectEntry:
    slug: str
    path: Path
    frontmatter_block: str
    body: str
    statuses: tuple[str, ...]
    title: str
    line: str | None
    summary: str | None
    cover_image: str | None
    editions: tuple[EditionEntry, ...]
    editable_editions: tuple[EditionEntry, ...]
    new_edition_template: EditionEntry
    parse_error: str | None


def _string_value(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _yaml_scalar(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"

    text = str(value).strip()
    if not text:
        return '""'

    lowered = text.lower()
    if (
        _SIMPLE_SCALAR_RE.fullmatch(text)
        and lowered not in {"null", "true", "false", "yes", "no", "on", "off", "~"}
        and not _INTEGER_RE.fullmatch(text)
    ):
        return text

    return _yaml_quote(text)


def _bool_text(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value).strip().lower()
    return text or None


def _pretty_title_from_slug(slug: str) -> str:
    return slug.replace("-", " ").replace("_", " ").title()


def split_frontmatter(text: str) -> tuple[str | None, str]:
    """Return the raw frontmatter block and Markdown body."""
    if not text.startswith("---"):
        return None, text

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text

    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            frontmatter_block = "\n".join(lines[: index + 1]).strip("\n")
            body = "\n".join(lines[index + 1 :]).lstrip("\n")
            return frontmatter_block, body

    return None, text


def _parse_post(text: str) -> tuple[dict[str, object], str, str | None]:
    if not text.strip():
        return {}, "", None

    try:
        post = frontmatter.loads(text)
    except Exception as exc:  # noqa: BLE001 - surface authoring errors as text
        return {}, "", str(exc)

    return dict(post.metadata or {}), str(post.content or ""), None


def _non_empty_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _teaser(text: str) -> str | None:
    lines = _non_empty_lines(text)
    if not lines:
        return None
    return textwrap.shorten(lines[0], width=160, placeholder="…")


def _options_suffix(options: tuple[str, ...], *, current: str | None = None) -> str:
    if len(options) >= 5:
        return ""

    remaining = [option for option in options if option != current] if current else list(options)
    if not remaining:
        return ""
    return " # " + " | ".join(remaining)


def _render_text_field(name: str, value: object | None, *, comment_out_if_missing: bool = False) -> str:
    text = _string_value(value)
    if text is None:
        prefix = "# " if comment_out_if_missing else ""
        return f"{prefix}{name}:"
    return f"{name}: {_yaml_scalar(text)}"


def _render_enum_field(
    name: str,
    value: object | None,
    options: tuple[str, ...],
    *,
    comment_out_if_missing: bool = False,
) -> str:
    text = _string_value(value)
    if text is None:
        if comment_out_if_missing:
            placeholder = " | ".join(options) if len(options) < 5 else ""
            return f"# {name}: {placeholder}".rstrip()
        return f"{name}: {_options_suffix(options)}".rstrip()
    return f"{name}: {_yaml_scalar(text)}{_options_suffix(options, current=text)}"


def _render_bool_field(
    name: str,
    value: object | None,
    *,
    comment_out_if_missing: bool = True,
) -> str:
    text = _bool_text(value)
    if text is None:
        return _render_enum_field(
            name,
            None,
            _BOOL_OPTIONS,
            comment_out_if_missing=comment_out_if_missing,
        )
    return f"{name}: {text}{_options_suffix(_BOOL_OPTIONS, current=text)}"


def _commented_block(lines: list[str], *, indent: str = "") -> list[str]:
    return [f"{indent}# {line}" if line else f"{indent}#" for line in lines]


def _guess_edition_title(project_title: str, edition_slug: str) -> str:
    if edition_slug == "index":
        return project_title
    if edition_slug == _NEW_EDITION_PLACEHOLDER:
        return f"{project_title} — nowe wydanie"
    return f"{project_title} {edition_slug}".strip()


def _creator_labels(raw_creators: object) -> tuple[str, ...]:
    if not isinstance(raw_creators, list):
        return ()

    creators: list[str] = []
    for creator in raw_creators:
        if isinstance(creator, dict):
            name = _string_value(creator.get("name"))
            role = _string_value(creator.get("role"))
            if name and role:
                creators.append(f"{role}: {name}")
            elif name:
                creators.append(name)
            continue

        name = _string_value(creator)
        if name:
            creators.append(name)

    return tuple(creators)


def _primary_cover_image(meta: dict[str, object]) -> str | None:
    primary_cover = meta.get("primary_cover")
    if not isinstance(primary_cover, dict):
        return None
    return _string_value(primary_cover.get("image"))


def _render_image_list_field(name: str, raw_value: object, *, indent: str = "") -> list[str]:
    if not isinstance(raw_value, list) or not raw_value:
        return _commented_block(
            [f"{name}:", "  - image:", "    alt:", "    caption:"],
            indent=indent,
        )

    lines = [f"{indent}{name}:"]
    for item in raw_value:
        if not isinstance(item, dict):
            lines.extend(
                _commented_block(["  - image:", "    alt:", "    caption:"], indent=indent)
            )
            continue

        image = _string_value(item.get("image"))
        if image is None:
            lines.extend(
                _commented_block(["  - image:", "    alt:", "    caption:"], indent=indent)
            )
            continue

        lines.append(f"{indent}  - image: {_yaml_scalar(image)}")
        alt = _string_value(item.get("alt"))
        if alt is None:
            lines.extend(_commented_block(["alt:"], indent=f"{indent}    "))
        else:
            lines.append(f"{indent}    alt: {_yaml_scalar(alt)}")

        caption = _string_value(item.get("caption"))
        if caption is None:
            lines.extend(_commented_block(["caption:"], indent=f"{indent}    "))
        else:
            lines.append(f"{indent}    caption: {_yaml_scalar(caption)}")

    return lines


def _render_cover_field(name: str, raw_value: object, *, indent: str = "") -> list[str]:
    template_lines = [
        f"{name}:",
        "  label:",
        "  image:",
        "  alt:",
        "  artist_name:",
        "  person_slug:",
    ]
    if not isinstance(raw_value, dict) or not raw_value:
        return _commented_block(template_lines, indent=indent)

    lines = [f"{indent}{name}:"]
    for field_name in ("label", "image", "alt", "artist_name", "person_slug"):
        value = _string_value(raw_value.get(field_name))
        if value is None:
            lines.extend(_commented_block([f"{field_name}:"], indent=f"{indent}  "))
        else:
            lines.append(f"{indent}  {field_name}: {_yaml_scalar(value)}")
    return lines


def _render_cover_list_field(name: str, raw_value: object, *, indent: str = "") -> list[str]:
    template_lines = [
        f"{name}:",
        "  - id:",
        "    label:",
        "    image:",
        "    alt:",
        "    artist_name:",
        "    person_slug:",
    ]
    if not isinstance(raw_value, list) or not raw_value:
        return _commented_block(template_lines, indent=indent)

    lines = [f"{indent}{name}:"]
    for item in raw_value:
        if not isinstance(item, dict):
            lines.extend(_commented_block(template_lines[1:], indent=indent))
            continue

        item_indent = f"{indent}  "
        nested_indent = f"{indent}    "
        identifier = _string_value(item.get("id"))
        if identifier is None:
            lines.append(f"{item_indent}-")
            lines.extend(_commented_block(["id:"], indent=nested_indent))
        else:
            lines.append(f"{item_indent}- id: {_yaml_scalar(identifier)}")

        for field_name in ("label", "image", "alt", "artist_name", "person_slug"):
            value = _string_value(item.get(field_name))
            if value is None:
                lines.extend(_commented_block([f"{field_name}:"], indent=nested_indent))
            else:
                lines.append(f"{nested_indent}{field_name}: {_yaml_scalar(value)}")

    return lines


def _render_creators_field(raw_value: object, *, indent: str = "") -> list[str]:
    if not isinstance(raw_value, list) or not raw_value:
        return _commented_block(
            ["creators:", "  - role:", "    name:", "    person_slug:"],
            indent=indent,
        )

    lines = [f"{indent}creators:"]
    for item in raw_value:
        if isinstance(item, dict):
            role = _string_value(item.get("role"))
            name = _string_value(item.get("name"))
            person_slug = _string_value(item.get("person_slug"))

            if role:
                lines.append(f"{indent}  - role: {_yaml_scalar(role)}")
                if name is None:
                    lines.extend(_commented_block(["name:"], indent=f"{indent}    "))
                else:
                    lines.append(f"{indent}    name: {_yaml_scalar(name)}")
            elif name:
                lines.append(f"{indent}  - name: {_yaml_scalar(name)}")
                lines.extend(_commented_block(["role:"], indent=f"{indent}    "))
            else:
                lines.append(f"{indent}  -")
                lines.extend(_commented_block(["role:", "name:"], indent=f"{indent}    "))

            if person_slug is None:
                lines.extend(_commented_block(["person_slug:"], indent=f"{indent}    "))
            else:
                lines.append(f"{indent}    person_slug: {_yaml_scalar(person_slug)}")
            continue

        name = _string_value(item)
        if name is None:
            lines.extend(_commented_block(["  - name:"], indent=indent))
            continue
        lines.append(f"{indent}  - {_yaml_scalar(name)}")

    return lines


def _render_specs_field(name: str, raw_value: object, *, indent: str = "") -> list[str]:
    template_lines = [
        f"{name}:",
        '  "Liczba stron":',
        '  "Oprawa":',
        '  "Wymiary":',
    ]
    if not isinstance(raw_value, dict) or not raw_value:
        return _commented_block(template_lines, indent=indent)

    lines = [f"{indent}{name}:"]
    for key, value in raw_value.items():
        key_text = _string_value(key)
        value_text = _string_value(value)
        if key_text is None or value_text is None:
            continue
        lines.append(f"{indent}  {_yaml_scalar(key_text)}: {_yaml_scalar(value_text)}")

    if len(lines) == 1:
        return _commented_block(template_lines, indent=indent)
    return lines


def _render_buy_links_field(raw_value: object, *, indent: str = "") -> list[str]:
    template_lines = ["buy_links:", "  - label:", "    url:"]
    if not isinstance(raw_value, list) or not raw_value:
        return _commented_block(template_lines, indent=indent)

    lines = [f"{indent}buy_links:"]
    for item in raw_value:
        if not isinstance(item, dict):
            lines.extend(_commented_block(["  - label:", "    url:"], indent=indent))
            continue

        label = _string_value(item.get("label"))
        url = _string_value(item.get("url"))
        if label is None:
            lines.append(f"{indent}  -")
            lines.extend(_commented_block(["label:"], indent=f"{indent}    "))
        else:
            lines.append(f"{indent}  - label: {_yaml_scalar(label)}")

        if url is None:
            lines.extend(_commented_block(["url:"], indent=f"{indent}    "))
        else:
            lines.append(f"{indent}    url: {_yaml_scalar(url)}")

    return lines


def _render_products_field(raw_value: object, *, indent: str = "") -> list[str]:
    template_lines = [
        "products:",
        f"  - format: {' | '.join(_PRODUCT_FORMAT_OPTIONS)}",
        "    cover_id:",
        "    label:",
        "    isbn13:",
        "    ean2:",
        "    price:",
        "    limited: true | false",
        "    numbered_copies:",
        "    specs:",
        '      "Oprawa":',
        "    buy_links:",
        "      - label:",
        "        url:",
    ]
    if not isinstance(raw_value, list) or not raw_value:
        return _commented_block(template_lines, indent=indent)

    lines = [f"{indent}products:"]
    for item in raw_value:
        if not isinstance(item, dict):
            lines.extend(_commented_block(template_lines[1:], indent=indent))
            continue

        item_indent = f"{indent}  "
        nested_indent = f"{indent}    "
        format_name = _string_value(item.get("format"))
        if format_name is None:
            lines.append(f"{item_indent}-")
            lines.extend(
                _commented_block([f"format: {' | '.join(_PRODUCT_FORMAT_OPTIONS)}"], indent=nested_indent)
            )
        else:
            lines.append(
                f"{item_indent}- format: {_yaml_scalar(format_name)}"
                f"{_options_suffix(_PRODUCT_FORMAT_OPTIONS, current=format_name)}"
            )

        for field_name in ("cover_id", "label", "isbn13", "ean2", "price"):
            value = _string_value(item.get(field_name))
            if value is None:
                lines.extend(_commented_block([f"{field_name}:"], indent=nested_indent))
            else:
                lines.append(f"{nested_indent}{field_name}: {_yaml_scalar(value)}")

        limited = _bool_text(item.get("limited"))
        if limited is None:
            lines.extend(_commented_block(["limited: true | false"], indent=nested_indent))
        else:
            lines.append(
                f"{nested_indent}limited: {limited}"
                f"{_options_suffix(_BOOL_OPTIONS, current=limited)}"
            )

        numbered_copies = _string_value(item.get("numbered_copies"))
        if numbered_copies is None:
            lines.extend(_commented_block(["numbered_copies:"], indent=nested_indent))
        else:
            lines.append(f"{nested_indent}numbered_copies: {_yaml_scalar(numbered_copies)}")

        lines.extend(_render_specs_field("specs", item.get("specs"), indent=nested_indent))
        lines.extend(_render_buy_links_field(item.get("buy_links"), indent=nested_indent))

    return lines


def _render_project_frontmatter(slug: str, meta: dict[str, object]) -> str:
    title = _string_value(meta.get("title")) or _pretty_title_from_slug(slug)

    lines = [
        "---",
        _render_text_field("title", title),
        _render_enum_field("line", meta.get("line"), _LINE_OPTIONS),
        _render_enum_field(
            "kind",
            meta.get("kind"),
            _PROJECT_KIND_OPTIONS,
            comment_out_if_missing=True,
        ),
        _render_text_field("universe_slug", meta.get("universe_slug"), comment_out_if_missing=True),
        _render_text_field("summary", meta.get("summary")),
        _render_text_field("legacy_path", meta.get("legacy_path"), comment_out_if_missing=True),
        _render_text_field("cover_image", meta.get("cover_image")),
        _render_bool_field("draft", meta.get("draft"), comment_out_if_missing=True),
        _render_bool_field(
            "legacy_landing",
            meta.get("legacy_landing"),
            comment_out_if_missing=True,
        ),
        "---",
    ]
    return "\n".join(lines)


def _render_edition_frontmatter(
    project_slug: str,
    project_title: str,
    edition_slug: str,
    meta: dict[str, object],
) -> str:
    title = _string_value(meta.get("title")) or _guess_edition_title(project_title, edition_slug)

    lines = [
        "---",
        _render_text_field("title", title),
    ]

    release_date = _string_value(meta.get("release_date"))
    if release_date is None:
        lines.extend(_commented_block(["release_date: YYYY-MM-DD"]))
    else:
        lines.append(f"release_date: {_yaml_scalar(release_date)}")

    lines.append(_render_text_field("release", meta.get("release"), comment_out_if_missing=True))
    lines.extend(_render_cover_field("primary_cover", meta.get("primary_cover")))
    lines.extend(_render_cover_list_field("alternate_covers", meta.get("alternate_covers")))
    lines.extend(_render_image_list_field("previews", meta.get("previews")))
    lines.extend(_render_creators_field(meta.get("creators")))
    lines.extend(_render_specs_field("edition_specs", meta.get("edition_specs")))
    lines.extend(_render_products_field(meta.get("products")))
    lines.append(_render_bool_field("force_new", meta.get("force_new"), comment_out_if_missing=True))
    lines.append(
        _render_bool_field(
            "force_announcement",
            meta.get("force_announcement"),
            comment_out_if_missing=True,
        )
    )
    lines.append(
        _render_text_field("presale_url", meta.get("presale_url"), comment_out_if_missing=True)
    )
    lines.append(_render_bool_field("featured", meta.get("featured"), comment_out_if_missing=True))
    lines.append(
        _render_bool_field("standalone", meta.get("standalone"), comment_out_if_missing=True)
    )
    lines.append(_render_text_field("subseries", meta.get("subseries"), comment_out_if_missing=True))
    lines.append(
        _render_text_field("issue_number", meta.get("issue_number"), comment_out_if_missing=True)
    )
    lines.append(
        _render_text_field("legacy_anchor", meta.get("legacy_anchor"), comment_out_if_missing=True)
    )
    lines.append(
        _render_text_field("legacy_path", meta.get("legacy_path"), comment_out_if_missing=True)
    )
    lines.append("---")
    return "\n".join(lines)


def _collect_project_statuses(
    *,
    file_exists: bool,
    text: str,
    frontmatter_block: str | None,
    body: str,
    meta: dict[str, object],
    parse_error: str | None,
) -> tuple[str, ...]:
    statuses: list[str] = []

    if not file_exists:
        statuses.append("missing-project-file")
    elif not text.strip():
        statuses.append("empty-file")

    if frontmatter_block is None:
        statuses.append("missing-frontmatter")
    if parse_error:
        statuses.append("invalid-frontmatter")

    body_lines = _non_empty_lines(body)
    if not body_lines:
        statuses.append("missing-body")
    elif len(body_lines) <= 2:
        statuses.append("short-body")

    if not _string_value(meta.get("summary")):
        statuses.append("missing-summary")

    return tuple(sorted(set(statuses), key=lambda status: _PROJECT_STATUS_ORDER[status]))


def _collect_edition_statuses(
    *,
    text: str,
    frontmatter_block: str | None,
    body: str,
    meta: dict[str, object],
    parse_error: str | None,
) -> tuple[str, ...]:
    statuses: list[str] = []

    if not text.strip():
        statuses.append("empty-file")
    if frontmatter_block is None:
        statuses.append("missing-frontmatter")
    if parse_error:
        statuses.append("invalid-frontmatter")
    if not _string_value(meta.get("title")):
        statuses.append("missing-title")

    body_lines = _non_empty_lines(body)
    if not body_lines:
        statuses.append("missing-body")
    elif len(body_lines) <= 2:
        statuses.append("short-body")

    return tuple(sorted(set(statuses), key=lambda status: _EDITION_STATUS_ORDER[status]))


def _collect_editions(
    project_dir: Path,
    *,
    project_slug: str,
    project_title: str,
) -> tuple[EditionEntry, ...]:
    editions_dir = project_dir / "editions"
    if not editions_dir.exists():
        return ()

    entries: list[EditionEntry] = []
    for edition_path in sorted(editions_dir.glob("*.md")):
        text = edition_path.read_text(encoding="utf-8")
        frontmatter_block, raw_body = split_frontmatter(text)
        meta, parsed_body, parse_error = _parse_post(text)
        body = raw_body if frontmatter_block is not None else parsed_body or raw_body
        slug = edition_path.stem

        entries.append(
            EditionEntry(
                project_slug=project_slug,
                slug=slug,
                path=edition_path,
                frontmatter_block=_render_edition_frontmatter(
                    project_slug,
                    project_title,
                    slug,
                    meta,
                ).strip("\n"),
                body=body.strip("\n"),
                statuses=_collect_edition_statuses(
                    text=text,
                    frontmatter_block=frontmatter_block,
                    body=body,
                    meta=meta,
                    parse_error=parse_error,
                ),
                title=_string_value(meta.get("title")) or _guess_edition_title(project_title, slug),
                release_label=_string_value(meta.get("release_date")) or _string_value(meta.get("release")),
                creators=_creator_labels(meta.get("creators")),
                cover_image=_primary_cover_image(meta),
                teaser=_teaser(body),
                parse_error=parse_error,
            )
        )

    return tuple(entries)


def _build_new_edition_template(project_slug: str, project_dir: Path, project_title: str) -> EditionEntry:
    slug = _NEW_EDITION_PLACEHOLDER
    return EditionEntry(
        project_slug=project_slug,
        slug=slug,
        path=project_dir / "editions" / f"{slug}.md",
        frontmatter_block=_render_edition_frontmatter(project_slug, project_title, slug, {}).strip("\n"),
        body="",
        statuses=(),
        title=_guess_edition_title(project_title, slug),
        release_label=None,
        creators=(),
        cover_image=None,
        teaser=None,
        parse_error=None,
        is_template=True,
    )


def collect_project_entries(root: Path, *, include_complete: bool = False) -> list[ProjectEntry]:
    """Collect project pages and edition pages that should appear in the workbook."""
    projects_dir = root / "content" / "projects"
    if not projects_dir.exists():
        return []

    entries: list[ProjectEntry] = []
    for project_dir in sorted(projects_dir.glob("*/")):
        slug = project_dir.name
        project_path = project_dir / "project.md"
        file_exists = project_path.exists()
        text = project_path.read_text(encoding="utf-8") if file_exists else ""
        frontmatter_block, raw_body = split_frontmatter(text)
        meta, parsed_body, parse_error = _parse_post(text)
        body = raw_body if frontmatter_block is not None else parsed_body or raw_body
        title = _string_value(meta.get("title")) or _pretty_title_from_slug(slug)
        editions = _collect_editions(project_dir, project_slug=slug, project_title=title)
        editable_editions = (
            editions if include_complete else tuple(edition for edition in editions if edition.statuses)
        )
        statuses = _collect_project_statuses(
            file_exists=file_exists,
            text=text,
            frontmatter_block=frontmatter_block,
            body=body,
            meta=meta,
            parse_error=parse_error,
        )

        if not include_complete and not statuses and not editable_editions:
            continue

        entries.append(
            ProjectEntry(
                slug=slug,
                path=project_path,
                frontmatter_block=_render_project_frontmatter(slug, meta).strip("\n"),
                body=body.strip("\n"),
                statuses=statuses,
                title=title,
                line=_string_value(meta.get("line")),
                summary=_string_value(meta.get("summary")),
                cover_image=_string_value(meta.get("cover_image")),
                editions=editions,
                editable_editions=editable_editions,
                new_edition_template=_build_new_edition_template(slug, project_dir, title),
                parse_error=parse_error,
            )
        )

    entries.sort(
        key=lambda entry: (
            min((_PROJECT_STATUS_ORDER[status] for status in entry.statuses), default=99),
            entry.slug,
        )
    )
    return entries


def _format_statuses(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "gotowe"
    return ", ".join(_STATUS_LABELS[status] for status in statuses)


def _render_edition_notes(lines: list[str], editions: tuple[EditionEntry, ...]) -> None:
    if not editions:
        lines.append("Brak plików wydań w tym projekcie.")
        return

    for edition in editions:
        lines.append(f"- `{edition.filename}` — {edition.title}")
        if edition.statuses:
            lines.append(f"  - status: {_format_statuses(edition.statuses)}")
        if edition.release_label:
            lines.append(f"  - premiera: {edition.release_label}")
        if edition.creators:
            lines.append(f"  - twórcy: {', '.join(edition.creators)}")
        if edition.cover_image:
            lines.append(f"  - okładka: {edition.cover_image}")
        if edition.teaser:
            lines.append(f"  - zajawka: {edition.teaser}")
        if edition.parse_error:
            lines.append(f"  - uwaga: błąd frontmatter ({edition.parse_error})")


def _render_edition_editor(lines: list[str], edition: EditionEntry, *, root: Path) -> None:
    relative_path = edition.path.relative_to(root)
    lines.extend(
        [
            f"#### {edition.filename}",
            f"- plik: `{relative_path}`",
            f"- status: {_format_statuses(edition.statuses)}",
            f"- tytuł: {edition.title}",
            f"- premiera: {edition.release_label or '—'}",
            f"- okładka: {edition.cover_image or '—'}",
            f"- twórcy: {', '.join(edition.creators) if edition.creators else '—'}",
        ]
    )
    if edition.parse_error:
        lines.append(f"- uwaga: obecny frontmatter nie parsuje się poprawnie ({edition.parse_error})")

    lines.extend(
        [
            "",
            "##### Edytowalny frontmatter wydania",
            f"<!-- EDITION FRONTMATTER START: {edition.workbook_id} -->",
            edition.frontmatter_block,
            f"<!-- EDITION FRONTMATTER END: {edition.workbook_id} -->",
            "",
            "##### Edytowalny opis wydania",
            "Wskazówki: 1–3 krótkie akapity. Najpierw haczyk fabularny, potem najważniejsze informacje o wydaniu, na końcu powód, żeby kliknąć dalej albo kupić.",
            f"<!-- EDITION BODY START: {edition.workbook_id} -->",
            edition.body,
            f"<!-- EDITION BODY END: {edition.workbook_id} -->",
            "",
        ]
    )


def _render_new_edition_template(lines: list[str], template: EditionEntry) -> None:
    lines.extend(
        [
            "### Szablon nowego wydania",
            "Skopiuj oba bloki poniżej, zmień identyfikator `__new_edition__` na docelowy slug pliku (np. `projekt/02` albo `projekt/index`), a dopiero potem uzupełnij treść.",
            f"<!-- EDITION FRONTMATTER START: {template.workbook_id} -->",
            template.frontmatter_block,
            f"<!-- EDITION FRONTMATTER END: {template.workbook_id} -->",
            "",
            f"<!-- EDITION BODY START: {template.workbook_id} -->",
            template.body,
            f"<!-- EDITION BODY END: {template.workbook_id} -->",
            "",
        ]
    )


def render_workbook(entries: list[ProjectEntry], *, root: Path, include_complete: bool) -> str:
    """Render a single editable workbook for project and edition pages."""
    project_counts = Counter(status for entry in entries for status in entry.statuses)
    edition_counts = Counter(
        status for entry in entries for edition in entry.editable_editions for status in edition.statuses
    )
    edition_sections = sum(len(entry.editable_editions) for entry in entries)

    lines = [
        "<!-- markdownlint-disable-file -->",
        "",
        "# Project page workbook",
        "",
        "Jeden plik do szybkiego uzupełniania `content/projects/*/project.md` i `content/projects/*/editions/*.md`.",
        "Edytuj tylko bloki między markerami `FRONTMATTER`, `BODY`, `EDITION FRONTMATTER` i `EDITION BODY`, a potem zaimportuj je z powrotem.",
        "",
        "## Jak używać",
        "1. `uv run diablaq-project-workbook export` — wygeneruj skoroszyt.",
        "2. Uzupełnij treść między markerami dla wybranych projektów i wydań.",
        "3. Jeśli dodajesz nowe wydanie, skopiuj blok `__new_edition__`, zmień identyfikator na `projekt/slug-wydania`, a potem uzupełnij treść.",
        "4. `uv run diablaq-project-workbook import` — zapisz zmiany z powrotem do `project.md` i `editions/*.md`.",
        "5. `uv run diablaq-build` — sprawdź efekt w `dist/`.",
        "",
        "## Zakres",
        f"- tryb eksportu: {'wszystkie projekty i wydania' if include_complete else 'tylko sekcje wymagające pracy'}",
        f"- liczba projektów w skoroszycie: {len(entries)}",
        f"- liczba sekcji wydań w skoroszycie: {edition_sections}",
        f"- puste pliki `project.md`: {project_counts['empty-file']}",
        f"- puste pliki wydań: {edition_counts['empty-file']}",
        f"- brak opisów projektów: {project_counts['missing-body']}",
        f"- brak opisów wydań: {edition_counts['missing-body']}",
        f"- krótkie opisy projektów: {project_counts['short-body']}",
        f"- krótkie opisy wydań: {edition_counts['short-body']}",
        "",
    ]

    if not entries:
        lines.extend(
            [
                "Nie znaleziono projektów ani wydań do uzupełnienia.",
                "Użyj `uv run diablaq-project-workbook export --all`, jeśli chcesz zobaczyć cały katalog.",
                "",
            ]
        )
        return "\n".join(lines)

    for entry in entries:
        relative_path = entry.path.relative_to(root)
        lines.extend(
            [
                f"## {entry.slug}",
                f"- plik projektu: `{relative_path}`",
                f"- status projektu: {_format_statuses(entry.statuses)}",
                f"- tytuł: {entry.title}",
                f"- linia: {entry.line or '—'}",
                f"- summary: {entry.summary or '—'}",
                f"- okładka: {entry.cover_image or '—'}",
            ]
        )
        if entry.parse_error:
            lines.append(f"- uwaga: obecny frontmatter nie parsuje się poprawnie ({entry.parse_error})")

        lines.extend(["", "### Materiały pomocnicze z wydań"])
        _render_edition_notes(lines, entry.editions)

        lines.extend(
            [
                "",
                "### Edytowalny frontmatter projektu",
                f"<!-- FRONTMATTER START: {entry.slug} -->",
                entry.frontmatter_block,
                f"<!-- FRONTMATTER END: {entry.slug} -->",
                "",
                "### Edytowalny opis projektu",
                "Wskazówki: 2–4 krótkie akapity. Najpierw 'o czym to jest', potem 'dla kogo i co wyróżnia serię', na końcu 'co znajdzie czytelnik na tej stronie'.",
                f"<!-- BODY START: {entry.slug} -->",
                entry.body,
                f"<!-- BODY END: {entry.slug} -->",
                "",
                "### Edytowalne wydania",
            ]
        )

        if entry.editable_editions:
            for edition in entry.editable_editions:
                _render_edition_editor(lines, edition, root=root)
        else:
            lines.extend(["Brak wydań wymagających pracy.", ""])

        _render_new_edition_template(lines, entry.new_edition_template)
        lines.extend(["---", ""])

    return "\n".join(lines).rstrip() + "\n"


def export_workbook(root: Path, workbook_path: Path, *, include_complete: bool = False) -> list[ProjectEntry]:
    """Write a workbook file and return the collected entries."""
    entries = collect_project_entries(root, include_complete=include_complete)
    workbook_path.write_text(
        render_workbook(entries, root=root, include_complete=include_complete),
        encoding="utf-8",
    )
    return entries


def _extract_blocks(
    workbook_text: str,
    *,
    pattern: re.Pattern[str],
    label: str,
    key_builder,
) -> dict[str, str]:
    blocks: dict[str, str] = {}
    for match in pattern.finditer(workbook_text):
        identifier = key_builder(match)
        if identifier in blocks:
            raise ValueError(f"Duplikat sekcji {label} dla {identifier}.")
        blocks[identifier] = match.group("content").strip("\n")
    return blocks


def _assert_matching_block_sets(
    frontmatters: dict[str, str],
    bodies: dict[str, str],
    *,
    prefix: str,
) -> None:
    if set(frontmatters) == set(bodies):
        return

    label_prefix = f"{prefix} " if prefix else ""
    missing_frontmatter = sorted(set(bodies) - set(frontmatters))
    missing_body = sorted(set(frontmatters) - set(bodies))
    problems: list[str] = []
    if missing_frontmatter:
        problems.append(
            f"brak {label_prefix}FRONTMATTER dla: {', '.join(missing_frontmatter)}"
        )
    if missing_body:
        problems.append(f"brak {label_prefix}BODY dla: {', '.join(missing_body)}")
    raise ValueError("Niespójny skoroszyt: " + "; ".join(problems))


def _validate_frontmatter_block(identifier: str, block: str, *, subject_label: str) -> str:
    block = block.strip("\n")
    frontmatter_block, _ = split_frontmatter(block + "\n")
    if frontmatter_block is None:
        raise ValueError(
            f"{subject_label} {identifier} nie ma poprawnego bloku frontmatter między markerami."
        )

    try:
        frontmatter.loads(block + "\n")
    except Exception as exc:  # noqa: BLE001 - show exact YAML issue to authors
        raise ValueError(f"{subject_label} {identifier} ma nieprawidłowy frontmatter: {exc}") from exc
    return block


def _render_markdown_file(frontmatter_block: str, body: str) -> str:
    if body.strip():
        return f"{frontmatter_block.rstrip()}\n\n{body.strip()}\n"
    return f"{frontmatter_block.rstrip()}\n"


def apply_workbook(root: Path, workbook_path: Path) -> list[Path]:
    """Apply workbook changes back into per-project and per-edition Markdown files."""
    workbook_text = workbook_path.read_text(encoding="utf-8")
    project_frontmatters = _extract_blocks(
        workbook_text,
        pattern=_FRONTMATTER_BLOCK_RE,
        label="FRONTMATTER",
        key_builder=lambda match: match.group("slug"),
    )
    project_bodies = _extract_blocks(
        workbook_text,
        pattern=_BODY_BLOCK_RE,
        label="BODY",
        key_builder=lambda match: match.group("slug"),
    )
    edition_frontmatters = _extract_blocks(
        workbook_text,
        pattern=_EDITION_FRONTMATTER_BLOCK_RE,
        label="EDITION FRONTMATTER",
        key_builder=lambda match: f"{match.group('project')}/{match.group('edition')}",
    )
    edition_bodies = _extract_blocks(
        workbook_text,
        pattern=_EDITION_BODY_BLOCK_RE,
        label="EDITION BODY",
        key_builder=lambda match: f"{match.group('project')}/{match.group('edition')}",
    )

    _assert_matching_block_sets(project_frontmatters, project_bodies, prefix="")
    _assert_matching_block_sets(edition_frontmatters, edition_bodies, prefix="EDITION")

    baseline_entries = collect_project_entries(root, include_complete=True)
    baseline_projects = {entry.slug: entry for entry in baseline_entries}
    baseline_editions = {
        edition.workbook_id: edition
        for entry in baseline_entries
        for edition in entry.editions
    }
    edition_templates = {
        entry.new_edition_template.workbook_id: entry.new_edition_template for entry in baseline_entries
    }

    updates: list[tuple[Path, str]] = []
    for slug, frontmatter_block in project_frontmatters.items():
        validated_frontmatter = _validate_frontmatter_block(slug, frontmatter_block, subject_label="Projekt")
        body = project_bodies[slug].strip("\n")
        baseline = baseline_projects.get(slug)
        if baseline is not None and (
            validated_frontmatter == baseline.frontmatter_block and body == baseline.body.strip("\n")
        ):
            continue

        project_path = root / "content" / "projects" / slug / "project.md"
        if not project_path.parent.exists():
            raise ValueError(f"Projekt {slug} nie istnieje w katalogu content/projects/.")
        updates.append((project_path, _render_markdown_file(validated_frontmatter, body)))

    for identifier, frontmatter_block in edition_frontmatters.items():
        validated_frontmatter = _validate_frontmatter_block(
            identifier,
            frontmatter_block,
            subject_label="Wydanie",
        )
        body = edition_bodies[identifier].strip("\n")
        template = edition_templates.get(identifier)
        if template is not None:
            if validated_frontmatter == template.frontmatter_block and body == template.body.strip("\n"):
                continue
            raise ValueError(
                f"Szablon nowego wydania {identifier} został zmieniony, ale nadal ma identyfikator szablonu. "
                "Skopiuj blok i zmień marker na docelowy slug wydania."
            )

        baseline = baseline_editions.get(identifier)
        if baseline is not None and (
            validated_frontmatter == baseline.frontmatter_block and body == baseline.body.strip("\n")
        ):
            continue

        project_slug, edition_slug = identifier.split("/", maxsplit=1)
        project_dir = root / "content" / "projects" / project_slug
        if not project_dir.exists():
            raise ValueError(f"Projekt {project_slug} nie istnieje w katalogu content/projects/.")
        edition_path = project_dir / "editions" / f"{edition_slug}.md"
        updates.append((edition_path, _render_markdown_file(validated_frontmatter, body)))

    updated_paths: list[Path] = []
    for target_path, content in updates:
        current_content = target_path.read_text(encoding="utf-8") if target_path.exists() else None
        if current_content == content:
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        updated_paths.append(target_path)

    return updated_paths


def main() -> None:
    parser = argparse.ArgumentParser(prog="diablaq-project-workbook")
    subparsers = parser.add_subparsers(dest="command", required=True)

    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Katalog repo (domyślnie: bieżący).",
    )

    export_parser = subparsers.add_parser(
        "export",
        parents=[common_parser],
        help="Wygeneruj skoroszyt do edycji.",
    )
    export_parser.add_argument(
        "--workbook",
        type=Path,
        default=None,
        help=f"Ścieżka wynikowego skoroszytu (domyślnie: <root>/{DEFAULT_WORKBOOK_NAME}).",
    )
    export_parser.add_argument(
        "--all",
        action="store_true",
        help="Uwzględnij także projekty i wydania, które są już kompletne.",
    )

    import_parser = subparsers.add_parser(
        "import",
        parents=[common_parser],
        help="Zapisz skoroszyt z powrotem do plików treści.",
    )
    import_parser.add_argument(
        "--workbook",
        type=Path,
        default=None,
        help=f"Ścieżka skoroszytu (domyślnie: <root>/{DEFAULT_WORKBOOK_NAME}).",
    )

    args = parser.parse_args()
    root = args.root.resolve()
    workbook_path = (args.workbook or (root / DEFAULT_WORKBOOK_NAME)).resolve()

    try:
        if args.command == "export":
            entries = export_workbook(root, workbook_path, include_complete=args.all)
            print(f"Zapisano skoroszyt: {workbook_path} ({len(entries)} projektów).")
            return

        updated_paths = apply_workbook(root, workbook_path)
        print(f"Zaktualizowano {len(updated_paths)} plików treści.")
        for path in updated_paths:
            print(f"- {path.relative_to(root)}")
    except ValueError as exc:
        print(f"Błąd skoroszytu: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
