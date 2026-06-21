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
class EditionHero:
    """Computed presentation aspect of an Edition — covers, heroes, contributors.

    Built once at Edition construction time from identity fields.
    """
    hero_image: str | None
    hero_image_alt: str | None
    hero_slide_class: str
    cover_image: str | None
    cover_alt: str | None
    all_covers: tuple[EditionCover, ...]
    cover_contributors: tuple[Creator, ...]

    def cover_by_id(self, cover_id: str | None) -> EditionCover | None:
        normalized = (cover_id or "primary").strip() or "primary"
        if normalized == "primary":
            return self.all_covers[0] if self.all_covers else None
        for cover in self.all_covers:
            if cover.id == normalized:
                return cover
        return None


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
    hero: EditionHero = None  # type: ignore[assignment] — set in __post_init__

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "hero",
            Edition._build_hero(
                primary_cover=self.primary_cover,
                alternate_covers=self.alternate_covers,
                cover_aspect_class=self.cover_aspect_class,
                featured_img=self.featured_img,
                featured_img_alt=self.featured_img_alt,
                creators=self.creators,
            ),
        )

    @property
    def all_contributors(self) -> tuple[Creator, ...]:
        return tuple([*self.creators, *self.hero.cover_contributors])

    def product_title(self, product: EditionProduct) -> str:
        parts: list[str] = []
        cover = self.hero.cover_by_id(product.cover_id)
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

    @staticmethod
    def _build_hero(
        primary_cover: EditionCover | None,
        alternate_covers: list[EditionCover],
        cover_aspect_class: str,
        featured_img: str | None,
        featured_img_alt: str | None,
        creators: list[Creator],
    ) -> EditionHero:
        cover_image = primary_cover.image if primary_cover is not None else None
        cover_alt = primary_cover.alt if primary_cover is not None else None
        hero_image = featured_img or cover_image
        hero_image_alt = featured_img_alt or cover_alt

        if featured_img:
            hero_slide_class = "hero-slide--wide"
        elif cover_aspect_class == "cover--tall":
            hero_slide_class = "hero-slide--poster"
        else:
            hero_slide_class = "hero-slide--wide"

        covers_list: list[EditionCover] = []
        if primary_cover is not None:
            covers_list.append(primary_cover)
        covers_list.extend(alternate_covers)
        all_covers = tuple(covers_list)

        cover_contributors: list[Creator] = []
        for cover in all_covers:
            contributor_name = cover.artist_name or cover.person_slug
            if not contributor_name:
                continue
            role = "Okładka"
            if cover.label:
                role = f"Okładka {cover.label.lower()}"
            cover_contributors.append(
                Creator(role=role, name=contributor_name, person_slug=cover.person_slug)
            )

        return EditionHero(
            hero_image=hero_image,
            hero_image_alt=hero_image_alt,
            hero_slide_class=hero_slide_class,
            cover_image=cover_image,
            cover_alt=cover_alt,
            all_covers=all_covers,
            cover_contributors=tuple(cover_contributors),
        )


@dataclass(frozen=True)
class Project:
    slug: str
    title: str
    line: str
    summary: str | None
    legacy_path: str | None
    url: str

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
