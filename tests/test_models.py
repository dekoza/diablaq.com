"""Tests for diablaq_site.models — dataclass definitions."""

from datetime import date

import pytest

from diablaq_site.models import (
    BuyLink,
    EditionVariant,
    Creator,
    ImageRef,
    Edition,
    Project,
    Person,
    Page,
    BlogPost,
)


class TestBuyLink:
    """BuyLink dataclass."""

    def test_buylink_import(self):
        """BuyLink can be imported from models."""
        assert BuyLink is not None

    def test_buylink_instantiation(self):
        """BuyLink can be instantiated with required fields."""
        link = BuyLink(label="Amazon", url="https://amazon.com")
        assert link.label == "Amazon"
        assert link.url == "https://amazon.com"

    def test_buylink_frozen(self):
        """BuyLink is frozen (immutable)."""
        link = BuyLink(label="Test", url="http://test.com")
        with pytest.raises(Exception):  # FrozenInstanceError
            link.label = "Changed"


class TestEditionVariant:
    """EditionVariant dataclass — most critical fields."""

    def test_editionvariant_import(self):
        """EditionVariant can be imported from models."""
        assert EditionVariant is not None

    def test_editionvariant_required_field_isbn13(self):
        """EditionVariant requires isbn13 (no default)."""
        # This should work with only required fields
        variant = EditionVariant(
            binding=None,
            version=None,
            isbn13="9788394123456",
            limited_print_run=None,
            numbered=False,
            buy_links=[],
            specs={},
        )
        assert variant.isbn13 == "9788394123456"

    def test_editionvariant_no_default_on_isbn13(self):
        """EditionVariant.isbn13 has NO default value."""
        # Missing isbn13 should raise TypeError
        with pytest.raises(TypeError):
            EditionVariant(
                binding=None,
                version=None,
                # isbn13 missing
                limited_print_run=None,
                numbered=False,
                buy_links=[],
                specs={},
            )

    def test_editionvariant_field_types(self):
        """EditionVariant has correct field types: binding|version optional, isbn13 str, numbered bool, lists."""
        variant = EditionVariant(
            binding="miekka",
            version=None,
            isbn13="9788394123456",
            limited_print_run=500,
            numbered=True,
            buy_links=[BuyLink(label="Sklepik", url="http://shop.com")],
            specs={"Cena": "69.90 zł", "Wymiary": "165 x 235 mm"},
        )
        assert isinstance(variant.binding, str | type(None))
        assert isinstance(variant.version, str | type(None))
        assert isinstance(variant.isbn13, str)
        assert isinstance(variant.limited_print_run, int | type(None))
        assert isinstance(variant.numbered, bool)
        assert isinstance(variant.buy_links, list)
        assert isinstance(variant.specs, dict)

    def test_editionvariant_frozen(self):
        """EditionVariant is frozen (immutable)."""
        variant = EditionVariant(
            binding=None,
            version=None,
            isbn13="123",
            limited_print_run=None,
            numbered=False,
            buy_links=[],
            specs={},
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            variant.isbn13 = "456"


class TestCreator:
    """Creator dataclass."""

    def test_creator_import(self):
        """Creator can be imported from models."""
        assert Creator is not None

    def test_creator_instantiation(self):
        """Creator can be instantiated."""
        creator = Creator(role="Autor", name="Jan Kowalski", person_slug="jan-kowalski")
        assert creator.name == "Jan Kowalski"
        assert creator.role == "Autor"
        assert creator.person_slug == "jan-kowalski"

    def test_creator_frozen(self):
        """Creator is frozen."""
        creator = Creator(role="Autor", name="Test", person_slug="test")
        with pytest.raises(Exception):
            creator.name = "Changed"


class TestImageRef:
    """ImageRef dataclass."""

    def test_imageref_import(self):
        """ImageRef can be imported from models."""
        assert ImageRef is not None

    def test_imageref_instantiation(self):
        """ImageRef can be instantiated."""
        img = ImageRef(image="cover.jpg", alt="Book cover", caption="Main cover")
        assert img.image == "cover.jpg"
        assert img.alt == "Book cover"
        assert img.caption == "Main cover"

    def test_imageref_frozen(self):
        """ImageRef is frozen."""
        img = ImageRef(image="test.jpg", alt=None, caption=None)
        with pytest.raises(Exception):
            img.image = "other.jpg"


class TestEdition:
    """Edition dataclass — includes is_new and is_announcement."""

    def test_edition_import(self):
        """Edition can be imported from models."""
        assert Edition is not None

    def test_edition_instantiation(self):
        """Edition can be instantiated with minimal data."""
        edition = Edition(
            url="/pl/wydania/test",
            title="Test Edition",
            project_slug="test-project",
            release="First Edition",
            release_date=date(2024, 1, 1),
            is_new=True,
            is_announcement=False,
            presale_url=None,
            legacy_anchor=None,
            cover_image="cover.jpg",
            cover_alt="Cover alt",
            cover_aspect_class="aspect-2-3",
            covers=[],
            previews=[],
            creators=[],
            creator_names=[],
            specs={},
            buy_links=[],
            variants=[],
            html_body="<p>Content</p>",
            standalone=True,
            subseries=None,
            issue_number=None,
            issue_number_display=None,
        )
        assert edition.title == "Test Edition"
        assert edition.is_new is True
        assert edition.is_announcement is False

    def test_edition_is_new_field_exists(self):
        """Edition.is_new field exists and is bool."""
        edition = Edition(
            url="/test",
            title="Test",
            project_slug="test",
            release=None,
            release_date=date(2024, 1, 1),
            is_new=False,
            is_announcement=True,
            presale_url=None,
            legacy_anchor=None,
            cover_image=None,
            cover_alt=None,
            cover_aspect_class="aspect-2-3",
            covers=[],
            previews=[],
            creators=[],
            creator_names=[],
            specs={},
            buy_links=[],
            variants=[],
            html_body="",
            standalone=False,
            subseries=None,
            issue_number=None,
            issue_number_display=None,
        )
        assert isinstance(edition.is_new, bool)
        assert isinstance(edition.is_announcement, bool)

    def test_edition_frozen(self):
        """Edition is frozen."""
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
            cover_image=None,
            cover_alt=None,
            cover_aspect_class="aspect-2-3",
            covers=[],
            previews=[],
            creators=[],
            creator_names=[],
            specs={},
            buy_links=[],
            variants=[],
            html_body="",
            standalone=False,
            subseries=None,
            issue_number=None,
            issue_number_display=None,
        )
        with pytest.raises(Exception):
            edition.title = "Changed"


