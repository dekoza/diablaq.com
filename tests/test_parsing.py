"""Tests for diablaq_site.parsing module — 14 parsing functions extracted from builder.py."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest


def test_module_imports():
    """Verify all 14 parsing functions can be imported from parsing module."""
    from diablaq_site.parsing import (
        read_markdown_file,
        parse_date,
        parse_optional_date,
        derive_flags,
        coerce_str_list,
        pick_cover,
        parse_image_list,
        as_str,
        parse_buy_links,
        parse_variants,
        parse_creators,
        parse_specs,
    )

    assert callable(read_markdown_file)
    assert callable(parse_date)
    assert callable(parse_optional_date)
    assert callable(derive_flags)
    assert callable(coerce_str_list)
    assert callable(pick_cover)
    assert callable(parse_image_list)
    assert callable(as_str)
    assert callable(parse_buy_links)
    assert callable(parse_variants)
    assert callable(parse_creators)
    assert callable(parse_specs)


# --- read_markdown_file tests ---


def test_read_markdown_file_basic(tmp_path):
    """Test reading a basic Markdown file with frontmatter."""
    from diablaq_site.parsing import read_markdown_file

    test_file = tmp_path / "test.md"
    test_file.write_text(
        """\
---
title: Test Title
slug: test-slug
---

Test body content with **bold**.
"""
    )

    meta, body_html = read_markdown_file(test_file)

    assert isinstance(meta, dict)
    assert meta["title"] == "Test Title"
    assert meta["slug"] == "test-slug"
    assert isinstance(body_html, str)
    assert "<strong>bold</strong>" in body_html


def test_read_markdown_file_fixes_orphans(tmp_path):
    """Test that Polish orphans are fixed with &nbsp; in HTML output."""
    from diablaq_site.parsing import read_markdown_file

    test_file = tmp_path / "orphan.md"
    test_file.write_text(
        """\
---
title: Test
---

To jest a test i example.
"""
    )

    _, body_html = read_markdown_file(test_file)

    # Orphans 'a' and 'i' should be fixed with &nbsp;
    assert " a&nbsp;test" in body_html or "a&nbsp;test" in body_html
    assert " i&nbsp;example" in body_html or "i&nbsp;example" in body_html


def test_read_markdown_file_reports_source_path_for_invalid_frontmatter(tmp_path):
    """Invalid YAML frontmatter should include file path and parser cause."""
    from diablaq_site.parsing import read_markdown_file

    test_file = tmp_path / "broken.md"
    test_file.write_text(
        """\
---
title: Broken example
summary: Invalid: YAML: value
---

