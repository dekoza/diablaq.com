from __future__ import annotations

from datetime import date

from diablaq_site.builder import _process_content
from diablaq_site.models import Edition


def _make_edition(*, title: str, release_date: date, is_new: bool = False, is_announcement: bool = False) -> Edition:
    return Edition(
        url=f"/komiksy/{title.lower().replace(' ', '-')}/",
        title=title,
        project_slug="test-project",
        release="Release",
        release_date=release_date,
        is_new=is_new,
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
        html_body="<p>Content</p>",
        standalone=True,
        subseries=None,
        issue_number=None,
        issue_number_display=None,
    )


def test_process_content_newest_anytime_excludes_future_dates() -> None:
    past_edition = _make_edition(title="Past Edition", release_date=date(2024, 1, 1))
    future_edition = _make_edition(title="Future Edition", release_date=date(2026, 12, 31))
    sentinel_edition = _make_edition(title="TBD Edition", release_date=date(9999, 12, 31))

    _, _, newest_anytime, _, _, _ = _process_content(
        projects=[],
        editions=[past_edition, future_edition, sentinel_edition],
        people=[],
        blog_posts=[],
        today=date(2025, 6, 1),
    )

    assert len(newest_anytime) == 1
    assert newest_anytime[0].title == "Past Edition"


def test_process_content_newest_anytime_limits_to_5() -> None:
    editions = [
        _make_edition(
            title=f"Edition {i}",
            release_date=date(2024, 1, i + 1),
            is_new=i < 2,
        )
        for i in range(7)
    ]

    _, _, newest_anytime, _, _, _ = _process_content(
        projects=[],
        editions=editions,
        people=[],
        blog_posts=[],
        today=date(2025, 6, 1),
    )

    assert len(newest_anytime) == 5


def test_process_content_newest_anytime_sorted_descending() -> None:
    editions = [
        _make_edition(title=f"Edition {i}", release_date=date(2024, 1, i + 1))
        for i in range(7)
    ]

    _, _, newest_anytime, _, _, _ = _process_content(
        projects=[],
        editions=editions,
        people=[],
        blog_posts=[],
        today=date(2025, 6, 1),
    )

    assert len(newest_anytime) == 5
    for i in range(len(newest_anytime) - 1):
        assert newest_anytime[i].release_date >= newest_anytime[i + 1].release_date
