"""Batch-edit project page copy through a single workbook file."""

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
_STATUS_ORDER = {
    "missing-project-file": 0,
    "empty-file": 1,
    "missing-frontmatter": 2,
    "invalid-frontmatter": 3,
    "missing-body": 4,
    "missing-summary": 5,
    "short-body": 6,
}
_STATUS_LABELS = {
    "missing-project-file": "brak pliku project.md",
    "empty-file": "pusty plik",
    "missing-frontmatter": "brak frontmatter",
    "invalid-frontmatter": "zepsuty frontmatter",
    "missing-body": "brak opisu",
    "missing-summary": "brak summary",
    "short-body": "krótki opis",
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


@dataclass(frozen=True)
class EditionNote:
    filename: str
    title: str
    release_label: str | None
    creators: tuple[str, ...]
    teaser: str | None
    parse_error: str | None
    is_empty: bool


@dataclass(frozen=True)
class ProjectEntry:
    slug: str
    path: Path
    frontmatter_block: str
    body: str
    statuses: tuple[str, ...]
    title: str | None
    line: str | None
    summary: str | None
    cover_image: str | None
    editions: tuple[EditionNote, ...]
    parse_error: str | None


def _string_value(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _pretty_title_from_slug(slug: str) -> str:
    return slug.replace("-", " ").title()


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


def _build_frontmatter_template(slug: str, meta: dict[str, object]) -> str:
    title = _string_value(meta.get("title")) or _pretty_title_from_slug(slug)
    line = _string_value(meta.get("line"))
    summary = _string_value(meta.get("summary"))
    cover_image = _string_value(meta.get("cover_image"))

    lines = [
        "---",
        f"title: {_yaml_quote(title)}",
        f"line: {_yaml_quote(line)}" if line else "line:  # diablaq | dobre-licho | mecenat | studio",
        f"summary: {_yaml_quote(summary)}" if summary else "summary:",
        f"cover_image: {_yaml_quote(cover_image)}" if cover_image else "cover_image:",
        "---",
    ]
    return "\n".join(lines)


def _collect_statuses(
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

    unique_statuses = sorted(set(statuses), key=lambda status: _STATUS_ORDER[status])
    return tuple(unique_statuses)


def _collect_editions(project_dir: Path) -> tuple[EditionNote, ...]:
    editions_dir = project_dir / "editions"
    if not editions_dir.exists():
        return ()

    notes: list[EditionNote] = []
    for edition_path in sorted(editions_dir.glob("*.md")):
        text = edition_path.read_text(encoding="utf-8")
        meta, body, parse_error = _parse_post(text)
        creators: list[str] = []
        raw_creators = meta.get("creators")
        if isinstance(raw_creators, list):
            for creator in raw_creators:
                if not isinstance(creator, dict):
                    continue
                name = _string_value(creator.get("name"))
                role = _string_value(creator.get("role"))
                if name and role:
                    creators.append(f"{role}: {name}")
                elif name:
                    creators.append(name)

        release_label = _string_value(meta.get("release_date")) or _string_value(meta.get("release"))
        notes.append(
            EditionNote(
                filename=edition_path.name,
                title=_string_value(meta.get("title")) or edition_path.stem,
                release_label=release_label,
                creators=tuple(creators),
                teaser=_teaser(body),
                parse_error=parse_error,
                is_empty=not text.strip(),
            )
        )

    return tuple(notes)


def collect_project_entries(root: Path, *, include_complete: bool = False) -> list[ProjectEntry]:
    """Collect project pages that should appear in the workbook."""
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
        statuses = _collect_statuses(
            file_exists=file_exists,
            text=text,
            frontmatter_block=frontmatter_block,
            body=body,
            meta=meta,
            parse_error=parse_error,
        )
        if not include_complete and not statuses:
            continue

        entries.append(
            ProjectEntry(
                slug=slug,
                path=project_path,
                frontmatter_block=(frontmatter_block or _build_frontmatter_template(slug, meta)).strip(
                    "\n"
                ),
                body=body.strip("\n"),
                statuses=statuses,
                title=_string_value(meta.get("title")) or _pretty_title_from_slug(slug),
                line=_string_value(meta.get("line")),
                summary=_string_value(meta.get("summary")),
                cover_image=_string_value(meta.get("cover_image")),
                editions=_collect_editions(project_dir),
                parse_error=parse_error,
            )
        )

    entries.sort(
        key=lambda entry: (
            min((_STATUS_ORDER[status] for status in entry.statuses), default=99),
            entry.slug,
        )
    )
    return entries


def _format_statuses(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "gotowe"
    return ", ".join(_STATUS_LABELS[status] for status in statuses)


def _render_edition_notes(lines: list[str], editions: tuple[EditionNote, ...]) -> None:
    if not editions:
        lines.append("Brak plików wydań w tym projekcie.")
        return

    for edition in editions:
        lines.append(f"- `{edition.filename}` — {edition.title}")
        if edition.release_label:
            lines.append(f"  - premiera: {edition.release_label}")
        if edition.creators:
            lines.append(f"  - twórcy: {', '.join(edition.creators)}")
        if edition.teaser:
            lines.append(f"  - zajawka: {edition.teaser}")
        if edition.is_empty:
            lines.append("  - stan: pusty plik")
        if edition.parse_error:
            lines.append(f"  - uwaga: błąd frontmatter ({edition.parse_error})")


def render_workbook(entries: list[ProjectEntry], *, root: Path, include_complete: bool) -> str:
    """Render a single editable workbook for project pages."""
    counts = Counter(status for entry in entries for status in entry.statuses)

    lines = [
        "# Project page workbook",
        "",
        "Jeden plik do szybkiego uzupełniania opisów `content/projects/*/project.md`.",
        "Edytuj tylko bloki między markerami `FRONTMATTER` i `BODY`, a potem zaimportuj je z powrotem.",
        "",
        "## Jak używać",
        "1. `uv run diablaq-project-workbook export` — wygeneruj skoroszyt.",
        "2. Uzupełnij treść między markerami dla wybranych projektów.",
        "3. `uv run diablaq-project-workbook import` — zapisz zmiany z powrotem do `project.md`.",
        "4. `uv run diablaq-build` — sprawdź efekt w `dist/`.",
        "",
        "## Zakres",
        f"- tryb eksportu: {'wszystkie projekty' if include_complete else 'tylko projekty wymagające pracy'}",
        f"- liczba projektów w skoroszycie: {len(entries)}",
        f"- puste pliki: {counts['empty-file']}",
        f"- brak pliku project.md: {counts['missing-project-file']}",
        f"- brak opisu: {counts['missing-body']}",
        f"- krótkie opisy: {counts['short-body']}",
        f"- brak summary: {counts['missing-summary']}",
        "",
    ]

    if not entries:
        lines.extend(
            [
                "Nie znaleziono projektów do uzupełnienia.",
                "Użyj `uv run diablaq-project-workbook export --all`, jeśli chcesz zobaczyć wszystkie strony projektów.",
                "",
            ]
        )
        return "\n".join(lines)

    for entry in entries:
        relative_path = entry.path.relative_to(root)
        lines.extend(
            [
                f"## {entry.slug}",
                f"- plik: `{relative_path}`",
                f"- status: {_format_statuses(entry.statuses)}",
                f"- tytuł: {entry.title or '—'}",
                f"- linia: {entry.line or '—'}",
                f"- summary: {entry.summary or '—'}",
                f"- okładka: {entry.cover_image or '—'}",
            ]
        )
        if entry.parse_error:
            lines.append(f"- uwaga: obecny frontmatter nie parsuje się poprawnie ({entry.parse_error})")

        lines.extend(
            [
                "",
                "### Materiały pomocnicze z wydań",
            ]
        )
        _render_edition_notes(lines, entry.editions)

        lines.extend(
            [
                "",
                "### Edytowalny frontmatter",
                f"<!-- FRONTMATTER START: {entry.slug} -->",
                entry.frontmatter_block,
                f"<!-- FRONTMATTER END: {entry.slug} -->",
                "",
                "### Edytowalny opis",
                "Wskazówki: 2–4 krótkie akapity. Najpierw 'o czym to jest', potem 'dla kogo i co wyróżnia serię', na końcu 'co znajdzie czytelnik na tej stronie'.",
                f"<!-- BODY START: {entry.slug} -->",
                entry.body,
                f"<!-- BODY END: {entry.slug} -->",
                "",
                "---",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def export_workbook(root: Path, workbook_path: Path, *, include_complete: bool = False) -> list[ProjectEntry]:
    """Write a workbook file and return the collected entries."""
    entries = collect_project_entries(root, include_complete=include_complete)
    workbook_path.write_text(
        render_workbook(entries, root=root, include_complete=include_complete),
        encoding="utf-8",
    )
    return entries


def _extract_blocks(workbook_text: str, *, pattern: re.Pattern[str], label: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    for match in pattern.finditer(workbook_text):
        slug = match.group("slug")
        if slug in blocks:
            raise ValueError(f"Duplikat sekcji {label} dla projektu {slug}.")
        blocks[slug] = match.group("content").strip("\n")
    return blocks


def _validate_frontmatter_block(slug: str, block: str) -> str:
    block = block.strip("\n")
    frontmatter_block, _ = split_frontmatter(block + "\n")
    if frontmatter_block is None:
        raise ValueError(f"Projekt {slug} nie ma poprawnego bloku frontmatter między markerami.")

    try:
        frontmatter.loads(block + "\n")
    except Exception as exc:  # noqa: BLE001 - show exact YAML issue to authors
        raise ValueError(f"Projekt {slug} ma nieprawidłowy frontmatter: {exc}") from exc
    return block


def _render_project_file(frontmatter_block: str, body: str) -> str:
    if body.strip():
        return f"{frontmatter_block.rstrip()}\n\n{body.strip()}\n"
    return f"{frontmatter_block.rstrip()}\n"


def apply_workbook(root: Path, workbook_path: Path) -> list[Path]:
    """Apply workbook changes back into per-project project.md files."""
    workbook_text = workbook_path.read_text(encoding="utf-8")
    frontmatters = _extract_blocks(
        workbook_text,
        pattern=_FRONTMATTER_BLOCK_RE,
        label="FRONTMATTER",
    )
    bodies = _extract_blocks(workbook_text, pattern=_BODY_BLOCK_RE, label="BODY")

    if set(frontmatters) != set(bodies):
        missing_frontmatter = sorted(set(bodies) - set(frontmatters))
        missing_body = sorted(set(frontmatters) - set(bodies))
        problems: list[str] = []
        if missing_frontmatter:
            problems.append(f"brak FRONTMATTER dla: {', '.join(missing_frontmatter)}")
        if missing_body:
            problems.append(f"brak BODY dla: {', '.join(missing_body)}")
        raise ValueError("Niespójny skoroszyt: " + "; ".join(problems))

    baseline_entries = {
        entry.slug: entry for entry in collect_project_entries(root, include_complete=True)
    }

    updates: list[tuple[Path, str]] = []
    for slug, frontmatter_block in frontmatters.items():
        validated_frontmatter = _validate_frontmatter_block(slug, frontmatter_block)
        body = bodies[slug].strip("\n")
        baseline = baseline_entries.get(slug)
        if baseline is not None and (
            validated_frontmatter == baseline.frontmatter_block and body == baseline.body.strip("\n")
        ):
            continue

        project_path = root / "content" / "projects" / slug / "project.md"
        if not project_path.parent.exists():
            raise ValueError(f"Projekt {slug} nie istnieje w katalogu content/projects/.")
        updates.append((project_path, _render_project_file(validated_frontmatter, body)))

    updated_paths: list[Path] = []
    for project_path, content in updates:
        current_content = project_path.read_text(encoding="utf-8") if project_path.exists() else None
        if current_content == content:
            continue
        project_path.parent.mkdir(parents=True, exist_ok=True)
        project_path.write_text(content, encoding="utf-8")
        updated_paths.append(project_path)

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
        help="Uwzględnij także projekty, które już mają kompletne opisy.",
    )

    import_parser = subparsers.add_parser(
        "import",
        parents=[common_parser],
        help="Zapisz skoroszyt z powrotem do project.md.",
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
            print(
                f"Zapisano skoroszyt: {workbook_path} ({len(entries)} projektów)."
            )
            return

        updated_paths = apply_workbook(root, workbook_path)
        print(f"Zaktualizowano {len(updated_paths)} plików project.md.")
        for path in updated_paths:
            print(f"- {path.relative_to(root)}")
    except ValueError as exc:
        print(f"Błąd skoroszytu: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
