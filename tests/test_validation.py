"""Tests for validation module: ISBN-13 checksum and variant kinds."""

import pytest
from diablaq_site.validation import _is_valid_isbn13, _ALLOWED_VARIANT_KINDS


class TestVariantKinds:
    """Test _ALLOWED_VARIANT_KINDS constant."""

    def test_variant_kinds_contains_required_bindings(self):
        """ALLOWED_VARIANT_KINDS should include 'miekka' and 'twarda'."""
        assert "miekka" in _ALLOWED_VARIANT_KINDS
        assert "twarda" in _ALLOWED_VARIANT_KINDS

    def test_variant_kinds_contains_required_versions(self):
        """ALLOWED_VARIANT_KINDS should include 'elektroniczna'."""
        assert "elektroniczna" in _ALLOWED_VARIANT_KINDS

    def test_variant_kinds_is_set(self):
        """ALLOWED_VARIANT_KINDS should be a set."""
        assert isinstance(_ALLOWED_VARIANT_KINDS, set)

    def test_variant_kinds_exactly_three_items(self):
        """ALLOWED_VARIANT_KINDS should contain exactly 3 items."""
        assert len(_ALLOWED_VARIANT_KINDS) == 3


class TestIsValidIsbn13:
    """Test _is_valid_isbn13 function with comprehensive ISBN-13 validation."""

    # Valid ISBNs (real-world examples with correct checksums)
    def test_valid_isbn13_basic(self):
        """Valid ISBN-13: 9780306406157 (real book ISBN)."""
        assert _is_valid_isbn13("9780306406157") is True

    def test_valid_isbn13_second_example(self):
        """Valid ISBN-13: 9780010350616 (has correct checksum)."""
        assert _is_valid_isbn13("9780010350616") is True



    def test_valid_isbn13_third_example(self):
        """Valid ISBN-13: 9780140328721 (real book ISBN)."""
        assert _is_valid_isbn13("9780140328721") is True

    def test_valid_isbn13_with_leading_zeros(self):
        """Valid ISBN-13 with leading zeros preserved: 9780000000002."""
        # Checksum: 9*1+7*3+8*1+0*3+0*1+0*3+0*1+0*3+0*1+0*3+0*1+0*3+2 = 9+21+8+0+0+0+0+0+0+0+0+0+2 = 40 % 10 == 0
        assert _is_valid_isbn13("9780000000002") is True

    # Invalid checksums
    def test_invalid_isbn13_wrong_checksum(self):
        """Invalid ISBN-13: wrong checksum digit (9780306406158 vs 9780306406157)."""
        assert _is_valid_isbn13("9780306406158") is False

    def test_invalid_isbn13_another_wrong_checksum(self):
        """Invalid ISBN-13: wrong checksum (9780060930297 vs 9780060930296)."""
        assert _is_valid_isbn13("9780060930297") is False

    # Length validation
    def test_invalid_isbn13_too_short(self):
        """Invalid: too short (12 digits instead of 13)."""
        assert _is_valid_isbn13("978030640615") is False

    def test_invalid_isbn13_too_long(self):
        """Invalid: too long (14 digits instead of 13)."""
        assert _is_valid_isbn13("97803064061577") is False

    def test_invalid_isbn13_empty_string(self):
        """Invalid: empty string."""
        assert _is_valid_isbn13("") is False

    # Non-digit characters
    def test_invalid_isbn13_with_hyphens(self):
        """Invalid: ISBN-13 with hyphens not allowed (978-03-06-40615-7)."""
        assert _is_valid_isbn13("978-03-06-40615-7") is False

    def test_invalid_isbn13_with_spaces(self):
        """Invalid: ISBN-13 with spaces not allowed."""
        assert _is_valid_isbn13("978 030 640 6157") is False

    def test_invalid_isbn13_with_letters(self):
        """Invalid: ISBN-13 with letters not allowed."""
        assert _is_valid_isbn13("97803064061A7") is False

    # Edge cases
    def test_invalid_isbn13_all_zeros(self):
        """Invalid: all zeros (0000000000000)."""
        # 0*1+0*3+0*1+0*3+0*1+0*3+0*1+0*3+0*1+0*3+0*1+0*3+0 = 0, 0 % 10 == 0 → actually valid!
        assert _is_valid_isbn13("0000000000000") is True

    def test_invalid_isbn13_all_nines(self):
        """Invalid checksum: all nines (9999999999999)."""
        # 9*1+9*3+9*1+9*3+9*1+9*3+9*1+9*3+9*1+9*3+9*1+9*3+9 = 9+27+9+27+9+27+9+27+9+27+9+27+9 = 162 % 10 != 0
        assert _is_valid_isbn13("9999999999999") is False

    def test_valid_isbn13_single_digit_numbers(self):
        """Valid ISBN-13 with pattern of single digits: 1234567890128."""
        # Checksum: 1*1+2*3+3*1+4*3+5*1+6*3+7*1+8*3+9*1+0*3+1*1+2*3+8 = 1+6+3+12+5+18+7+24+9+0+1+6+8 = 100 % 10 == 0 → valid
        assert _is_valid_isbn13("1234567890128") is True

    # None/type checking
    def test_invalid_isbn13_none_type(self):
        """Invalid: None type should be handled gracefully."""
        with pytest.raises((TypeError, AttributeError)):
            _is_valid_isbn13(None)

    def test_invalid_isbn13_integer_type(self):
        """Invalid: integer type should be handled gracefully."""
        with pytest.raises(TypeError):
            _is_valid_isbn13(9780306406157)
