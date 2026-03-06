"""Text processing utilities for HTML generation."""

import re


# Lista polskich spójników i przyimków, które nie powinny zostawać na końcu linii
_ORPHAN_WORDS = {
    # Spójniki
    "a",
    "i",
    "o",
    "u",
    "w",
    "z",
    "k",
    # Przyimki
    "do",
    "na",
    "od",
    "po",
    "za",
    "ze",
    "we",
    "ku",
    # Inne krótkie słowa
    "to",
    "co",
    "że",
    "by",
    "są",
    "je",
    "go",
    "mu",
    "ją",
    "mi",
    "ty",
    "on",
    "my",
    "wy",
}

# Regex pattern: spacja + słowo z listy + spacja (case insensitive)
_ORPHAN_PATTERN = re.compile(
    r"(\s)(" + "|".join(re.escape(w) for w in _ORPHAN_WORDS) + r")(\s)", re.IGNORECASE
)


def _fix_orphans(text: str) -> str:
    """Zamienia spację po spójnikach/przyimkach na &nbsp; aby uniknąć zawieszek.

    Przykład: "W tym tygodniu o godzinie" -> "W&nbsp;tym tygodniu o&nbsp;godzinie"
    """

    def replace_orphan(match: re.Match) -> str:
        before_space = match.group(1)
        word = match.group(2)
        # Zamieniamy spację PO słowie na &nbsp;
        return f"{before_space}{word}&nbsp;"

    # Iterujemy wielokrotnie, bo pattern może się nakładać
    prev_text = None
    while prev_text != text:
        prev_text = text
        text = _ORPHAN_PATTERN.sub(replace_orphan, text)

    return text