class TestProject:
    """Project dataclass."""

    def test_project_import(self):
        """Project can be imported from models."""
        assert Project is not None

    def test_project_instantiation(self):
        """Project can be instantiated."""
        project = Project(
            slug="test-project",
            title="Test Project",
            line="diablaq",
            summary="A test project",
            legacy_path=None,
            url="/pl/projekty/test-project",
            legacy_landing=False,
            cover_image="cover.jpg",
            cover_aspect_class="aspect-2-3",
            html_body="<p>Body</p>",
        )
        assert project.title == "Test Project"
        assert project.slug == "test-project"
        assert project.kind == "title"
        assert project.universe_slug is None

    def test_project_instantiation_with_universe_relationship(self):
        """Project can represent a title that belongs to a universe."""
        project = Project(
            slug="cudowni",
            title="Cudowni",
            line="diablaq",
            summary="A title inside MidGuard.",
            legacy_path=None,
            url="/komiksy/cudowni/",
            legacy_landing=False,
            cover_image="cover.jpg",
            cover_aspect_class="cover--standard",
            html_body="<p>Body</p>",
            universe_slug="midguard",
        )
        assert project.kind == "title"
        assert project.universe_slug == "midguard"

    def test_project_frozen(self):
        """Project is frozen."""
        project = Project(
            slug="test",
            title="Test",
            line="diablaq",
            summary=None,
            legacy_path=None,
            url="/test",
            legacy_landing=False,
            cover_image=None,
            cover_aspect_class="",
            html_body="",
        )
        with pytest.raises(Exception):
            project.title = "Changed"


class TestPerson:
    """Person dataclass."""

    def test_person_import(self):
        """Person can be imported from models."""
        assert Person is not None

    def test_person_instantiation(self):
        """Person can be instantiated."""
        person = Person(
            slug="jan-kowalski",
            name="Jan Kowalski",
            photo="photo.jpg",
            photo_thumb="photo-thumb.jpg",
            html_bio="<p>Bio</p>",
            related_editions=[],
        )
        assert person.name == "Jan Kowalski"
        assert person.slug == "jan-kowalski"
        assert person.display_name == "Jan Kowalski"
        assert person.publication_name == "Jan Kowalski"
        assert person.credit_label is None

    def test_person_prefers_credit_name_for_publication_display(self):
        """Publication display should prefer credit_name over full name."""
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

    def test_person_uses_credit_name_when_full_name_is_missing(self):
        """Credit-only people should display and publish under credit_name."""
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

    def test_person_frozen(self):
        """Person is frozen."""
        person = Person(
            slug="test",
            name="Test",
            photo=None,
            photo_thumb=None,
            html_bio="",
            related_editions=[],
        )
        with pytest.raises(Exception):
            person.name = "Changed"


class TestPage:
    """Page dataclass."""

    def test_page_import(self):
        """Page can be imported from models."""
        assert Page is not None

    def test_page_instantiation(self):
        """Page can be instantiated."""
        page = Page(slug="about", title="About Us", html_body="<p>About</p>")
        assert page.slug == "about"
        assert page.title == "About Us"

    def test_page_frozen(self):
        """Page is frozen."""
        page = Page(slug="test", title="Test", html_body="")
        with pytest.raises(Exception):
            page.title = "Changed"


class TestBlogPost:
    """BlogPost dataclass."""

    def test_blogpost_import(self):
        """BlogPost can be imported from models."""
        assert BlogPost is not None

    def test_blogpost_instantiation(self):
        """BlogPost can be instantiated."""
        post = BlogPost(
            url="/blog/test-post",
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

    def test_blogpost_frozen(self):
        """BlogPost is frozen."""
        post = BlogPost(
            url="/test",
            slug="test",
            title="Test",
            date=date(2024, 1, 1),
            summary=None,
            cover_image=None,
            cover_alt=None,
            tags=[],
            html_body="",
        )
        with pytest.raises(Exception):
            post.title = "Changed"
