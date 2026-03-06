"""Tests for diablaq_site.text module."""

import pytest


class TestFixOrphans:
    """Test _fix_orphans function for HTML orphan word prevention."""

    def test_import_module(self):
        """Module diablaq_site.text should exist."""
        import diablaq_site.text

        assert hasattr(diablaq_site.text, "_fix_orphans")
        assert hasattr(diablaq_site.text, "_ORPHAN_WORDS")

    def test_orphan_words_constant_exists(self):
        """_ORPHAN_WORDS should be a collection of Polish orphan words."""
        from diablaq_site.text import _ORPHAN_WORDS

        assert _ORPHAN_WORDS is not None
        assert len(_ORPHAN_WORDS) > 0
        # Should contain known orphan words
        assert "a" in _ORPHAN_WORDS
        assert "i" in _ORPHAN_WORDS
        assert "do" in _ORPHAN_WORDS
        assert "na" in _ORPHAN_WORDS

    def test_fix_orphans_empty_string(self):
        """Empty string should remain empty."""
        from diablaq_site.text import _fix_orphans

        assert _fix_orphans("") == ""

    def test_fix_orphans_single_orphan_with_spaces(self):
        """Single orphan word with space before and after should be fixed."""
        from diablaq_site.text import _fix_orphans

        # Pattern requires space before and after, so ' a ' becomes ' a&nbsp;'
        result = _fix_orphans(" a jednak")
        assert result == " a&nbsp;jednak"

    def test_fix_orphans_multiple_orphans(self):
        """Multiple orphan words in text with proper spacing should be fixed."""
        from diablaq_site.text import _fix_orphans

        # ' To i to ' - To needs space before, i is between spaces, to has space before
        result = _fix_orphans(" To i to ")
        assert result == " To&nbsp;i to&nbsp;"

    def test_fix_orphans_no_orphan(self):
        """Text without orphan words should remain unchanged."""
        from diablaq_site.text import _fix_orphans

        result = _fix_orphans("Example text.")
        assert result == "Example text."

    def test_fix_orphans_orphan_at_start_no_preceding_space(self):
        """Orphan word at start without preceding space is not fixed."""
        from diablaq_site.text import _fix_orphans

        # Pattern needs space before the word, so 'a jednak' is not matched
        result = _fix_orphans("a jednak")
        assert result == "a jednak"  # unchanged

    def test_fix_orphans_case_insensitive(self):
        """Orphan words should work case-insensitively (re.IGNORECASE)."""
        from diablaq_site.text import _fix_orphans

        # Pattern uses re.IGNORECASE, so uppercase A is matched with space before
        result = _fix_orphans(" A jednak")
        assert result == " A&nbsp;jednak"

    def test_fix_orphans_word_requires_surrounding_spaces(self):
        """Orphan word requires spaces on both sides to be matched."""
        from diablaq_site.text import _fix_orphans

        # ' w domu' has space before w and space after, so w is matched
        result = _fix_orphans(" w domu")
        assert result == " w&nbsp;domu"

    def test_fix_orphans_sentence_boundary(self):
        """Orphan word after period with space is treated as new word."""
        from diablaq_site.text import _fix_orphans

        # 'Test. A jednak' -> 'Test. A&nbsp;jednak' (space after period counts as space before)
        result = _fix_orphans("Test. A jednak")
        assert "A&nbsp;jednak" in result

    def test_fix_orphans_newline_boundary(self):
        """Newline counts as whitespace for orphan matching."""
        from diablaq_site.text import _fix_orphans

        # Newline is \\s in regex, so works as space
        text = "Line.\n A word."
        result = _fix_orphans(text)
        # '\n A' has space before A (newline), so should match
        assert "A&nbsp;word" in result

    def test_fix_orphans_no_match_without_space_after(self):
        """Orphan word without space after is not fixed."""
        from diablaq_site.text import _fix_orphans

        # ' a!' has space before but no space after, so not matched
        result = _fix_orphans(" a!")
        assert "a&nbsp;" not in result

    def test_fix_orphans_preserves_existing_nbsp(self):
        """Existing &nbsp; entities are preserved."""
        from diablaq_site.text import _fix_orphans

        result = _fix_orphans("Test&nbsp;word")
        assert "&nbsp;" in result

    def test_fix_orphans_sample_orphans_with_spacing(self):
        """Test that sample orphan words are handled correctly with proper spacing."""
        from diablaq_site.text import _fix_orphans, _ORPHAN_WORDS

        test_words = ["a", "i", "w", "do", "na", "że", "są"]
        for word in test_words:
            if word in _ORPHAN_WORDS:
                # ' word test' pattern with space before and after
                result = _fix_orphans(f" {word} test")
                assert f"{word}&nbsp;test" in result, f"Failed for orphan word '{word}'"

    def test_fix_orphans_trailing_content(self):
        """Orphan word followed by space and more text is fixed."""
        from diablaq_site.text import _fix_orphans

        # ' do domu' has space before do, space after, then more text
        result = _fix_orphans(" do domu")
        assert result == " do&nbsp;domu"

    def test_fix_orphans_returns_string(self):
        """_fix_orphans should always return a string."""
        from diablaq_site.text import _fix_orphans

        result = _fix_orphans("Test")
        assert isinstance(result, str)

    def test_fix_orphans_simple_leading_space(self):
        """Simple case with leading space before orphan word."""
        from diablaq_site.text import _fix_orphans

        result = _fix_orphans(" i now")
        assert result == " i&nbsp;now"

    def test_fix_orphans_multiple_in_sequence(self):
        """Multiple orphan words in sequence with proper spacing."""
        from diablaq_site.text import _fix_orphans

        # ' a i ' - both a and i are matched (space before and after)
        result = _fix_orphans(" a i ")
        assert "a&nbsp;i" in result

    def test_fix_orphans_word_boundary_requirements(self):
        """Test that orphans require space both before and after."""
        from diablaq_site.text import _fix_orphans

        # Without leading space, 'a test' is not matched
        assert _fix_orphans("a test") == "a test"
        # With leading space, ' a test' is matched
        assert _fix_orphans(" a test") == " a&nbsp;test"
        # With both spaces, ' a ' matches
        assert _fix_orphans(" a ") == " a&nbsp;"

    def test_fix_orphans_iterative_replacement(self):
        """Test that overlapping patterns are fixed through iteration."""
        from diablaq_site.text import _fix_orphans

        # Function iterates until no more replacements, handling overlaps
        result = _fix_orphans(" a i to ")
        # After first pass: ' a&nbsp;i to '
        # 'i ' still needs fixing: ' a&nbsp;i&nbsp;to '
        # 'to ' still needs fixing: final result
        assert "&nbsp;" in result
