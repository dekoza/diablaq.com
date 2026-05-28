"""Data models for diablaq site builder."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


_PRODUCT_FORMAT_LABELS = {
    "zeszyt": "Zeszyt",
    "miekka": "Miękka",
    "twarda": "Twarda",
    "ebook": "E-book",
}


@dataclass(frozen=True)
class BuyLink:
    label: str
    url: str


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
class EditionCover:
    id: str
    label: str | None
    image: str
    alt: str | None
    artist_name: str | None
    person_slug: str | None


@dataclass(frozen=True)
class EditionProduct:
    format: str
    cover_id: str | None
    label: str | None
    isbn13: str | None
    ean2: str | None
    price: str | None
    limited: bool
    numbered_copies: int | None
    buy_links: list[BuyLink]
    specs: dict[str, str]

    @property
    def format_label(self) -> str:
        return _PRODUCT_FORMAT_LABELS.get(self.format, self.format)


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
    primary_cover: EditionCover | None
    cover_aspect_class: str
    alternate_covers: list[EditionCover]
    previews: list[ImageRef]
    creators: list[Creator]
    creator_names: list[str]
    edition_specs: dict[str, str]
    products: list[EditionProduct]
    html_body: str
    standalone: bool
    subseries: str | None
    issue_number: int | None
    issue_number_display: str | None
    featured: bool = False
    legacy_path: str | None = None
    featured_img: str | None = None
    featured_img_alt: str | None = None
    featured_order: int = 0
    featured_duration: int = 10
    summary: str | None = None

    @property
    def hero_image(self) -> str | None:
        return self.featured_img or self.cover_image

    @property
    def hero_image_alt(self) -> str | None:
        return self.featured_img_alt or self.cover_alt

    @property
    def hero_slide_class(self) -> str:
        if self.featured_img:
            return "hero-slide--wide"
        if self.cover_aspect_class == "cover--tall":
            return "hero-slide--poster"
        return "hero-slide--wide"

    @property
    def cover_image(self) -> str | None:
        if self.primary_cover is None:
            return None
        return self.primary_cover.image

    @property
    def cover_alt(self) -> str | None:
        if self.primary_cover is None:
            return None
        return self.primary_cover.alt

    @property
    def all_covers(self) -> tuple[EditionCover, ...]:
        covers: list[EditionCover] = []
        if self.primary_cover is not None:
            covers.append(self.primary_cover)
        covers.extend(self.alternate_covers)
        return tuple(covers)

    def cover_by_id(self, cover_id: str | None) -> EditionCover | None:
        normalized = (cover_id or "primary").strip() or "primary"
        if normalized == "primary":
            return self.primary_cover
        for cover in self.alternate_covers:
            if cover.id == normalized:
                return cover
        return None

    @property
    def cover_contributors(self) -> tuple[Creator, ...]:
        contributors: list[Creator] = []
        for cover in self.all_covers:
            contributor_name = cover.artist_name or cover.person_slug
            if not contributor_name:
                continue
            role = "Okładka"
            if cover.label:
                role = f"Okładka {cover.label.lower()}"
            contributors.append(
                Creator(
                    role=role,
                    name=contributor_name,
                    person_slug=cover.person_slug,
                )
            )
        return tuple(contributors)

    @property
    def all_contributors(self) -> tuple[Creator, ...]:
        return tuple([*self.creators, *self.cover_contributors])

    def product_title(self, product: EditionProduct) -> str:
        parts: list[str] = []
        cover = self.cover_by_id(product.cover_id)
        if product.label:
            parts.append(product.label)
        elif cover and cover.label and (len(self.products) > 1 or cover.id != "primary"):
            parts.append(cover.label)

        format_label = product.format_label
        if len(self.products) > 1 or not parts:
            parts.append(format_label)

        deduped: list[str] = []
        for part in parts:
            if part and part not in deduped:
                deduped.append(part)
        return " · ".join(deduped) or "Wersja"


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
    latest_cover_image: str | None = None
    latest_cover_aspect_class: str = "cover--standard"


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
