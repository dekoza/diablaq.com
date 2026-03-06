"""Tests for diablaq_site.images module."""

import pytest
from pathlib import Path
from PIL import Image
from diablaq_site.images import (
    get_cover_aspect_class,
    generate_thumbnail,
    thumb_path_from_photo,
)


class TestGetCoverAspectClass:
    """Tests for get_cover_aspect_class function."""

    def test_returns_standard_for_none_path(self, tmp_path):
        """None path should return 'cover--standard'."""
        result = get_cover_aspect_class(None, tmp_path)
        assert result == "cover--standard"

    def test_returns_standard_for_empty_path(self, tmp_path):
        """Empty string path should return 'cover--standard'."""
        result = get_cover_aspect_class("", tmp_path)
        assert result == "cover--standard"

    def test_returns_standard_for_missing_file(self, tmp_path):
        """Non-existent file should return 'cover--standard', not raise error."""
        result = get_cover_aspect_class("/missing/file.jpg", tmp_path)
        assert result == "cover--standard"

    def test_tall_image_less_than_0_6(self, tmp_path):
        """Image with ratio < 0.6 should return 'cover--tall'."""
        # Create a 100x200 image (ratio = 0.5)
        img_path = tmp_path / "tall.jpg"
        img = Image.new("RGB", (100, 200), color="red")
        img.save(img_path, "JPEG")

        root = tmp_path
        result = get_cover_aspect_class(str(img_path.relative_to(root)), root)
        assert result == "cover--tall"

    def test_wide_image_greater_than_0_75(self, tmp_path):
        """Image with ratio > 0.75 should return 'cover--wide'."""
        # Create a 200x100 image (ratio = 2.0)
        img_path = tmp_path / "wide.jpg"
        img = Image.new("RGB", (200, 100), color="blue")
        img.save(img_path, "JPEG")

        root = tmp_path
        result = get_cover_aspect_class(str(img_path.relative_to(root)), root)
        assert result == "cover--wide"

    def test_standard_image_between_0_6_and_0_75(self, tmp_path):
        """Image with 0.6 <= ratio <= 0.75 should return 'cover--standard'."""
        # Create a 150x200 image (ratio = 0.75)
        img_path = tmp_path / "standard.jpg"
        img = Image.new("RGB", (150, 200), color="green")
        img.save(img_path, "JPEG")

        root = tmp_path
        result = get_cover_aspect_class(str(img_path.relative_to(root)), root)
        assert result == "cover--standard"

    def test_standard_image_at_boundary_0_6(self, tmp_path):
        """Image with ratio exactly at 0.6 boundary should return 'cover--standard'."""
        # Create a 120x200 image (ratio = 0.6)
        img_path = tmp_path / "boundary_low.jpg"
        img = Image.new("RGB", (120, 200), color="yellow")
        img.save(img_path, "JPEG")

        root = tmp_path
        result = get_cover_aspect_class(str(img_path.relative_to(root)), root)
        assert result == "cover--standard"

    def test_standard_image_at_boundary_0_75(self, tmp_path):
        """Image with ratio exactly at 0.75 boundary should return 'cover--standard'."""
        # Create a 150x200 image (ratio = 0.75)
        img_path = tmp_path / "boundary_high.jpg"
        img = Image.new("RGB", (150, 200), color="cyan")
        img.save(img_path, "JPEG")

        root = tmp_path
        result = get_cover_aspect_class(str(img_path.relative_to(root)), root)
        assert result == "cover--standard"

    def test_handles_leading_slash_in_path(self, tmp_path):
        """Path with leading slash should be stripped and resolved."""
        # Create subdir with image
        img_dir = tmp_path / "img"
        img_dir.mkdir()
        img_path = img_dir / "cover.jpg"
        img = Image.new("RGB", (200, 100), color="red")
        img.save(img_path, "JPEG")

        root = tmp_path
        result = get_cover_aspect_class("/img/cover.jpg", root)
        assert result == "cover--wide"

    def test_returns_standard_for_corrupted_image(self, tmp_path):
        """Corrupted image file should return 'cover--standard', not raise error."""
        corrupted_path = tmp_path / "corrupted.jpg"
        corrupted_path.write_text("not a valid image")

        root = tmp_path
        result = get_cover_aspect_class(str(corrupted_path.relative_to(root)), root)
        assert result == "cover--standard"

    def test_png_image(self, tmp_path):
        """PNG image should be handled correctly."""
        img_path = tmp_path / "cover.png"
        img = Image.new("RGBA", (100, 200), color=(255, 0, 0, 255))
        img.save(img_path, "PNG")

        root = tmp_path
        result = get_cover_aspect_class(str(img_path.relative_to(root)), root)
        assert result == "cover--tall"


