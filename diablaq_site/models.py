"""Data models for diablaq site builder."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class BuyLink:
    label: str
    url: str


@dataclass(frozen=True)
class EditionVariant:
    """Pojedynczy wariant wydania bez osobnej podstrony."""

    binding: str | None  # miekka | twarda
    version: str | None  # elektroniczna
    isbn13: str
    limited_print_run: int | None
    numbered: bool
    buy_links: list[BuyLink]
    specs: dict[str, str]


@dataclass(frozen=True)
class Creator:
    role: str | None
    name: str
    person_slug: str | None


@dataclass(frozen=True)
class ImageRef:
    image: str
    alt: str | None
    caption: str | None


@dataclass(frozen=True)
class Edition:
    url: str
    title: str
    project_slug: str
    release: str | None
    release_date: date
    is_new: bool
    is_announcement: bool
    presale_url: str | None
    legacy_anchor: str | None
    cover_image: str | None
    cover_alt: str | None
    cover_aspect_class: str
    covers: list[ImageRef]
    previews: list[ImageRef]
    creators: list[Creator]
    creator_names: list[str]
    specs: dict[str, str]
    buy_links: list[BuyLink]
    variants: list[EditionVariant]
    html_body: str
    standalone: bool
    subseries: str | None
    issue_number: int | None
    issue_number_display: str | None
    featured: bool = False
    legacy_path: str | None = None


@dataclass(frozen=True)
class Project:
    slug: str
    title: str
    line: str
    summary: str | None
    legacy_path: str | None
    url: str
    legacy_landing: bool
    cover_image: str | None
    cover_aspect_class: str
    html_body: str
    draft: bool = False
    kind: str = "title"
    universe_slug: str | None = None


@dataclass(frozen=True)
class Person:
    slug: str
    name: str | None
    photo: str | None
    photo_thumb: str | None
    html_bio: str
    related_editions: list[Edition]
    credit_name: str | None = None

    @property
    def display_name(self) -> str:
        return self.name or self.credit_name or self.slug

    @property
    def publication_name(self) -> str:
        return self.credit_name or self.name or self.slug

    @property
    def credit_label(self) -> str | None:
        if self.name and self.credit_name and self.credit_name != self.name:
            return f"Publikuje jako: {self.credit_name}"
        if not self.name and self.credit_name:
            return f"Pseudonim artystyczny: {self.credit_name}"
        return None

    @property
    def match_names(self) -> tuple[str, ...]:
        names: list[str] = []
        for value in (self.name, self.credit_name):
            normalized = (value or "").strip().lower()
            if normalized and normalized not in names:
                names.append(normalized)
        return tuple(names)


@dataclass(frozen=True)
class Page:
    slug: str
    title: str
    html_body: str


@dataclass(frozen=True)
class BlogPost:
    url: str
    slug: str
    title: str
    date: date
    summary: str | None
    cover_image: str | None
    cover_alt: str | None
    tags: list[str]
    html_body: str
