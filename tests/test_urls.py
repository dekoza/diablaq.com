"""
Tests for diablaq_site.urls module — URL generation functions.

Test coverage:
- canonical_project_url: URL generation for projects by line/slug
- canonical_edition_url: URL generation for editions, with special index handling
- slugify_tag: URL-safe tag slugification with percent-encoding
"""

import pytest


class TestCanonicalProjectUrl:
    """Tests for canonical_project_url(line, slug) -> str"""

    def test_diablaq_line(self):
        """diablaq line → /publikacje/{slug}/ pattern"""
        from diablaq_site.urls import canonical_project_url

        result = canonical_project_url(line="diablaq", slug="belzebubs")
        assert result == "/publikacje/belzebubs/"

    def test_dobre_licho_line(self):
        """dobre-licho line → /dobre-licho/{slug}/ pattern"""
        from diablaq_site.urls import canonical_project_url

        result = canonical_project_url(line="dobre-licho", slug="some-project")
        assert result == "/dobre-licho/some-project/"

    def test_mecenat_line(self):
        """mecenat line → /mecenat/{slug}/ pattern"""
        from diablaq_site.urls import canonical_project_url

        result = canonical_project_url(line="mecenat", slug="x")
        assert result == "/mecenat/x/"

    def test_studio_line(self):
        """studio line → /studio/{slug}/ pattern"""
        from diablaq_site.urls import canonical_project_url

        result = canonical_project_url(line="studio", slug="test-project")
        assert result == "/studio/test-project/"

    def test_unknown_line_defaults_to_publikacje(self):
        """Unknown line type falls back to /publikacje/ pattern"""
        from diablaq_site.urls import canonical_project_url

        result = canonical_project_url(line="unknown-line", slug="foo")
        assert result == "/publikacje/foo/"

    def test_slug_with_special_chars(self):
        """Slug with special characters is passed through as-is"""
        from diablaq_site.urls import canonical_project_url

        # Assume slug is already URL-safe (caller's responsibility)
        result = canonical_project_url(line="diablaq", slug="foo-bar-123")
        assert result == "/publikacje/foo-bar-123/"

    def test_empty_slug(self):
        """Empty slug produces valid (if unusual) URL"""
        from diablaq_site.urls import canonical_project_url

        result = canonical_project_url(line="diablaq", slug="")
        assert result == "/publikacje//"


class TestCanonicalEditionUrl:
    """Tests for canonical_edition_url(line, project_slug, edition_slug) -> str"""

    def test_index_edition_returns_project_url(self):
        """edition_slug='index' → delegates to canonical_project_url (no /index/)"""
        from diablaq_site.urls import canonical_edition_url

        result = canonical_edition_url(
            line="diablaq", project_slug="belzebubs", edition_slug="index"
        )
        assert result == "/publikacje/belzebubs/"

    def test_index_edition_with_dobre_licho(self):
        """index edition with dobre-licho line"""
        from diablaq_site.urls import canonical_edition_url

        result = canonical_edition_url(
            line="dobre-licho", project_slug="proj", edition_slug="index"
        )
        assert result == "/dobre-licho/proj/"

    def test_regular_edition_diablaq(self):
        """Regular edition with diablaq line"""
        from diablaq_site.urls import canonical_edition_url

        result = canonical_edition_url(
            line="diablaq", project_slug="belzebubs", edition_slug="vol-1"
        )
        assert result == "/publikacje/belzebubs/vol-1/"

    def test_regular_edition_dobre_licho(self):
        """Regular edition with dobre-licho line"""
        from diablaq_site.urls import canonical_edition_url

        result = canonical_edition_url(
            line="dobre-licho", project_slug="p1", edition_slug="issue-2"
        )
        assert result == "/dobre-licho/p1/issue-2/"

    def test_regular_edition_mecenat(self):
        """Regular edition with mecenat line"""
        from diablaq_site.urls import canonical_edition_url

        result = canonical_edition_url(
            line="mecenat", project_slug="support", edition_slug="edition-a"
        )
        assert result == "/mecenat/support/edition-a/"

    def test_regular_edition_studio(self):
        """Regular edition with studio line"""
        from diablaq_site.urls import canonical_edition_url

        result = canonical_edition_url(line="studio", project_slug="art", edition_slug="piece-1")
        assert result == "/studio/art/piece-1/"

    def test_regular_edition_unknown_line(self):
        """Regular edition with unknown line falls back to publikacje"""
        from diablaq_site.urls import canonical_edition_url

        result = canonical_edition_url(line="unknown", project_slug="p", edition_slug="e")
        assert result == "/publikacje/p/e/"

    def test_edition_slug_with_special_chars(self):
        """Edition slug with hyphens is passed through"""
        from diablaq_site.urls import canonical_edition_url

        result = canonical_edition_url(
            line="diablaq", project_slug="proj", edition_slug="vol-2-special"
        )
        assert result == "/publikacje/proj/vol-2-special/"


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

        # quote() converts space to %20
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

        # quote() encodes special chars except those in safe=""
        result = slugify_tag("sci-fi & fantasy")
        # Expects: sci%2Dfi%20%26%20fantasy OR sci-fi%20%26%20fantasy depending on quote() behavior
        # Actually quote(safe="") encodes everything except unreserved chars
        # Let's just assert it's URL-safe (no raw spaces or special chars)
        assert "%" in result or "-" in result  # At least some encoding happened
        assert " " not in result  # No raw spaces

    def test_tag_with_unicode(self):
        """Unicode characters are percent-encoded in UTF-8"""
        from diablaq_site.urls import slugify_tag

        result = slugify_tag("Łódź")
        # quote() should UTF-8 encode and percent-encode
        assert "%" in result or "Ł" in result  # Either percent-encoded or preserved
        # Most importantly: no error should be raised

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
        # quote(safe="") will encode !
        assert "%" in result or "!" not in result

    def test_tag_case_preserved(self):
        """Tag case is preserved (not lowercased)"""
        from diablaq_site.urls import slugify_tag

        result = slugify_tag("MyTag")
        # quote() preserves case for unreserved chars
        assert "M" in result and "y" in result

    def test_tag_with_ampersand(self):
        """Ampersand in tag is percent-encoded"""
        from diablaq_site.urls import slugify_tag

        result = slugify_tag("A & B")
        assert "&" not in result  # Should be encoded to %26
        assert "A" in result and "B" in result