class TestGenerateThumbnail:
    """Tests for generate_thumbnail function."""

    def test_creates_thumbnail_from_existing_file(self, tmp_path):
        """Should create thumbnail from existing image."""
        src = tmp_path / "source.jpg"
        dst = tmp_path / "thumb.jpg"

        # Create source image (800x600)
        img = Image.new("RGB", (800, 600), color="red")
        img.save(src, "JPEG")

        generate_thumbnail(src, dst, size=(300, 300))

        # Verify thumbnail was created
        assert dst.exists()
        thumb = Image.open(dst)
        assert thumb.width <= 300
        assert thumb.height <= 300

    def test_preserves_aspect_ratio_in_thumbnail(self, tmp_path):
        """Thumbnail should maintain aspect ratio."""
        src = tmp_path / "source.jpg"
        dst = tmp_path / "thumb.jpg"

        # Create 800x400 image (2:1 aspect ratio)
        img = Image.new("RGB", (800, 400), color="blue")
        img.save(src, "JPEG")

        generate_thumbnail(src, dst, size=(300, 300))

        thumb = Image.open(dst)
        # Aspect ratio should be preserved (width > height)
        assert thumb.width > thumb.height

    def test_handles_missing_source_file(self, tmp_path):
        """Missing source file should not raise error (graceful no-op)."""
        src = tmp_path / "missing.jpg"
        dst = tmp_path / "thumb.jpg"

        # Should not raise error
        generate_thumbnail(src, dst, size=(300, 300))

        # Destination should not be created
        assert not dst.exists()

    def test_creates_parent_directories(self, tmp_path):
        """Should create parent directories if they don't exist."""
        src = tmp_path / "source.jpg"
        dst = tmp_path / "deep" / "nested" / "path" / "thumb.jpg"

        # Create source
        img = Image.new("RGB", (800, 600), color="green")
        img.save(src, "JPEG")

        generate_thumbnail(src, dst, size=(300, 300))

        assert dst.exists()
        assert dst.parent == tmp_path / "deep" / "nested" / "path"

    def test_converts_rgba_to_rgb(self, tmp_path):
        """RGBA image should be converted to RGB for JPEG."""
        src = tmp_path / "source.png"
        dst = tmp_path / "thumb.jpg"

        # Create RGBA image
        img = Image.new("RGBA", (800, 600), color=(255, 0, 0, 255))
        img.save(src, "PNG")

        generate_thumbnail(src, dst, size=(300, 300))

        # Verify JPEG was created (not RGBA)
        assert dst.exists()
        thumb = Image.open(dst)
        assert thumb.format == "JPEG"

    def test_custom_size_parameter(self, tmp_path):
        """Should respect custom size parameter."""
        src = tmp_path / "source.jpg"
        dst = tmp_path / "thumb.jpg"

        img = Image.new("RGB", (2000, 1500), color="yellow")
        img.save(src, "JPEG")

        generate_thumbnail(src, dst, size=(100, 100))

        thumb = Image.open(dst)
        assert thumb.width <= 100
        assert thumb.height <= 100

    def test_large_image_downsampled(self, tmp_path):
        """Large image should be downsampled to thumbnail size."""
        src = tmp_path / "large.jpg"
        dst = tmp_path / "thumb.jpg"

        # Create very large image
        img = Image.new("RGB", (4000, 3000), color="purple")
        img.save(src, "JPEG")

        generate_thumbnail(src, dst, size=(300, 300))

        thumb = Image.open(dst)
        assert thumb.width <= 300
        assert thumb.height <= 300


class TestThumbPathFromPhoto:
    """Tests for thumb_path_from_photo function."""

    def test_simple_filename(self):
        """Simple filename should get _thumb.jpg suffix."""
        result = thumb_path_from_photo("photo.jpg")
        assert result == "photo_thumb.jpg"

    def test_path_with_directory(self):
        """Path with directory should preserve directory and add suffix."""
        result = thumb_path_from_photo("img/photos/photo.jpg")
        assert result == "img/photos/photo_thumb.jpg"

    def test_different_extension(self):
        """Should replace original extension with _thumb.jpg."""
        result = thumb_path_from_photo("photo.png")
        assert result == "photo_thumb.jpg"

    def test_path_without_extension(self):
        """Path without extension should still add _thumb.jpg."""
        result = thumb_path_from_photo("photo")
        assert result == "photo_thumb.jpg"

    def test_multiple_dots_in_filename(self):
        """Filename with multiple dots should use stem correctly."""
        result = thumb_path_from_photo("photo.backup.jpg")
        assert result == "photo.backup_thumb.jpg"

    def test_absolute_path(self):
        """Absolute path should be preserved."""
        result = thumb_path_from_photo("/var/img/photo.jpg")
        assert result == "/var/img/photo_thumb.jpg"

    def test_nested_directories(self):
        """Deeply nested path should be preserved."""
        result = thumb_path_from_photo("a/b/c/d/photo.jpg")
        assert result == "a/b/c/d/photo_thumb.jpg"

    def test_return_type_is_string(self):
        """Return value should be a string, not Path object."""
        result = thumb_path_from_photo("photo.jpg")
        assert isinstance(result, str)
