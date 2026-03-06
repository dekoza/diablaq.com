"""Validation utilities: ISBN-13 checksum and edition variant kinds."""


def _is_valid_isbn13(isbn13: str) -> bool:
    """Walidacja checksum ISBN-13.

    Zasada: (suma cyfr na pozycjach parzystych*3 + nieparzystych) % 10 == 0.
    """

    if len(isbn13) != 13 or not isbn13.isdigit():
        return False

    total = 0
    for idx, ch in enumerate(isbn13):
        digit = int(ch)
        total += digit * 3 if (idx % 2 == 1) else digit

    return total % 10 == 0


_ALLOWED_BINDINGS = {"miekka", "twarda"}
_ALLOWED_VERSIONS = {"elektroniczna"}
_ALLOWED_VARIANT_KINDS = _ALLOWED_BINDINGS | _ALLOWED_VERSIONS
