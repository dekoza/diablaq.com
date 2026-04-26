"""Tests for subseries grouping on project pages (Option E)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from diablaq_site.models import Edition
from diablaq_site.rendering import _group_editions_by_subseries


def _make_edition(
    *,
    title: str,
    subseries: str | None = None,
    release_date: date | None = None,
) -> Edition:
    return Edition(
        url=f"/komiksy/test/{title.lower().replace(' ', '-').replace('#', '')}/",
        title=title,
        project_slug="test",
        release=None,
        release_date=release_date or date(2024, 1, 1),
        is_new=False,
        is_announcement=False,
        presale_url=None,
        legacy_anchor=None,
        primary_cover=None,
        cover_aspect_class="cover--standard",
        alternate_covers=[],
        previews=[],
        creators=[],
        creator_names=[],
        edition_specs={},
        products=[],
        html_body="",
        standalone=False,
        subseries=subseries,
        issue_number=None,
        issue_number_display=None,
    )


def test_empty_editions_returns_empty_list():
    assert _group_editions_by_subseries([]) == []


def test_all_none_subseries_returns_one_group():
    editions = [_make_edition(title=f"#{i}") for i in range(5)]
    groups = _group_editions_by_subseries(editions)
    assert len(groups) == 1
    assert groups[0][0] is None
    assert len(groups[0][1]) == 5


def test_all_named_same_subseries_returns_one_group():
    editions = [_make_edition(title=f"e{i}", subseries="Alfa") for i in range(3)]
    groups = _group_editions_by_subseries(editions)
    assert len(groups) == 1
    assert groups[0][0] == "Alfa"


def test_none_subseries_group_comes_before_named():
    editions = [
        _make_edition(title="extra-1", subseries="eXXXtra"),
        _make_edition(title="main-1", subseries=None),
    ]
    groups = _group_editions_by_subseries(editions)
    assert len(groups) == 2
    assert groups[0][0] is None, "None-subseries group must come first"
    assert groups[1][0] == "eXXXtra"


def test_named_groups_ordered_alphabetically():
    editions = [
        _make_edition(title="z", subseries="Zeta"),
        _make_edition(title="a", subseries="Alfa"),
        _make_edition(title="m", subseries="Mezo"),
    ]
    groups = _group_editions_by_subseries(editions)
    labels = [g[0] for g in groups]
    assert labels == sorted(labels), "Named groups must be in alphabetical order"


def test_within_group_order_is_preserved():
    editions = [
        _make_edition(title="#03", release_date=date(2024, 3, 1)),
        _make_edition(title="#01", release_date=date(2024, 1, 1)),
        _make_edition(title="#02", release_date=date(2024, 2, 1)),
    ]
    groups = _group_editions_by_subseries(editions)
    assert len(groups) == 1
    titles = [e.title for e in groups[0][1]]
    assert titles == ["#03", "#01", "#02"], "Within-group order must match input order"


def test_bzik_scenario_none_first_extra_second():
    """BZIK: 4 main issues (None) + 4 eXXXtra issues — two groups, None first."""
    main = [_make_edition(title=f"#{i}", subseries=None, release_date=date(2024, i, 1))
            for i in range(1, 5)]
    extra = [_make_edition(title=f"x{i}", subseries="eXXXtra", release_date=date(2024, i, 15))
             for i in range(1, 5)]
    # interleaved as they'd come from sorted(release_date desc)
    editions = sorted(main + extra, key=lambda e: e.release_date, reverse=True)

    groups = _group_editions_by_subseries(editions)

    assert len(groups) == 2
    none_label, none_eds = groups[0]
    extra_label, extra_eds = groups[1]
    assert none_label is None
    assert extra_label == "eXXXtra"
    assert len(none_eds) == 4
    assert len(extra_eds) == 4


def test_full_build_bzik_project_has_grouped_editions(tmp_path):
    """BZIK project page must render subseries section headers for main + eXXXtra."""
    from diablaq_site.builder import build_site

    repo_root = Path(__file__).resolve().parents[1]
    out_dir = tmp_path / "dist"
    build_site(root=repo_root, out_dir=out_dir)

    html = (out_dir / "komiksy" / "bzik" / "index.html").read_text(encoding="utf-8")
    # The eXXXtra subseries section header must be present
    assert "eXXXtra" in html, "BZIK page missing eXXXtra subseries section header"


def test_full_build_single_subseries_project_has_no_section_header(tmp_path):
    """Projects with a single subseries must NOT get a redundant section header."""
    from diablaq_site.builder import build_site

    repo_root = Path(__file__).resolve().parents[1]
    out_dir = tmp_path / "dist"
    build_site(root=repo_root, out_dir=out_dir)

    html = (out_dir / "komiksy" / "kodiak" / "index.html").read_text(encoding="utf-8")
    # Should have an "Wydania" heading but NOT a subseries-named heading
    assert "Wydania" in html
    # No arbitrary subseries heading (kodiak editions have no subseries field)
    assert "subseries" not in html.lower()
