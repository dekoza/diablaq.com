"""Helpers for turning YAML/frontmatter parser exceptions into actionable messages."""

from __future__ import annotations


def format_frontmatter_error(
    exc: Exception,
    *,
    source_text: str,
    parent_label: str | None = None,
    parent_start_line: int | None = None,
) -> str:
    """Return a concise, line-aware description of a frontmatter parsing error."""
    problem = _clean_text(getattr(exc, "problem", None))
    context = _clean_text(getattr(exc, "context", None))
    problem_mark = _get_mark(exc, "problem_mark")
    context_mark = _get_mark(exc, "context_mark")

    if problem_mark is None and context_mark is None:
        return str(exc)

    lines: list[str] = []
    if context and context_mark is not None and not _same_mark(context_mark, problem_mark):
        location = _format_location(
            context_mark,
            parent_label=parent_label,
            parent_start_line=parent_start_line,
        )
        lines.append(f"Kontekst parsera: {context} ({location}).")

    if problem:
        if problem_mark is not None:
            location = _format_location(
                problem_mark,
                parent_label=parent_label,
                parent_start_line=parent_start_line,
            )
            lines.append(f"Problem YAML: {problem} ({location}).")
        else:
            lines.append(f"Problem YAML: {problem}.")
    else:
        summary = str(exc).splitlines()[0] if str(exc).splitlines() else exc.__class__.__name__
        lines.append(f"Problem YAML: {summary}.")

    excerpt = _format_excerpt(source_text, context_mark=context_mark, problem_mark=problem_mark)
    if excerpt:
        lines.append("Fragment:")
        lines.append(excerpt)

    return "\n".join(lines)


def _clean_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _get_mark(exc: Exception, attr_name: str) -> object | None:
    mark = getattr(exc, attr_name, None)
    if mark is None:
        return None
    if not isinstance(getattr(mark, "line", None), int):
        return None
    if not isinstance(getattr(mark, "column", None), int):
        return None
    return mark


def _same_mark(left: object | None, right: object | None) -> bool:
    if left is None or right is None:
        return False
    return (left.line, left.column) == (right.line, right.column)


def _format_location(
    mark: object,
    *,
    parent_label: str | None,
    parent_start_line: int | None,
) -> str:
    parts = [f"linia {mark.line + 1}, kolumna {mark.column + 1}"]
    if parent_label is not None and parent_start_line is not None:
        parts.append(f"{parent_label} linia {parent_start_line + mark.line}")
    return "; ".join(parts)


def _format_excerpt(
    source_text: str,
    *,
    context_mark: object | None,
    problem_mark: object | None,
) -> str:
    if not source_text:
        return ""

    source_lines = source_text.splitlines()
    if not source_lines:
        return ""

    marked_lines = sorted(
        {
            mark.line + 1
            for mark in (context_mark, problem_mark)
            if mark is not None and 0 <= mark.line < len(source_lines)
        }
    )
    if not marked_lines:
        return ""

    start_line = max(1, marked_lines[0] - 1)
    end_line = min(len(source_lines), marked_lines[-1] + 1)
    width = len(str(end_line))
    pointers_by_line: dict[int, list[str]] = {}

    if context_mark is not None and 0 <= context_mark.line < len(source_lines):
        pointers_by_line.setdefault(context_mark.line + 1, []).append(
            _format_pointer(
                source_lines[context_mark.line],
                context_mark.column,
                width,
                label="kontekst parsera",
            )
        )
    if problem_mark is not None and 0 <= problem_mark.line < len(source_lines):
        pointers_by_line.setdefault(problem_mark.line + 1, []).append(
            _format_pointer(
                source_lines[problem_mark.line],
                problem_mark.column,
                width,
                label="problem YAML",
            )
        )

    rendered: list[str] = []
    for line_number in range(start_line, end_line + 1):
        rendered.append(f"{line_number:>{width}} | {source_lines[line_number - 1]}")
        rendered.extend(pointers_by_line.get(line_number, []))

    return "\n".join(rendered)


def _format_pointer(line_text: str, column_zero_based: int, width: int, *, label: str) -> str:
    pointer_column = min(max(column_zero_based + 1, 1), len(line_text) + 1)
    return f"{'':>{width}} | {' ' * (pointer_column - 1)}^-- {label}"
