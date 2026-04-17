from datetime import date

from diablaq_site.builder import _process_content
from diablaq_site.models import Edition


def test_process_content_newest_anytime_excludes_future_dates():
    """newest_anytime excludes future and sentinel-9999 dates."""
    past_edition = Edition(
        url="/pl/wydania/past",
        title="Past Edition",
        project_slug="test-project",
        release="First",
        release_date=date(2024, 1, 1),
        is_new=False,
        is_announcement=False,
        presale_url=None,
        legacy_anchor=None,
        cover_image="cover.jpg",
        cover_alt="Cover alt",
        cover_aspect_class="aspect-auto",
        covers=[],
        previews=[],
        creators=[],
        creator_names=[],
        specs={},
        buy_links=[],
        variants=[],
        html_body="<p>Content</p>",
        standalone=True,
        subseries=None,
        issue_number=None,
        issue_number_display=None,
    )
    future_edition = Edition(
        url="/pl/wydania/future",
        title="Future Edition",
        project_slug="test-project",
        release="Second",
        release_date=date(2026, 12, 31),
        is_new=False,
        is_announcement=False,
        presale_url=None,
        legacy_anchor=None,
        cover_image="cover.jpg",
        cover_alt="Cover alt",
        cover_aspect_class="aspect-auto",
        covers=[],
        previews=[],
        creators=[],
        creator_names=[],
        specs={},
        buy_links=[],
        variants=[],
        html_body="<p>Content</p>",
        standalone=True,
        subseries=None,
        issue_number=None,
        issue_number_display=None,
    )
    sentinel_edition = Edition(
        url="/pl/wydania/tbd",
        title="TBD Edition",
        project_slug="test-project",
        release="Third",
        release_date=date(9999, 12, 31),
        is_new=False,
        is_announcement=False,
        presale_url=None,
        legacy_anchor=None,
        cover_image="cover.jpg",
        cover_alt="Cover alt",
        cover_aspect_class="aspect-auto",
        covers=[],
        previews=[],
        creators=[],
        creator_names=[],
        specs={},
        buy_links=[],
        variants=[],
        html_body="<p>Content</p>",
        standalone=True,
        subseries=None,
        issue_number=None,
        issue_number_display=None,
    )

    _, _, newest_anytime, _, _, _ = _process_content(
        projects=[],
        editions=[past_edition, future_edition, sentinel_edition],
        people=[],
        blog_posts=[],
        today=date(2025, 6, 1),
    )

    assert len(newest_anytime) == 1
    assert newest_anytime[0].title == "Past Edition"


def test_process_content_newest_anytime_limits_to_5():
    """newest_anytime returns exactly 5 items even when more exist."""
    editions = [
        Edition(
            url=f"/komiksy/edition-{i}",
            title=f"Edition {i}",
            project_slug="test-project",
            release=f"Release {i}",
            release_date=date(2024, 1, i + 1),
            is_new=(i < 2),
            is_announcement=False,
            presale_url=None,
            legacy_anchor=None,
            cover_image="cover.jpg",
            cover_alt="Cover alt",
            cover_aspect_class="aspect-auto",
            covers=[],
            previews=[],
            creators=[],
            creator_names=[],
            specs={},
            buy_links=[],
            variants=[],
            html_body="<p>Content</p>",
            standalone=True,
            subseries=None,
            issue_number=None,
            issue_number_display=None,
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


def test_process_content_newest_anytime_sorted_descending():
    """newest_anytime items are sorted by release_date descending."""
    editions = [
        Edition(
            url=f"/komiksy/edition-{i}",
            title=f"Edition {i}",
            project_slug="test-project",
            release=f"Release {i}",
            release_date=date(2024, 1, i + 1),
            is_new=False,
            is_announcement=False,
            presale_url=None,
            legacy_anchor=None,
            cover_image="cover.jpg",
            cover_alt="Cover alt",
            cover_aspect_class="aspect-auto",
            covers=[],
            previews=[],
            creators=[],
            creator_names=[],
            specs={},
            buy_links=[],
            variants=[],
            html_body="<p>Content</p>",
            standalone=True,
            subseries=None,
            issue_number=None,
            issue_number_display=None,
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
    for i in range(len(newest_anytime) - 1):
        assert newest_anytime[i].release_date >= newest_anytime[i + 1].release_date
