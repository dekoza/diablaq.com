from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest


def test_pick_cover_reads_primary_cover() -> None:
    from diablaq_site.parsing import pick_cover

    meta = {
        "primary_cover": {
            "image": "/img/cover.jpg",
            "alt": "Main cover",
        }
    }

    image, alt = pick_cover(meta)

    assert image == "/img/cover.jpg"
    assert alt == "Main cover"


def test_parse_cover_list_requires_unique_cover_ids() -> None:
    from diablaq_site.parsing import parse_cover_list

    meta = {
        "alternate_covers": [
            {"id": "alt", "image": "/img/alt-a.jpg"},
            {"id": "alt", "image": "/img/alt-b.jpg"},
        ]
    }

    with pytest.raises(ValueError, match=r"duplicate.*alternate_covers"):
        parse_cover_list(meta, "alternate_covers", source_path=Path("test.md"))


def test_parse_products_supports_cover_ids_ean2_and_numbered_copies() -> None:
    from diablaq_site.models import EditionCover
    from diablaq_site.parsing import parse_products

    primary_cover = EditionCover(
        id="primary",
        label="Standardowa",
        image="/img/standard.jpg",
        alt="Standard cover",
        artist_name="Artist One",
        person_slug="artist-one",
    )
    alternate_cover = EditionCover(
        id="limitowana",
        label="Limitowana",
        image="/img/limited.jpg",
        alt="Limited cover",
        artist_name="Artist Two",
        person_slug="artist-two",
    )
    meta = {
        "products": [
            {
                "format": "zeszyt",
                "cover_id": "primary",
                "isbn13": "978-0-306-40615-7",
                "ean2": 1,
                "price": "19,99 zł",
                "limited": False,
                "buy_links": [{"label": "Store", "url": "https://example.com/standard"}],
            },
            {
                "format": "zeszyt",
                "cover_id": "limitowana",
                "isbn13": "9780306406157",
                "ean2": "02",
                "price": "29,99 zł",
                "limited": True,
                "numbered_copies": 333,
                "buy_links": [{"label": "Store", "url": "https://example.com/limited"}],
                "specs": {"Oprawa": "zeszytowa"},
            },
        ]
    }

    products = parse_products(
        meta,
        source_path=Path("test.md"),
        primary_cover=primary_cover,
        alternate_covers=[alternate_cover],
    )

    assert len(products) == 2
    assert products[0].cover_id == "primary"
    assert products[0].isbn13 == "9780306406157"
    assert products[0].ean2 == "01"
    assert products[1].cover_id == "limitowana"
    assert products[1].limited is True
    assert products[1].numbered_copies == 333
    assert products[1].specs == {"Oprawa": "zeszytowa"}


def test_parse_products_rejects_numbered_copies_without_limited_flag() -> None:
    from diablaq_site.models import EditionCover
    from diablaq_site.parsing import parse_products

    primary_cover = EditionCover(
        id="primary",
        label=None,
        image="/img/cover.jpg",
        alt=None,
        artist_name=None,
        person_slug=None,
    )
    meta = {
        "products": [
            {
                "format": "twarda",
                "numbered_copies": 333,
            }
        ]
    }

    with pytest.raises(ValueError, match=r"numbered_copies.*limited"):
        parse_products(
            meta,
            source_path=Path("test.md"),
            primary_cover=primary_cover,
            alternate_covers=[],
        )


def test_load_projects_and_editions_reads_new_cover_and_product_schema(tmp_path: Path) -> None:
    from diablaq_site.parsing import load_projects_and_editions

    projects_dir = tmp_path / "content" / "projects"
    project_dir = projects_dir / "alpha"
    (project_dir / "editions").mkdir(parents=True)

    (project_dir / "project.md").write_text(
        """\
---
title: Alpha
line: diablaq
summary: Alpha summary
---
Project body.
""",
        encoding="utf-8",
    )
    (project_dir / "editions" / "index.md").write_text(
        """\
---
title: Alpha
release_date: 2026-02-01
standalone: true
primary_cover:
  label: Standardowa
  image: /img/alpha-standard.jpg
  alt: Alpha standard
  artist_name: Artist One
  person_slug: artist-one
alternate_covers:
  - id: alt
    label: Limitowana
    image: /img/alpha-limited.jpg
    alt: Alpha limited
    artist_name: Artist Two
    person_slug: artist-two
previews:
  - image: /img/alpha-preview-1.jpg
    alt: Alpha preview 1
creators:
  - role: Scenariusz
    name: Writer One
    person_slug: writer-one
edition_specs:
  "Liczba stron": "24"
products:
  - format: zeszyt
    cover_id: primary
    isbn13: "9780306406157"
    price: "19,99 zł"
    buy_links:
      - label: Strefa Komiksu
        url: https://example.com/alpha-standard
  - format: zeszyt
    cover_id: alt
    isbn13: "9780306406157"
    ean2: "02"
    price: "24,99 zł"
    limited: true
    buy_links:
      - label: Strefa Komiksu
        url: https://example.com/alpha-limited
---
Edition body.
""",
        encoding="utf-8",
    )

    projects, editions = load_projects_and_editions(projects_dir, tmp_path)

    assert projects[0].cover_image == "/img/alpha-standard.jpg"
    assert editions[0].primary_cover is not None
    assert editions[0].primary_cover.artist_name == "Artist One"
    assert [cover.id for cover in editions[0].alternate_covers] == ["alt"]
    assert editions[0].products[1].cover_id == "alt"
    assert editions[0].products[1].ean2 == "02"
    assert editions[0].edition_specs == {"Liczba stron": "24"}
    assert editions[0].cover_image == "/img/alpha-standard.jpg"


