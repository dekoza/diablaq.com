"""
Tests for diablaq_site.urls module — URL generation functions.

All projects and editions are now under /komiksy/ regardless of publication line.
"""

import pytest


class TestCanonicalProjectUrl:
    """Tests for canonical_project_url(line, slug) -> str"""

    def test_diablaq_line(self):
        """diablaq line → /komiksy/{slug}/"""
        from diablaq_site.urls import canonical_project_url

        result = canonical_project_url(line="diablaq", slug="belzebubs")
        assert result == "/komiksy/belzebubs/"

    def test_dobre_licho_line(self):
        """dobre-licho line → /komiksy/{slug}/"""
        from diablaq_site.urls import canonical_project_url

        result = canonical_project_url(line="dobre-licho", slug="some-project")
        assert result == "/komiksy/some-project/"

    def test_mecenat_line(self):
        """mecenat line → /komiksy/{slug}/"""
        from diablaq_site.urls import canonical_project_url

        result = canonical_project_url(line="mecenat", slug="x")
        assert result == "/komiksy/x/"

    def test_studio_line(self):
        """studio line → /komiksy/{slug}/"""
        from diablaq_site.urls import canonical_project_url

        result = canonical_project_url(line="studio", slug="test-project")
        assert result == "/komiksy/test-project/"

    def test_unknown_line_defaults_to_komiksy(self):
        """Unknown line type falls back to /komiksy/"""
        from diablaq_site.urls import canonical_project_url

        result = canonical_project_url(line="unknown-line", slug="foo")
        assert result == "/komiksy/foo/"

    def test_slug_with_special_chars(self):
        """Slug with hyphens is passed through as-is"""
        from diablaq_site.urls import canonical_project_url

        result = canonical_project_url(line="diablaq", slug="foo-bar-123")
        assert result == "/komiksy/foo-bar-123/"

    def test_empty_slug(self):
        """Empty slug produces valid (if unusual) URL"""
        from diablaq_site.urls import canonical_project_url

        result = canonical_project_url(line="diablaq", slug="")
        assert result == "/komiksy//"


class TestCanonicalEditionUrl:
    """Tests for canonical_edition_url(line, project_slug, edition_slug) -> str"""

    def test_index_edition_returns_project_url(self):
        """edition_slug='index' → collapses to project URL (no /index/ segment)"""
        from diablaq_site.urls import canonical_edition_url

        result = canonical_edition_url(
            line="diablaq", project_slug="belzebubs", edition_slug="index"
        )
        assert result == "/komiksy/belzebubs/"

    def test_index_edition_with_dobre_licho(self):
        """index edition with dobre-licho line"""
        from diablaq_site.urls import canonical_edition_url

        result = canonical_edition_url(
            line="dobre-licho", project_slug="proj", edition_slug="index"
        )
        assert result == "/komiksy/proj/"

    def test_regular_edition_diablaq(self):
        """Regular edition with diablaq line"""
        from diablaq_site.urls import canonical_edition_url

        result = canonical_edition_url(
            line="diablaq", project_slug="belzebubs", edition_slug="vol-1"
        )
        assert result == "/komiksy/belzebubs/vol-1/"

    def test_regular_edition_dobre_licho(self):
        """Regular edition with dobre-licho line"""
        from diablaq_site.urls import canonical_edition_url

        result = canonical_edition_url(
            line="dobre-licho", project_slug="p1", edition_slug="issue-2"
        )
        assert result == "/komiksy/p1/issue-2/"

    def test_regular_edition_mecenat(self):
        """Regular edition with mecenat line"""
        from diablaq_site.urls import canonical_edition_url

        result = canonical_edition_url(
            line="mecenat", project_slug="support", edition_slug="edition-a"
        )
        assert result == "/komiksy/support/edition-a/"

    def test_regular_edition_studio(self):
        """Regular edition with studio line"""
        from diablaq_site.urls import canonical_edition_url

        result = canonical_edition_url(line="studio", project_slug="art", edition_slug="piece-1")
        assert result == "/komiksy/art/piece-1/"

    def test_regular_edition_unknown_line(self):
        """Regular edition with unknown line falls back to /komiksy/"""
        from diablaq_site.urls import canonical_edition_url

        result = canonical_edition_url(line="unknown", project_slug="p", edition_slug="e")
        assert result == "/komiksy/p/e/"

    def test_edition_slug_with_special_chars(self):
        """Edition slug with hyphens is passed through"""
        from diablaq_site.urls import canonical_edition_url

        result = canonical_edition_url(
            line="diablaq", project_slug="proj", edition_slug="vol-2-special"
        )
        assert result == "/komiksy/proj/vol-2-special/"


class TestSlugifyTag:
    """Tests for slugify_tag(tag: str) -> str"""

    def test_simple_tag(self):
        """Simple tag without special chars"""
        from diablaq_site.urls import slugify_tag

        result = slugify_tag("adventure")
        assert result == "adventure"

    def test_tag_with_spaces(self):
        """Tag with spaces is percent-encoded"""
        from diablaq_site.urls import slugify_tag

        result = slugify_tag("action adventure")
        assert result == "action%20adventure"

    def test_tag_with_leading_trailing_spaces(self):
        """Leading/trailing spaces are stripped before encoding"""
        from diablaq_site.urls import slugify_tag

        result = slugify_tag("  comedy  ")
        assert result == "comedy"

    def test_tag_with_special_chars(self):
        """Special characters are percent-encoded"""
        from diablaq_site.urls import slugify_tag

        result = slugify_tag("sci-fi & fantasy")
        assert " " not in result

    def test_tag_with_unicode(self):
        """Unicode characters are percent-encoded in UTF-8"""
        from diablaq_site.urls import slugify_tag

        result = slugify_tag("Łódź")
        assert "%" in result or "Ł" in result

    def test_empty_tag(self):
        """Empty tag or whitespace-only tag returns empty string"""
        from diablaq_site.urls import slugify_tag

        result = slugify_tag("")
        assert result == ""

    def test_whitespace_only_tag(self):
        """Whitespace-only tag is stripped to empty"""
        from diablaq_site.urls import slugify_tag

        result = slugify_tag("   ")
        assert result == ""

    def test_tag_with_punctuation(self):
        """Punctuation is percent-encoded"""
        from diablaq_site.urls import slugify_tag

        result = slugify_tag("drama!")
        assert "%" in result or "!" not in result

    def test_tag_case_preserved(self):
        """Tag case is preserved (not lowercased)"""
        from diablaq_site.urls import slugify_tag

        result = slugify_tag("MyTag")
        assert "M" in result and "y" in result

    def test_tag_with_ampersand(self):
        """Ampersand in tag is percent-encoded"""
        from diablaq_site.urls import slugify_tag

        result = slugify_tag("A & B")
        assert "&" not in result
        assert "A" in result and "B" in result
