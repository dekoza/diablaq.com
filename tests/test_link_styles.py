from __future__ import annotations

import re
from pathlib import Path

from diablaq_site.builder import build_site


def _extract_hex_variable(css: str, variable_name: str) -> str:
    match = re.search(rf"{re.escape(variable_name)}:\s*(#[0-9a-fA-F]{{6}})\s*;", css)
    assert match is not None, f"Missing CSS variable: {variable_name}"
    return match.group(1)


def _extract_rule(css: str, selector: str) -> str:
    match = re.search(rf"{re.escape(selector)}\s*\{{(?P<body>.*?)\}}", css, re.DOTALL)
    assert match is not None, f"Missing CSS rule: {selector}"
    return match.group("body")


def _contrast_ratio(foreground_hex: str, background_hex: str) -> float:
    def _hex_to_rgb(color: str) -> tuple[float, float, float]:
        color = color.lstrip("#")
        return tuple(int(color[index:index + 2], 16) / 255 for index in (0, 2, 4))

    def _channel(value: float) -> float:
        if value <= 0.03928:
            return value / 12.92
        return ((value + 0.055) / 1.055) ** 2.4

    def _luminance(color: str) -> float:
        red, green, blue = map(_channel, _hex_to_rgb(color))
        return 0.2126 * red + 0.7152 * green + 0.0722 * blue

    foreground_luminance = _luminance(foreground_hex)
    background_luminance = _luminance(background_hex)
    lighter = max(foreground_luminance, background_luminance)
    darker = min(foreground_luminance, background_luminance)
    return (lighter + 0.05) / (darker + 0.05)


def _create_link_regression_fixture(work_root: Path, repo_root: Path) -> Path:
    work_root.mkdir(parents=True, exist_ok=True)
    (work_root / "templates").symlink_to(repo_root / "templates")
    (work_root / "css").symlink_to(repo_root / "css")
    (work_root / "img").symlink_to(repo_root / "img")

    content_root = work_root / "content"
    (content_root / "pages").mkdir(parents=True)
    (content_root / "people").mkdir(parents=True)
    (content_root / "blog").mkdir(parents=True)
    (content_root / "projects" / "test-project" / "editions").mkdir(parents=True)
    (content_root / "projects" / "test-universe").mkdir(parents=True)
    (content_root / "projects" / "related-title").mkdir(parents=True)

    (content_root / "pages" / "test-page.md").write_text(
        """\
---
title: Test Page
---

Page body with a [page link](https://example.com/page).
""",
        encoding="utf-8",
    )

    (content_root / "people" / "test-author.md").write_text(
        """\
---
name: Test Author
---

Biography with a [person link](https://example.com/person).
""",
        encoding="utf-8",
    )

    (content_root / "blog" / "2026-01-15-test-post.md").write_text(
        """\
---
title: Test Blog Post
date: 2026-01-15
summary: Link styling regression post
---

Blog body with a [blog link](https://example.com/blog).
""",
        encoding="utf-8",
    )

    (content_root / "projects" / "test-project" / "project.md").write_text(
        """\
---
title: Test Project
line: diablaq
summary: Link styling regression project
cover_image: /img/logo.png
---

Project body with a [project link](https://example.com/project).
""",
        encoding="utf-8",
    )

    (content_root / "projects" / "test-project" / "editions" / "01.md").write_text(
        """\
---
title: Test Edition
release_date: 2025-01-01
primary_cover:
  image: /img/belzebubs1.jpg
---

Edition body with an [edition link](https://example.com/edition).
""",
        encoding="utf-8",
    )

    (content_root / "projects" / "test-universe" / "project.md").write_text(
        """\
---
title: Test Universe
line: diablaq
kind: universe
summary: Link styling regression universe
cover_image: /img/logo.png
---

Universe body with a [universe link](https://example.com/universe).
""",
        encoding="utf-8",
    )

    (content_root / "projects" / "related-title" / "project.md").write_text(
        """\
---
title: Related Title
line: diablaq
summary: Related title for the universe page
universe_slug: test-universe
cover_image: /img/logo.png
---

Related title body.
""",
        encoding="utf-8",
    )

    return work_root


def _link_is_inside_rich_text_container(html: str, url: str) -> bool:
    pattern = re.compile(
        rf'class="[^"]*rich-text[^"]*"[^>]*>.*?<a href="{re.escape(url)}"',
        re.DOTALL,
    )
    return pattern.search(html) is not None


def test_rich_text_links_use_accessible_visited_states(repo_root: Path) -> None:
    css = (repo_root / "css" / "diablaq.css").read_text(encoding="utf-8")

    background_color = _extract_hex_variable(css, "--bg")
    link_color = _extract_hex_variable(css, "--link-text")
    visited_color = _extract_hex_variable(css, "--link-visited")
    hover_color = _extract_hex_variable(css, "--link-hover")

    assert link_color != visited_color
    assert _contrast_ratio(link_color, background_color) >= 4.5
    assert _contrast_ratio(visited_color, background_color) >= 4.5
    assert _contrast_ratio(hover_color, background_color) >= 4.5

    rich_text_rule = _extract_rule(css, ".rich-text a")
    visited_rule = _extract_rule(css, ".rich-text a:visited")
    hover_rule = _extract_rule(css, ".rich-text a:hover")
    focus_rule = _extract_rule(css, ".rich-text a:focus-visible")

    assert "color: var(--link-text);" in rich_text_rule
    assert "text-decoration: underline;" in rich_text_rule
    assert "color: var(--link-visited);" in visited_rule
    assert "color: var(--link-hover);" in hover_rule
    assert "outline: 2px solid var(--link-hover);" in focus_rule
    assert "main a:visited" not in css


def test_markdown_output_wraps_inline_links_in_rich_text(repo_root: Path, tmp_path: Path) -> None:
    work_root = _create_link_regression_fixture(tmp_path / "repo", repo_root)
    out_dir = tmp_path / "dist"

    build_site(root=work_root, out_dir=out_dir)

    rendered_pages = {
        out_dir / "test-page" / "index.html": "https://example.com/page",
        out_dir / "ludzie" / "test-author" / "index.html": "https://example.com/person",
        out_dir / "blog" / "test-post" / "index.html": "https://example.com/blog",
        out_dir / "komiksy" / "test-project" / "index.html": "https://example.com/project",
        out_dir / "komiksy" / "test-project" / "01" / "index.html": "https://example.com/edition",
        out_dir / "komiksy" / "test-universe" / "index.html": "https://example.com/universe",
    }

    for html_path, url in rendered_pages.items():
        html = html_path.read_text(encoding="utf-8")
        assert _link_is_inside_rich_text_container(html, url), html_path
