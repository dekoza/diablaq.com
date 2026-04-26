"""Tests for diablaq_site.models dataclasses."""

from __future__ import annotations

from datetime import date

import pytest

from diablaq_site.models import (
    BlogPost,
    BuyLink,
    Creator,
    Edition,
    EditionCover,
    EditionProduct,
    ImageRef,
    Page,
    Person,
    Project,
)


class TestBuyLink:
    def test_instantiation(self) -> None:
        link = BuyLink(label="Amazon", url="https://amazon.com")
        assert link.label == "Amazon"
        assert link.url == "https://amazon.com"

    def test_is_frozen(self) -> None:
        link = BuyLink(label="Test", url="http://test.com")
        with pytest.raises(Exception):
            link.label = "Changed"


class TestEditionCover:
    def test_instantiation(self) -> None:
        cover = EditionCover(
            id="primary",
            label="Standardowa",
            image="cover.jpg",
            alt="Cover alt",
            artist_name="Artist",
            person_slug="artist-slug",
        )
        assert cover.id == "primary"
        assert cover.label == "Standardowa"
        assert cover.artist_name == "Artist"

    def test_is_frozen(self) -> None:
        cover = EditionCover(
            id="primary",
            label=None,
            image="cover.jpg",
            alt=None,
            artist_name=None,
            person_slug=None,
        )
        with pytest.raises(Exception):
            cover.image = "other.jpg"


class TestEditionProduct:
    def test_instantiation(self) -> None:
        product = EditionProduct(
            format="twarda",
            cover_id="primary",
            label="Limitowana",
            isbn13="9788394123456",
            ean2="02",
            price="69,90 zł",
            limited=True,
            numbered_copies=333,
            buy_links=[BuyLink(label="Sklep", url="https://example.com")],
            specs={"Oprawa": "ze skrzydełkami"},
        )
        assert product.format == "twarda"
        assert product.format_label == "Twarda"
        assert product.numbered_copies == 333

    def test_is_frozen(self) -> None:
        product = EditionProduct(
            format="zeszyt",
            cover_id="primary",
            label=None,
            isbn13=None,
            ean2=None,
            price=None,
            limited=False,
            numbered_copies=None,
            buy_links=[],
            specs={},
        )
        with pytest.raises(Exception):
            product.format = "ebook"


class TestCreator:
    def test_instantiation(self) -> None:
        creator = Creator(role="Autor", name="Jan Kowalski", person_slug="jan-kowalski")
        assert creator.name == "Jan Kowalski"
        assert creator.role == "Autor"
        assert creator.person_slug == "jan-kowalski"


class TestImageRef:
    def test_instantiation(self) -> None:
        img = ImageRef(image="cover.jpg", alt="Book cover", caption="Main cover")
        assert img.image == "cover.jpg"
        assert img.alt == "Book cover"
        assert img.caption == "Main cover"


