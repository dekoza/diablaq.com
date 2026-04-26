"""Tests for sub-line catalog pages (Option B)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from jinja2 import DictLoader, Environment

from diablaq_site.models import Project
from diablaq_site.rendering import render_catalog_page


def _make_project(*, slug: str, line: str, title: str | None = None) -> Project:
    return Project(
        slug=slug,
        title=title or slug,
        line=line,
        summary="Test summary.",
        legacy_path=None,
        url=f"/komiksy/{slug}/",
        legacy_landing=False,
        cover_image=None,
        cover_aspect_class="cover--standard",
        html_body="",
        kind="title",
    )


@pytest.fixture
def minimal_env():
    templates = {
        "catalog.html": "{{ groups | map(attribute='label') | join(',') }}",
        "catalog_line.html": "{{ group.label }}|{{ group.projects | length }}",
    }
    return Environment(loader=DictLoader(templates))


def _run(env, tmp_path, projects):
    written: dict[str, str] = {}

    def fake_write(path, html):
        written[str(path)] = html

    def fake_render(env_, template, **ctx):
        return env_.get_template(template).render(**ctx)

    render_catalog_page(env, tmp_path, "", [], projects, fake_render, fake_write)
    return written


def test_subline_page_generated_for_each_represented_line(minimal_env, tmp_path):
    projects = [
        _make_project(slug="karmiciel", line="diablaq"),
        _make_project(slug="pisto", line="dobre-licho"),
        _make_project(slug="bzik", line="mecenat"),
    ]
    written = _run(minimal_env, tmp_path, projects)

    paths = set(written.keys())
    assert any("diablaq" in p for p in paths), "No diablaq sub-line page"
    assert any("dobre-licho" in p for p in paths), "No dobre-licho sub-line page"
    assert any("mecenat" in p for p in paths), "No mecenat sub-line page"


def test_no_subline_page_for_absent_line(minimal_env, tmp_path):
    projects = [_make_project(slug="karmiciel", line="diablaq")]
    written = _run(minimal_env, tmp_path, projects)

    assert not any("studio" in p for p in written), "Studio sub-page generated for empty line"


def test_overview_groups_have_url_and_description(minimal_env, tmp_path):
    captured: list[dict] = []

    def fake_write(path, html):
        pass

    def fake_render(env_, template, **ctx):
        if template == "catalog.html":
            captured.extend(ctx.get("groups", []))
        return env_.get_template(template).render(**ctx)

    projects = [
        _make_project(slug="karmiciel", line="diablaq"),
        _make_project(slug="pisto", line="dobre-licho"),
    ]
    render_catalog_page(minimal_env, tmp_path, "", [], projects, fake_render, fake_write)

    assert captured, "No groups passed to catalog.html"
    for group in captured:
        assert "url" in group, f"Group '{group.get('label')}' missing 'url'"
        assert "description" in group, f"Group '{group.get('label')}' missing 'description'"
        assert "total" in group, f"Group '{group.get('label')}' missing 'total'"


def test_overview_limits_preview_to_4(minimal_env, tmp_path):
    captured: list[dict] = []

    def fake_write(path, html):
        pass

    def fake_render(env_, template, **ctx):
        if template == "catalog.html":
            captured.extend(ctx.get("groups", []))
        return env_.get_template(template).render(**ctx)

    projects = [_make_project(slug=f"proj-{i}", line="diablaq") for i in range(6)]
    render_catalog_page(minimal_env, tmp_path, "", [], projects, fake_render, fake_write)

    main = next(g for g in captured if g["id"] == "diablaq")
    assert len(main["projects"]) <= 4, "Overview exposes more than 4 projects per line"


def test_overview_total_reflects_full_count(minimal_env, tmp_path):
    captured: list[dict] = []

    def fake_write(path, html):
        pass

    def fake_render(env_, template, **ctx):
        if template == "catalog.html":
            captured.extend(ctx.get("groups", []))
        return env_.get_template(template).render(**ctx)

    projects = [_make_project(slug=f"proj-{i}", line="diablaq") for i in range(6)]
    render_catalog_page(minimal_env, tmp_path, "", [], projects, fake_render, fake_write)

    main = next(g for g in captured if g["id"] == "diablaq")
    assert main["total"] == 6, "Overview 'total' does not reflect full project count"


def test_subline_page_receives_all_projects(minimal_env, tmp_path):
    captured: dict[str, list] = {}

    def fake_write(path, html):
        pass

    def fake_render(env_, template, **ctx):
        if template == "catalog_line.html":
            captured[ctx["group"]["id"]] = ctx["group"]["projects"]
        return env_.get_template(template).render(**ctx)

    projects = [_make_project(slug=f"proj-{i}", line="diablaq") for i in range(6)]
    render_catalog_page(minimal_env, tmp_path, "", [], projects, fake_render, fake_write)

    assert "diablaq" in captured, "No sub-line render for diablaq"
    assert len(captured["diablaq"]) == 6, "Sub-line page missing projects"


def test_line_meta_has_required_keys():
    from diablaq_site.rendering import _LINE_META

    required = {"label", "url_slug", "description"}
    for line_id, meta in _LINE_META.items():
        missing = required - meta.keys()
        assert not missing, f"_LINE_META['{line_id}'] missing: {missing}"


def test_full_build_generates_subline_pages(tmp_path):
    """Smoke test: real build produces sub-line index pages."""
    from diablaq_site.builder import build_site

    repo_root = Path(__file__).resolve().parents[1]
    out_dir = tmp_path / "dist"
    build_site(root=repo_root, out_dir=out_dir)

    assert (out_dir / "komiksy" / "index.html").exists()
    assert (out_dir / "komiksy" / "diablaq" / "index.html").exists()
    assert (out_dir / "komiksy" / "dobre-licho" / "index.html").exists()
    assert (out_dir / "komiksy" / "mecenat" / "index.html").exists()


def test_full_build_subline_contains_breadcrumb(tmp_path):
    """Sub-line pages should include a breadcrumb back to /komiksy/."""
    from diablaq_site.builder import build_site

    repo_root = Path(__file__).resolve().parents[1]
    out_dir = tmp_path / "dist"
    build_site(root=repo_root, out_dir=out_dir)

    html = (out_dir / "komiksy" / "dobre-licho" / "index.html").read_text(encoding="utf-8")
    assert "/komiksy/" in html
    assert "Komiksy" in html


def test_full_build_overview_has_see_all_links(tmp_path):
    """Catalog overview must contain 'See all' links for lines with projects."""
    from diablaq_site.builder import build_site

    repo_root = Path(__file__).resolve().parents[1]
    out_dir = tmp_path / "dist"
    build_site(root=repo_root, out_dir=out_dir)

    html = (out_dir / "komiksy" / "index.html").read_text(encoding="utf-8")
    assert "/komiksy/dobre-licho/" in html
    assert "/komiksy/mecenat/" in html