Body.
"""
    )

    with pytest.raises(ValueError, match=r"broken\.md") as exc_info:
        read_markdown_file(test_file)

    assert "Nie udało się wczytać frontmatter" in str(exc_info.value)
    assert "did not find expected key" in str(exc_info.value)


# --- parse_date tests ---


def test_parse_date_valid():
    """Test parsing valid YYYY-MM-DD date string."""
    from diablaq_site.parsing import parse_date

    result = parse_date("2024-01-15", source_path=Path("test.md"))

    assert result == date(2024, 1, 15)


def test_parse_date_leap_year():
    """Test parsing leap year date."""
    from diablaq_site.parsing import parse_date

    result = parse_date("2024-02-29", source_path=Path("test.md"))

    assert result == date(2024, 2, 29)


def test_parse_date_invalid_format():
    """Test that invalid date format raises ValueError with source path in message."""
    from diablaq_site.parsing import parse_date

    with pytest.raises(ValueError, match=r"test\.md"):
        parse_date("invalid-date", source_path=Path("test.md"))


def test_parse_date_empty_string():
    """Test that empty string raises ValueError."""
    from diablaq_site.parsing import parse_date

    with pytest.raises(ValueError):
        parse_date("", source_path=Path("test.md"))


def test_parse_date_wrong_separator():
    """Test that wrong separator raises ValueError."""
    from diablaq_site.parsing import parse_date

    with pytest.raises(ValueError):
        parse_date("2024/01/15", source_path=Path("test.md"))


# --- parse_optional_date tests ---


def test_parse_optional_date_none():
    """Test that None returns None."""
    from diablaq_site.parsing import parse_optional_date

    result = parse_optional_date(None, source_path=Path("test.md"))

    assert result is None


def test_parse_optional_date_empty_string():
    """Test that empty string returns None."""
    from diablaq_site.parsing import parse_optional_date

    result = parse_optional_date("", source_path=Path("test.md"))

    assert result is None


def test_parse_optional_date_valid_string():
    """Test that valid date string is parsed correctly."""
    from diablaq_site.parsing import parse_optional_date

    result = parse_optional_date("2024-01-15", source_path=Path("test.md"))

    assert result == date(2024, 1, 15)


def test_parse_optional_date_invalid_string():
    """Test that invalid date string raises ValueError."""
    from diablaq_site.parsing import parse_optional_date

    with pytest.raises(ValueError):
        parse_optional_date("bad-date", source_path=Path("test.md"))


# --- derive_flags tests ---


def test_derive_flags_no_release_date():
    """Test that missing release_date returns (False, False) — neither new nor announcement."""
    from diablaq_site.parsing import derive_flags

    is_new, is_announcement = derive_flags(release_date=None, today=date(2024, 1, 15))

    assert is_new is False
    assert is_announcement is False


def test_derive_flags_future_release():
    """Test that future release_date returns (False, True) — announcement."""
    from diablaq_site.parsing import derive_flags

    is_new, is_announcement = derive_flags(release_date=date(2024, 2, 1), today=date(2024, 1, 15))

    assert is_new is False
    assert is_announcement is True


def test_derive_flags_today_release():
    """Test that release today returns (True, False) — new."""
    from diablaq_site.parsing import derive_flags

    today = date(2024, 1, 15)
    is_new, is_announcement = derive_flags(release_date=today, today=today)

    assert is_new is True
    assert is_announcement is False


def test_derive_flags_within_6_weeks():
    """Test that release within 6 weeks returns (True, False) — new."""
    from diablaq_site.parsing import derive_flags

    release = date(2024, 1, 1)
    today = release + timedelta(weeks=5, days=6)  # Just under 6 weeks

    is_new, is_announcement = derive_flags(release_date=release, today=today)

    assert is_new is True
    assert is_announcement is False


def test_derive_flags_exactly_6_weeks():
    """Test that release exactly 6 weeks ago still counts as new."""
    from diablaq_site.parsing import derive_flags

    release = date(2024, 1, 1)
    today = release + timedelta(weeks=6)

    is_new, is_announcement = derive_flags(release_date=release, today=today)

    assert is_new is True
    assert is_announcement is False


def test_derive_flags_older_than_6_weeks():
    """Test that release older than 6 weeks returns (False, False)."""
    from diablaq_site.parsing import derive_flags

    release = date(2024, 1, 1)
    today = release + timedelta(weeks=6, days=1)

    is_new, is_announcement = derive_flags(release_date=release, today=today)

    assert is_new is False
    assert is_announcement is False


# --- coerce_str_list tests ---


def test_coerce_str_list_none():
    """Test that None returns empty list."""
    from diablaq_site.parsing import coerce_str_list

    result = coerce_str_list(None)

    assert result == []


def test_coerce_str_list_string():
    """Test that single string returns list with one element."""
    from diablaq_site.parsing import coerce_str_list

    result = coerce_str_list("single item")

    assert result == ["single item"]


def test_coerce_str_list_list_of_strings():
    """Test that list of strings is preserved."""
    from diablaq_site.parsing import coerce_str_list

    result = coerce_str_list(["first", "second", "third"])

    assert result == ["first", "second", "third"]


def test_coerce_str_list_list_with_whitespace():
    """Test that whitespace is stripped from list items."""
    from diablaq_site.parsing import coerce_str_list

    result = coerce_str_list(["  first  ", "  second  "])

    assert result == ["first", "second"]


def test_coerce_str_list_empty_items():
    """Test that empty items are filtered out."""
    from diablaq_site.parsing import coerce_str_list

    result = coerce_str_list(["valid", "", "  ", "another"])

    assert result == ["valid", "another"]


# --- pick_cover tests ---


def test_pick_cover_explicit_fields():
    """Test picking cover from explicit cover_image/cover_alt fields."""
    from diablaq_site.parsing import pick_cover

    meta = {"cover_image": "/img/cover.jpg", "cover_alt": "Cover description"}

    image, alt = pick_cover(meta)

    assert image == "/img/cover.jpg"
    assert alt == "Cover description"


def test_pick_cover_no_alt():
    """Test that missing cover_alt returns None for alt."""
    from diablaq_site.parsing import pick_cover

    meta = {"cover_image": "/img/cover.jpg"}

    image, alt = pick_cover(meta)

    assert image == "/img/cover.jpg"
    assert alt is None


def test_pick_cover_from_covers_list():
    """Test picking first cover from covers list."""
    from diablaq_site.parsing import pick_cover

    meta = {
        "covers": [
            {"image": "/img/first.jpg", "alt": "First cover"},
            {"image": "/img/second.jpg", "alt": "Second cover"},
        ]
    }

    image, alt = pick_cover(meta)

    assert image == "/img/first.jpg"
    assert alt == "First cover"


def test_pick_cover_from_covers_no_alt():
    """Test picking cover from covers list when alt is missing."""
    from diablaq_site.parsing import pick_cover

    meta = {"covers": [{"image": "/img/cover.jpg"}]}

    image, alt = pick_cover(meta)

    assert image == "/img/cover.jpg"
    assert alt is None


def test_pick_cover_missing_fields():
    """Test that missing cover fields return (None, None)."""
    from diablaq_site.parsing import pick_cover

    meta = {}

    image, alt = pick_cover(meta)

    assert image is None
    assert alt is None


# --- parse_image_list tests ---


def test_parse_image_list_valid():
    """Test parsing valid image list."""
    from diablaq_site.parsing import parse_image_list

    meta = {
        "covers": [
            {"image": "/img/1.jpg", "alt": "First", "caption": "Caption 1"},
            {"image": "/img/2.jpg", "alt": "Second"},
        ]
    }

    result = parse_image_list(meta, "covers", source_path=Path("test.md"))

    assert len(result) == 2
    assert result[0].image == "/img/1.jpg"
    assert result[0].alt == "First"
    assert result[0].caption == "Caption 1"
    assert result[1].image == "/img/2.jpg"
    assert result[1].alt == "Second"
    assert result[1].caption is None


def test_parse_image_list_missing_key():
    """Test that missing key returns empty list."""
    from diablaq_site.parsing import parse_image_list

    meta = {}

    result = parse_image_list(meta, "covers", source_path=Path("test.md"))

    assert result == []


def test_parse_image_list_not_a_list():
    """Test that non-list value raises ValueError."""
    from diablaq_site.parsing import parse_image_list

    meta = {"covers": "not a list"}

    with pytest.raises(ValueError, match="covers musi być listą"):
        parse_image_list(meta, "covers", source_path=Path("test.md"))


def test_parse_image_list_item_not_dict():
    """Test that non-dict item raises ValueError."""
    from diablaq_site.parsing import parse_image_list

    meta = {"covers": ["not a dict"]}

    with pytest.raises(ValueError, match=r"covers\[0\] musi być dict"):
        parse_image_list(meta, "covers", source_path=Path("test.md"))


def test_parse_image_list_missing_image_field():
    """Test that missing image field raises ValueError."""
    from diablaq_site.parsing import parse_image_list

    meta = {"covers": [{"alt": "Alt text"}]}

    with pytest.raises(ValueError, match=r"covers\[0\] musi mieć image"):
        parse_image_list(meta, "covers", source_path=Path("test.md"))


# --- as_str tests ---


def test_as_str_string():
    """Test converting string returns stripped string."""
    from diablaq_site.parsing import as_str

    result = as_str("  test value  ")

    assert result == "test value"


def test_as_str_integer():
    """Test converting integer to string."""
    from diablaq_site.parsing import as_str

    result = as_str(42)

    assert result == "42"


def test_as_str_empty():
    """Test converting empty string returns empty."""
    from diablaq_site.parsing import as_str

    result = as_str("")

    assert result == ""


# --- parse_buy_links tests ---


def test_parse_buy_links_valid():
    """Test parsing valid buy links."""
    from diablaq_site.parsing import parse_buy_links

    meta = {
        "buy_links": [
            {"label": "Store A", "url": "https://store-a.com"},
            {"label": "Store B", "url": "https://store-b.com"},
        ]
    }

    result = parse_buy_links(meta, source_path=Path("test.md"))

    assert len(result) == 2
    assert result[0].label == "Store A"
    assert result[0].url == "https://store-a.com"
    assert result[1].label == "Store B"
    assert result[1].url == "https://store-b.com"


def test_parse_buy_links_missing():
    """Test that missing buy_links returns empty list."""
    from diablaq_site.parsing import parse_buy_links

    meta = {}

    result = parse_buy_links(meta, source_path=Path("test.md"))

    assert result == []


def test_parse_buy_links_not_list():
    """Test that non-list buy_links raises ValueError."""
    from diablaq_site.parsing import parse_buy_links

    meta = {"buy_links": "not a list"}

    with pytest.raises(ValueError, match="buy_links musi być listą"):
        parse_buy_links(meta, source_path=Path("test.md"))


def test_parse_buy_links_missing_label():
    """Test that missing label raises ValueError."""
    from diablaq_site.parsing import parse_buy_links

    meta = {"buy_links": [{"url": "https://example.com"}]}

    with pytest.raises(ValueError, match=r"buy_links\[0\] musi mieć label i url"):
        parse_buy_links(meta, source_path=Path("test.md"))


def test_parse_buy_links_missing_url():
    """Test that missing url raises ValueError."""
    from diablaq_site.parsing import parse_buy_links

    meta = {"buy_links": [{"label": "Store"}]}

    with pytest.raises(ValueError, match=r"buy_links\[0\] musi mieć label i url"):
        parse_buy_links(meta, source_path=Path("test.md"))


# --- parse_variants tests ---


def test_parse_variants_valid_binding():
    """Test parsing variant with binding field."""
    from diablaq_site.parsing import parse_variants

    meta = {
        "variants": [
            {
                "binding": "miekka",
                "isbn13": "9780306406157",
                "specs": {"Cena": "69,90 zł"},
            }
        ]
    }

    result = parse_variants(meta, source_path=Path("test.md"))

    assert len(result) == 1
    assert result[0].binding == "miekka"
    assert result[0].version is None
    assert result[0].isbn13 == "9780306406157"
    assert result[0].numbered is False
    assert result[0].specs == {"Cena": "69,90 zł"}


def test_parse_variants_valid_version():
    """Test parsing variant with version field."""
    from diablaq_site.parsing import parse_variants

    meta = {
        "variants": [
            {
                "version": "elektroniczna",
                "isbn13": "9780140328721",
                "specs": {"Cena": "29,90 zł"},
            }
        ]
    }

    result = parse_variants(meta, source_path=Path("test.md"))

    assert len(result) == 1
    assert result[0].binding is None
    assert result[0].version == "elektroniczna"
    assert result[0].isbn13 == "9780140328721"


def test_parse_variants_legacy_kind():
    """Test parsing variant with legacy kind field."""
    from diablaq_site.parsing import parse_variants

    meta = {"variants": [{"kind": "twarda", "isbn13": "9780010350616"}]}

    result = parse_variants(meta, source_path=Path("test.md"))

    assert len(result) == 1
    assert result[0].binding == "twarda"
    assert result[0].version is None


def test_parse_variants_legacy_kind_electronic():
    """Test parsing variant with legacy kind=elektroniczna."""
    from diablaq_site.parsing import parse_variants

    meta = {"variants": [{"kind": "elektroniczna", "isbn13": "9780306406157"}]}

    result = parse_variants(meta, source_path=Path("test.md"))

    assert len(result) == 1
    assert result[0].binding is None
    assert result[0].version == "elektroniczna"


def test_parse_variants_invalid_isbn():
    """Test that invalid ISBN-13 checksum raises ValueError."""
    from diablaq_site.parsing import parse_variants

    meta = {"variants": [{"binding": "miekka", "isbn13": "9780306406150"}]}  # Wrong checksum

    with pytest.raises(ValueError, match=r"nie wygląda jak poprawny ISBN-13"):
        parse_variants(meta, source_path=Path("test.md"))


def test_parse_variants_missing_isbn():
    """Test that missing ISBN-13 raises ValueError."""
    from diablaq_site.parsing import parse_variants

    meta = {"variants": [{"binding": "miekka"}]}

    with pytest.raises(ValueError, match=r"isbn13 jest wymagane"):
        parse_variants(meta, source_path=Path("test.md"))


def test_parse_variants_both_binding_and_version():
    """Test that having both binding and version raises ValueError."""
    from diablaq_site.parsing import parse_variants

    meta = {
        "variants": [
            {
                "binding": "miekka",
                "version": "elektroniczna",
                "isbn13": "9780306406157",
            }
        ]
    }

    with pytest.raises(ValueError, match=r"nie może mieć jednocześnie binding i version"):
        parse_variants(meta, source_path=Path("test.md"))


def test_parse_variants_neither_binding_nor_version():
    """Test that missing both binding and version raises ValueError."""
    from diablaq_site.parsing import parse_variants

    meta = {"variants": [{"isbn13": "9780306406157"}]}

    with pytest.raises(ValueError, match=r"musi mieć binding albo version"):
        parse_variants(meta, source_path=Path("test.md"))


def test_parse_variants_limited_print_run():
    """Test parsing variant with limited_print_run."""
    from diablaq_site.parsing import parse_variants

    meta = {
        "variants": [
            {
                "binding": "twarda",
                "isbn13": "9780306406157",
                "limited_print_run": 500,
            }
        ]
    }

    result = parse_variants(meta, source_path=Path("test.md"))

    assert result[0].limited_print_run == 500


def test_parse_variants_numbered_requires_limited_print_run():
    """Test that numbered=true requires limited_print_run."""
    from diablaq_site.parsing import parse_variants

    meta = {"variants": [{"binding": "twarda", "isbn13": "9780306406157", "numbered": True}]}

    with pytest.raises(ValueError, match=r"numbered=true wymaga podania limited_print_run"):
        parse_variants(meta, source_path=Path("test.md"))


def test_parse_variants_with_buy_links():
    """Test parsing variant with buy_links."""
    from diablaq_site.parsing import parse_variants

    meta = {
        "variants": [
            {
                "binding": "miekka",
                "isbn13": "9780306406157",
                "buy_links": [{"label": "Store", "url": "https://example.com"}],
            }
        ]
    }

    result = parse_variants(meta, source_path=Path("test.md"))

    assert len(result[0].buy_links) == 1
    assert result[0].buy_links[0].label == "Store"


def test_parse_variants_fallback_specs():
    """Test that edition-level specs are used as fallback for variants without specs."""
    from diablaq_site.parsing import parse_variants

    meta = {
        "specs": {"Cena": "69,90 zł"},
        "variants": [{"binding": "miekka", "isbn13": "9780306406157"}],
    }

    result = parse_variants(meta, source_path=Path("test.md"))

    assert result[0].specs == {"Cena": "69,90 zł"}


# --- parse_creators tests ---


def test_parse_creators_legacy_list():
    """Test parsing creators as legacy string list."""
    from diablaq_site.parsing import parse_creators

    meta = {"creators": ["Author One", "Author Two"]}

    creators, names = parse_creators(meta, source_path=Path("test.md"))

    assert len(creators) == 2
    assert creators[0].name == "Author One"
    assert creators[0].role is None
    assert creators[0].person_slug is None
    assert names == ["Author One", "Author Two"]


def test_parse_creators_dict_format():
    """Test parsing creators as dict format with role and person_slug."""
    from diablaq_site.parsing import parse_creators

    meta = {
        "creators": [
            {"name": "John Doe", "role": "Autor", "person_slug": "john-doe"},
            {"name": "Jane Smith", "role": "Ilustrator"},
        ]
    }

    creators, names = parse_creators(meta, source_path=Path("test.md"))

    assert len(creators) == 2
    assert creators[0].name == "John Doe"
    assert creators[0].role == "Autor"
    assert creators[0].person_slug == "john-doe"
    assert creators[1].name == "Jane Smith"
    assert creators[1].role == "Ilustrator"
    assert creators[1].person_slug is None
    assert names == ["John Doe", "Jane Smith"]


def test_parse_creators_missing():
    """Test that missing creators returns empty lists."""
    from diablaq_site.parsing import parse_creators

    meta = {}

    creators, names = parse_creators(meta, source_path=Path("test.md"))

    assert creators == []
    assert names == []


def test_parse_creators_missing_name():
    """Test that missing name in dict format raises ValueError."""
    from diablaq_site.parsing import parse_creators

    meta = {"creators": [{"role": "Autor"}]}

    with pytest.raises(ValueError, match=r"creators\[0\] musi mieć name"):
        parse_creators(meta, source_path=Path("test.md"))


def test_parse_creators_not_list():
    """Test that non-list creators raises ValueError."""
    from diablaq_site.parsing import parse_creators

    meta = {"creators": "not a list"}

    with pytest.raises(ValueError, match="creators musi być listą"):
        parse_creators(meta, source_path=Path("test.md"))


# --- parse_specs tests ---


def test_parse_specs_valid():
    """Test parsing valid specs dictionary."""
    from diablaq_site.parsing import parse_specs

    meta = {"specs": {"Cena": "69,90 zł", "Wymiary": "165 x 235 mm"}}

    result = parse_specs(meta)

    assert result == {"Cena": "69,90 zł", "Wymiary": "165 x 235 mm"}


def test_parse_specs_missing():
    """Test that missing specs returns empty dict."""
    from diablaq_site.parsing import parse_specs

    meta = {}

    result = parse_specs(meta)

    assert result == {}


def test_parse_specs_not_dict():
    """Test that non-dict specs returns empty dict."""
    from diablaq_site.parsing import parse_specs

    meta = {"specs": "not a dict"}

    result = parse_specs(meta)

    assert result == {}


def test_parse_specs_filters_none_values():
    """Test that None values are filtered out."""
    from diablaq_site.parsing import parse_specs

    meta = {"specs": {"Cena": "69,90 zł", "Empty": None, "Wymiary": "165 x 235 mm"}}

    result = parse_specs(meta)

    assert result == {"Cena": "69,90 zł", "Wymiary": "165 x 235 mm"}


def test_parse_specs_strips_whitespace():
    """Test that whitespace is stripped from keys and values."""
    from diablaq_site.parsing import parse_specs

    meta = {"specs": {"  Cena  ": "  69,90 zł  ", "Wymiary": "165 x 235 mm"}}

    result = parse_specs(meta)

    assert result == {"Cena": "69,90 zł", "Wymiary": "165 x 235 mm"}