class TestEdition:
    def test_instantiation(self) -> None:
        edition = Edition(
            url="/komiksy/test/",
            title="Test Edition",
            project_slug="test-project",
            release="First Edition",
            release_date=date(2024, 1, 1),
            is_new=True,
            is_announcement=False,
            presale_url=None,
            legacy_anchor=None,
            primary_cover=EditionCover(
                id="primary",
                label="Standardowa",
                image="cover.jpg",
                alt="Cover alt",
                artist_name="Artist One",
                person_slug="artist-one",
            ),
            cover_aspect_class="cover--standard",
            alternate_covers=[],
            previews=[],
            creators=[],
            creator_names=[],
            edition_specs={"Liczba stron": "24"},
            products=[],
            html_body="<p>Content</p>",
            standalone=True,
            subseries=None,
            issue_number=None,
            issue_number_display=None,
        )
        assert edition.title == "Test Edition"
        assert edition.cover_image == "cover.jpg"
        assert edition.cover_alt == "Cover alt"

    def test_cover_contributors_are_derived_from_cover_metadata(self) -> None:
        edition = Edition(
            url="/komiksy/test/",
            title="Test Edition",
            project_slug="test-project",
            release=None,
            release_date=date(2024, 1, 1),
            is_new=False,
            is_announcement=False,
            presale_url=None,
            legacy_anchor=None,
            primary_cover=EditionCover(
                id="primary",
                label="Standardowa",
                image="cover.jpg",
                alt="Cover alt",
                artist_name="Artist One",
                person_slug="artist-one",
            ),
            cover_aspect_class="cover--standard",
            alternate_covers=[
                EditionCover(
                    id="alt",
                    label="Limitowana",
                    image="cover-2.jpg",
                    alt="Alt cover",
                    artist_name="Artist Two",
                    person_slug="artist-two",
                )
            ],
            previews=[],
            creators=[Creator(role="Scenariusz", name="Writer", person_slug=None)],
            creator_names=["Writer"],
            edition_specs={},
            products=[],
            html_body="",
            standalone=True,
            subseries=None,
            issue_number=None,
            issue_number_display=None,
        )

        assert [contributor.role for contributor in edition.cover_contributors] == [
            "Okładka standardowa",
            "Okładka limitowana",
        ]
        assert edition.all_contributors[0].role == "Scenariusz"
        assert edition.all_contributors[1].name == "Artist One"

    def test_product_title_combines_cover_and_format_when_needed(self) -> None:
        product = EditionProduct(
            format="zeszyt",
            cover_id="alt",
            label=None,
            isbn13=None,
            ean2=None,
            price=None,
            limited=False,
            numbered_copies=None,
            buy_links=[],
            specs={},
        )
        edition = Edition(
            url="/komiksy/test/",
            title="Test Edition",
            project_slug="test-project",
            release=None,
            release_date=date(2024, 1, 1),
            is_new=False,
            is_announcement=False,
            presale_url=None,
            legacy_anchor=None,
            primary_cover=EditionCover(
                id="primary",
                label="Standardowa",
                image="cover.jpg",
                alt=None,
                artist_name=None,
                person_slug=None,
            ),
            cover_aspect_class="cover--standard",
            alternate_covers=[
                EditionCover(
                    id="alt",
                    label="Limitowana",
                    image="cover-2.jpg",
                    alt=None,
                    artist_name=None,
                    person_slug=None,
                )
            ],
            previews=[],
            creators=[],
            creator_names=[],
            edition_specs={},
            products=[product],
            html_body="",
            standalone=True,
            subseries=None,
            issue_number=None,
            issue_number_display=None,
        )

        assert edition.product_title(product) == "Limitowana"

    def test_is_frozen(self) -> None:
        edition = Edition(
            url="/test",
            title="Test",
            project_slug="test",
            release=None,
            release_date=date(2024, 1, 1),
            is_new=False,
            is_announcement=False,
            presale_url=None,
            legacy_anchor=None,
            primary_cover=None,
            cover_aspect_class="cover--standard",
            alternate_covers=[],
            previews=[],
            creators=[],
            creator_names=[],
            edition_specs={},
            products=[],
            html_body="",
            standalone=False,
            subseries=None,
            issue_number=None,
            issue_number_display=None,
        )
        with pytest.raises(Exception):
            edition.title = "Changed"


class TestProject:
    def test_instantiation(self) -> None:
        project = Project(
            slug="test-project",
            title="Test Project",
            line="diablaq",
            summary="A test project",
            legacy_path=None,
            url="/komiksy/test-project/",
            legacy_landing=False,
            cover_image="cover.jpg",
            cover_aspect_class="cover--standard",
            html_body="<p>Body</p>",
        )
        assert project.title == "Test Project"
        assert project.kind == "title"
        assert project.universe_slug is None


class TestPerson:
    def test_prefers_credit_name_for_publication_display(self) -> None:
        person = Person(
            slug="werka-dobro",
            name="Weronika Dobrowolska",
            credit_name="Werka Dobro",
            photo=None,
            photo_thumb=None,
            html_bio="",
            related_editions=[],
        )
        assert person.display_name == "Weronika Dobrowolska"
        assert person.publication_name == "Werka Dobro"
        assert person.credit_label == "Publikuje jako: Werka Dobro"

    def test_uses_credit_name_when_full_name_is_missing(self) -> None:
        person = Person(
            slug="zvyrke",
            name=None,
            credit_name="Zvyrke",
            photo=None,
            photo_thumb=None,
            html_bio="",
            related_editions=[],
        )
        assert person.display_name == "Zvyrke"
        assert person.publication_name == "Zvyrke"
        assert person.credit_label == "Pseudonim artystyczny: Zvyrke"


class TestPage:
    def test_instantiation(self) -> None:
        page = Page(slug="about", title="About Us", html_body="<p>About</p>")
        assert page.slug == "about"
        assert page.title == "About Us"


class TestBlogPost:
    def test_instantiation(self) -> None:
        post = BlogPost(
            url="/blog/test-post/",
            slug="test-post",
            title="Test Post",
            date=date(2024, 1, 1),
            summary="A test post",
            cover_image="cover.jpg",
            cover_alt="Cover",
            tags=["test", "python"],
            html_body="<p>Content</p>",
        )
        assert post.title == "Test Post"
        assert post.slug == "test-post"
        assert post.date == date(2024, 1, 1)