def test_load_projects_and_editions_rejects_legacy_edition_fields(tmp_path: Path) -> None:
    from diablaq_site.parsing import load_projects_and_editions

    projects_dir = tmp_path / "content" / "projects"
    project_dir = projects_dir / "legacy"
    (project_dir / "editions").mkdir(parents=True)

    (project_dir / "project.md").write_text(
        """\
---
title: Legacy
line: diablaq
summary: Legacy summary
cover_image: /img/project.jpg
---
Project body.
""",
        encoding="utf-8",
    )
    (project_dir / "editions" / "index.md").write_text(
        """\
---
title: Legacy
release_date: 2026-02-01
cover_image: /img/legacy.jpg
products:
  - format: zeszyt
---
Edition body.
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=r"legacy.*cover_image"):
        load_projects_and_editions(projects_dir, tmp_path)


def test_apply_person_credit_names_updates_cover_artist_names() -> None:
    from diablaq_site.models import Edition, EditionCover, Person
    from diablaq_site.parsing import apply_person_credit_names

    edition = Edition(
        url="/komiksy/test/",
        title="Test",
        project_slug="test",
        release=None,
        release_date=date(2024, 1, 1),
        is_new=True,
        is_announcement=False,
        presale_url=None,
        legacy_anchor=None,
        primary_cover=EditionCover(
            id="primary",
            label="Standardowa",
            image="/img/test.jpg",
            alt="Test cover",
            artist_name="Weronika Dobrowolska",
            person_slug="werka-dobro",
        ),
        cover_aspect_class="cover--standard",
        alternate_covers=[],
        previews=[],
        creators=[],
        creator_names=[],
        edition_specs={},
        products=[],
        html_body="",
        standalone=True,
        subseries=None,
        issue_number=None,
        issue_number_display=None,
    )
    people = [
        Person(
            slug="werka-dobro",
            name="Weronika Dobrowolska",
            credit_name="Werka Dobro",
            photo=None,
            photo_thumb=None,
            html_bio="",
            related_editions=[],
        )
    ]

    resolved = apply_person_credit_names([edition], people)

    assert resolved[0].primary_cover is not None
    assert resolved[0].primary_cover.artist_name == "Werka Dobro"


def test_build_people_index_matches_cover_artists() -> None:
    from diablaq_site.models import Edition, EditionCover, Person
    from diablaq_site.parsing import build_people_index

    person = Person(
        slug="werka-dobro",
        name="Weronika Dobrowolska",
        credit_name="Werka Dobro",
        photo=None,
        photo_thumb=None,
        html_bio="",
        related_editions=[],
    )
    edition = Edition(
        url="/komiksy/test/",
        title="Test",
        project_slug="test",
        release=None,
        release_date=date(2024, 1, 1),
        is_new=True,
        is_announcement=False,
        presale_url=None,
        legacy_anchor=None,
        primary_cover=EditionCover(
            id="primary",
            label="Standardowa",
            image="/img/test.jpg",
            alt="Test cover",
            artist_name="Werka Dobro",
            person_slug="werka-dobro",
        ),
        cover_aspect_class="cover--standard",
        alternate_covers=[],
        previews=[],
        creators=[],
        creator_names=[],
        edition_specs={},
        products=[],
        html_body="",
        standalone=True,
        subseries=None,
        issue_number=None,
        issue_number_display=None,
    )

    indexed = build_people_index([person], [edition])

    assert indexed[0].related_editions == [edition]
