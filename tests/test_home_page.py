"""Tests for homepage data: hero fallback, per-line sections, deduplication."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from diablaq_site.models import Edition, Project
from diablaq_site.rendering import _build_home_per_line_sections


# ── helpers ───────────────────────────────────────────────────────────────


def _edition(
    *,
    slug: str,
    project_slug: str,
    release_date: date,
    is_announcement: bool = False,
    cover_image: str | None = "/img/cover.jpg",
    featured: bool = False,
) -> Edition:
    return Edition(
        url=f"/komiksy/{project_slug}/{slug}/",
        title=slug,
        project_slug=project_slug,
        release=None,
        release_date=release_date,
        is_new=False,
        is_announcement=is_announcement,
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
        subseries=None,
        issue_number=None,
        issue_number_display=None,
        featured=featured,
        cover_image=cover_image,  # shortcut via property — set primary_cover instead
    )


def _project(*, slug: str, line: str) -> Project:
    return Project(
        slug=slug,
        title=slug,
        line=line,
        summary="summary",
        legacy_path=None,
        url=f"/komiksy/{slug}/",
        legacy_landing=False,
        cover_image="/img/cover.jpg",
        cover_aspect_class="cover--standard",
        html_body="",
        kind="title",
    )


# Edition doesn't have cover_image as a direct field (it's a property from primary_cover),
# so build a helper that patches the property for test purposes.
from diablaq_site.models import EditionCover


def _edition_with_cover(
    *,
    slug: str,
    project_slug: str,
    release_date: date,
    is_announcement: bool = False,
    featured: bool = False,
) -> Edition:
    cover = EditionCover(
        id="primary",
        label=None,
        image=f"/img/{slug}.jpg",
        alt=slug,
        artist_name=None,
        person_slug=None,
    )
    return Edition(
        url=f"/komiksy/{project_slug}/{slug}/",
        title=slug,
        project_slug=project_slug,
        release=None,
        release_date=release_date,
        is_new=False,
        is_announcement=is_announcement,
        presale_url=None,
        legacy_anchor=None,
        primary_cover=cover,
        cover_aspect_class="cover--standard",
        alternate_covers=[],
        previews=[],
        creators=[],
        creator_names=[],
        edition_specs={},
        products=[],
        html_body="",
        standalone=False,
        subseries=None,
        issue_number=None,
        issue_number_display=None,
        featured=featured,
    )


def _edition_no_cover(
    *,
    slug: str,
    project_slug: str,
    release_date: date,
    is_announcement: bool = False,
    featured: bool = False,
) -> Edition:
    return Edition(
        url=f"/komiksy/{project_slug}/{slug}/",
        title=slug,
        project_slug=project_slug,
        release=None,
        release_date=release_date,
        is_new=False,
        is_announcement=is_announcement,
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
        subseries=None,
        issue_number=None,
        issue_number_display=None,
        featured=featured,
    )


# ── hero fallback ─────────────────────────────────────────────────────────


def _pick_hero_slides(editions: list[Edition]) -> list[Edition]:
    """Replicate the carousel hero selection logic from builder._render_all."""
    featured = sorted(
        [e for e in editions if e.featured and e.cover_image],
        key=lambda e: e.featured_order,
    )
    if featured:
        return featured
    past_with_cover = sorted(
        [e for e in editions
         if not e.is_announcement
         and e.release_date.year < 9999
         and e.cover_image],
        key=lambda e: e.release_date,
        reverse=True,
    )
    return past_with_cover[:1]


def _pick_hero(editions: list[Edition]) -> Edition | None:
    """Return the first hero slide, or None."""
    slides = _pick_hero_slides(editions)
    return slides[0] if slides else None


def test_hero_prefers_featured_over_latest_release():
    older_featured = _edition_with_cover(
        slug="old-featured", project_slug="p", release_date=date(2023, 1, 1), featured=True
    )
    newer_release = _edition_with_cover(
        slug="newer", project_slug="p", release_date=date(2024, 6, 1)
    )
    assert _pick_hero([older_featured, newer_release]) is older_featured


def test_hero_falls_back_to_latest_release_when_no_featured():
    announcement = _edition_with_cover(
        slug="ann", project_slug="p", release_date=date(2099, 1, 1), is_announcement=True
    )
    old_release = _edition_with_cover(
        slug="old", project_slug="p", release_date=date(2023, 1, 1)
    )
    new_release = _edition_with_cover(
        slug="new", project_slug="p", release_date=date(2024, 6, 1)
    )
    # Announcement must NOT be picked; newest release wins
    hero = _pick_hero([announcement, old_release, new_release])
    assert hero is new_release


def test_hero_skips_announcement_even_when_only_option_with_cover():
    announcement = _edition_with_cover(
        slug="ann", project_slug="p", release_date=date(2099, 1, 1), is_announcement=True
    )
    release_no_cover = _edition_no_cover(
        slug="rel", project_slug="p", release_date=date(2024, 1, 1)
    )
    assert _pick_hero([announcement, release_no_cover]) is None


def test_hero_returns_none_when_no_cover_available():
    editions = [
        _edition_no_cover(slug="a", project_slug="p", release_date=date(2024, 1, 1)),
        _edition_no_cover(slug="b", project_slug="p", release_date=date(2024, 2, 1)),
    ]
    assert _pick_hero(editions) is None


# ── per-line sections ─────────────────────────────────────────────────────


def test_per_line_sections_excludes_hero():
    projects = [_project(slug="proj", line="diablaq")]
    hero = _edition_with_cover(slug="hero", project_slug="proj", release_date=date(2024, 6, 1))
    other = _edition_with_cover(slug="other", project_slug="proj", release_date=date(2024, 3, 1))
    editions = [hero, other]

    sections = _build_home_per_line_sections(projects, editions, [hero], newest_anytime=[])

    assert len(sections) == 1
    shown_urls = {e.url for e in sections[0]["editions"]}
    assert hero.url not in shown_urls
    assert other.url in shown_urls


def test_per_line_sections_excludes_newest_anytime_items():
    projects = [_project(slug="proj", line="diablaq")]
    e1 = _edition_with_cover(slug="e1", project_slug="proj", release_date=date(2024, 6, 1))
    e2 = _edition_with_cover(slug="e2", project_slug="proj", release_date=date(2024, 5, 1))
    e3 = _edition_with_cover(slug="e3", project_slug="proj", release_date=date(2024, 4, 1))

    sections = _build_home_per_line_sections(
        projects, [e1, e2, e3], [], newest_anytime=[e1, e2]
    )

    shown_urls = {e.url for e in sections[0]["editions"]}
    assert e1.url not in shown_urls
    assert e2.url not in shown_urls
    assert e3.url in shown_urls


def test_per_line_sections_excludes_announcements():
    projects = [_project(slug="proj", line="diablaq")]
    ann = _edition_with_cover(
        slug="ann", project_slug="proj",
        release_date=date(2099, 1, 1), is_announcement=True
    )
    release = _edition_with_cover(
        slug="rel", project_slug="proj", release_date=date(2024, 1, 1)
    )

    sections = _build_home_per_line_sections(projects, [ann, release], [], [])

    shown_urls = {e.url for e in sections[0]["editions"]}
    assert ann.url not in shown_urls
    assert release.url in shown_urls


def test_per_line_sections_caps_at_8():
    projects = [_project(slug="proj", line="diablaq")]
    editions = [
        _edition_with_cover(slug=f"e{i}", project_slug="proj", release_date=date(2024, 1, i + 1))
        for i in range(12)
    ]

    sections = _build_home_per_line_sections(projects, editions, [], [])

    assert len(sections[0]["editions"]) == 8


def test_per_line_sections_has_more_true_when_over_cap():
    projects = [_project(slug="proj", line="diablaq")]
    editions = [
        _edition_with_cover(slug=f"e{i}", project_slug="proj", release_date=date(2024, 1, i + 1))
        for i in range(9)
    ]

    sections = _build_home_per_line_sections(projects, editions, [], [])

    assert sections[0]["has_more"] is True


def test_per_line_sections_has_more_false_at_cap():
    projects = [_project(slug="proj", line="diablaq")]
    editions = [
        _edition_with_cover(slug=f"e{i}", project_slug="proj", release_date=date(2024, 1, i + 1))
        for i in range(8)
    ]

    sections = _build_home_per_line_sections(projects, editions, [], [])

    assert sections[0]["has_more"] is False


def test_per_line_sections_has_more_false_under_cap():
    projects = [_project(slug="proj", line="diablaq")]
    editions = [
        _edition_with_cover(slug=f"e{i}", project_slug="proj", release_date=date(2024, 1, i + 1))
        for i in range(3)
    ]

    sections = _build_home_per_line_sections(projects, editions, [], [])

    assert sections[0]["has_more"] is False


def test_per_line_sections_empty_when_all_excluded():
    projects = [_project(slug="proj", line="diablaq")]
    e = _edition_with_cover(slug="e", project_slug="proj", release_date=date(2024, 1, 1))

    sections = _build_home_per_line_sections(projects, [e], [e], newest_anytime=[])

    assert sections == []


def test_per_line_sections_sorted_newest_first():
    projects = [_project(slug="proj", line="diablaq")]
    editions = [
        _edition_with_cover(slug="old", project_slug="proj", release_date=date(2024, 1, 1)),
        _edition_with_cover(slug="new", project_slug="proj", release_date=date(2024, 6, 1)),
        _edition_with_cover(slug="mid", project_slug="proj", release_date=date(2024, 3, 1)),
    ]

    sections = _build_home_per_line_sections(projects, editions, [], [])

    dates = [e.release_date for e in sections[0]["editions"]]
    assert dates == sorted(dates, reverse=True)


def test_per_line_sections_groups_by_line():
    proj_a = _project(slug="proj-a", line="diablaq")
    proj_b = _project(slug="proj-b", line="dobre-licho")
    ed_a = _edition_with_cover(slug="ea", project_slug="proj-a", release_date=date(2024, 1, 1))
    ed_b = _edition_with_cover(slug="eb", project_slug="proj-b", release_date=date(2024, 2, 1))

    sections = _build_home_per_line_sections([proj_a, proj_b], [ed_a, ed_b], [], [])

    ids = [s["id"] for s in sections]
    assert "diablaq" in ids
    assert "dobre-licho" in ids

    diablaq = next(s for s in sections if s["id"] == "diablaq")
    dobre = next(s for s in sections if s["id"] == "dobre-licho")
    assert any(e.url == ed_a.url for e in diablaq["editions"])
    assert any(e.url == ed_b.url for e in dobre["editions"])


def test_per_line_sections_has_url_and_label():
    projects = [_project(slug="proj", line="dobre-licho")]
    editions = [
        _edition_with_cover(slug="e", project_slug="proj", release_date=date(2024, 1, 1))
    ]

    sections = _build_home_per_line_sections(projects, editions, [], [])

    s = sections[0]
    assert s["url"] == "/komiksy/dobre-licho/"
    assert s["label"] == "Dobre Licho"


def test_per_line_sections_unknown_project_slug_skipped():
    projects = [_project(slug="known", line="diablaq")]
    orphan = _edition_with_cover(
        slug="orphan", project_slug="unknown-slug", release_date=date(2024, 1, 1)
    )
    known = _edition_with_cover(
        slug="known-e", project_slug="known", release_date=date(2024, 1, 1)
    )

    sections = _build_home_per_line_sections(projects, [orphan, known], [], [])

    all_editions = [e for s in sections for e in s["editions"]]
    urls = {e.url for e in all_editions}
    assert orphan.url not in urls
    assert known.url in urls


# ── smoke tests ───────────────────────────────────────────────────────────


def test_full_build_homepage_has_no_full_catalog(tmp_path: Path) -> None:
    """Homepage must not contain the full 30-project catalog grid."""
    from diablaq_site.builder import build_site

    repo_root = Path(__file__).resolve().parents[1]
    out_dir = tmp_path / "dist"
    build_site(root=repo_root, out_dir=out_dir)

    html = (out_dir / "index.html").read_text(encoding="utf-8")
    assert "Wszystkie komiksy wydawnictwa Diablaq." not in html


def test_full_build_homepage_per_line_sections_link_to_subline_pages(tmp_path: Path) -> None:
    """Per-line mini-catalog sections must link to /komiksy/{line}/ pages."""
    from diablaq_site.builder import build_site

    repo_root = Path(__file__).resolve().parents[1]
    out_dir = tmp_path / "dist"
    build_site(root=repo_root, out_dir=out_dir)

    html = (out_dir / "index.html").read_text(encoding="utf-8")
    assert "/komiksy/diablaq/" in html
    assert "/komiksy/dobre-licho/" in html


# ── hero carousel ─────────────────────────────────────────────────────────


def test_hero_all_featured_editions_become_slides():
    e1 = _edition_with_cover(slug="e1", project_slug="p", release_date=date(2024, 1, 1), featured=True)
    e2 = _edition_with_cover(slug="e2", project_slug="p", release_date=date(2024, 6, 1), featured=True)
    non = _edition_with_cover(slug="non", project_slug="p", release_date=date(2024, 9, 1))

    slides = _pick_hero_slides([e1, e2, non])

    assert len(slides) == 2
    assert e1 in slides
    assert e2 in slides
    assert non not in slides


def test_hero_slides_sorted_by_featured_order():
    from diablaq_site.models import EditionCover

    def _feat(slug, order):
        cover = EditionCover(
            id="primary", label=None, image=f"/img/{slug}.jpg",
            alt=slug, artist_name=None, person_slug=None,
        )
        return Edition(
            url=f"/komiksy/p/{slug}/", title=slug, project_slug="p",
            release=None, release_date=date(2024, 1, 1),
            is_new=False, is_announcement=False, presale_url=None,
            legacy_anchor=None, primary_cover=cover,
            cover_aspect_class="cover--standard", alternate_covers=[],
            previews=[], creators=[], creator_names=[], edition_specs={},
            products=[], html_body="", standalone=False, subseries=None,
            issue_number=None, issue_number_display=None,
            featured=True, featured_order=order,
        )

    e_second = _feat("second", order=2)
    e_first = _feat("first", order=1)
    e_third = _feat("third", order=3)

    slides = _pick_hero_slides([e_second, e_third, e_first])

    assert slides == [e_first, e_second, e_third]


def test_hero_fallback_returned_as_single_element_list():
    e = _edition_with_cover(slug="e", project_slug="p", release_date=date(2024, 3, 1))

    slides = _pick_hero_slides([e])

    assert slides == [e]


def test_hero_fallback_empty_list_when_no_cover():
    e = _edition_no_cover(slug="e", project_slug="p", release_date=date(2024, 3, 1))

    assert _pick_hero_slides([e]) == []


def test_per_line_excludes_all_hero_slides():
    projects = [_project(slug="proj", line="diablaq")]
    s1 = _edition_with_cover(slug="s1", project_slug="proj", release_date=date(2024, 1, 1), featured=True)
    s2 = _edition_with_cover(slug="s2", project_slug="proj", release_date=date(2024, 2, 1), featured=True)
    other = _edition_with_cover(slug="other", project_slug="proj", release_date=date(2024, 3, 1))

    sections = _build_home_per_line_sections(projects, [s1, s2, other], [s1, s2], [])

    shown_urls = {e.url for s in sections for e in s["editions"]}
    assert s1.url not in shown_urls
    assert s2.url not in shown_urls
    assert other.url in shown_urls


def test_full_build_homepage_renders_hero_carousel(tmp_path: Path) -> None:
    """Built homepage must contain the hero carousel markup."""
    from diablaq_site.builder import build_site

    repo_root = Path(__file__).resolve().parents[1]
    out_dir = tmp_path / "dist"
    build_site(root=repo_root, out_dir=out_dir)

    html = (out_dir / "index.html").read_text(encoding="utf-8")
    assert "hero-carousel" in html
    assert "hero-slide" in html
