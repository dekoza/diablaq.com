"""Tests for io.py module — HTML writing and directory copying utilities."""

import shutil
from pathlib import Path

import pytest

from diablaq_site.io import _write_html, _copy_tree


class TestWriteHtml:
    """Tests for _write_html(path: Path, html: str) -> None."""

    def test_writes_file_with_utf8_encoding(self, tmp_path):
        """Normal write: creates file with UTF-8 content."""
        target = tmp_path / "output.html"
        content = "<html><body>Hello</body></html>"

        _write_html(target, content)

        assert target.exists()
        assert target.read_text(encoding="utf-8") == content

    def test_creates_missing_parent_directory(self, tmp_path):
        """Parent dir missing: creates parent directories automatically."""
        target = tmp_path / "nested" / "output.html"
        content = "<html></html>"

        _write_html(target, content)

        assert target.exists()
        assert target.read_text(encoding="utf-8") == content

    def test_creates_multiple_nested_parent_directories(self, tmp_path):
        """Nested parent dirs missing: creates all intermediate directories."""
        target = tmp_path / "a" / "b" / "c" / "d" / "output.html"
        content = "<html><body>Nested</body></html>"

        _write_html(target, content)

        assert target.exists()
        assert target.parent.exists()
        assert target.read_text(encoding="utf-8") == content

    def test_overwrites_existing_file(self, tmp_path):
        """Overwrite existing file: replaces content."""
        target = tmp_path / "output.html"
        target.write_text("old content", encoding="utf-8")

        new_content = "<html><body>New</body></html>"
        _write_html(target, new_content)

        assert target.read_text(encoding="utf-8") == new_content

    def test_writes_utf8_special_characters(self, tmp_path):
        """UTF-8 content with special characters: written correctly."""
        target = tmp_path / "polish.html"
        content = "<html>ąćęłńóśźż</html>"

        _write_html(target, content)

        assert target.read_text(encoding="utf-8") == content

    def test_writes_empty_content(self, tmp_path):
        """Empty content: creates empty file."""
        target = tmp_path / "empty.html"

        _write_html(target, "")

        assert target.exists()
        assert target.read_text(encoding="utf-8") == ""

    def test_writes_large_content(self, tmp_path):
        """Large content: test with multi-KB HTML string."""
        target = tmp_path / "large.html"
        content = "<html><body>" + ("x" * 10000) + "</body></html>"

        _write_html(target, content)

        assert target.read_text(encoding="utf-8") == content

    def test_preserves_newlines(self, tmp_path):
        """Newlines are preserved correctly in content."""
        target = tmp_path / "newlines.html"
        content = "<html>\n<body>\n  <p>Test</p>\n</body>\n</html>"

        _write_html(target, content)

        assert target.read_text(encoding="utf-8") == content

    def test_overwrites_with_different_length(self, tmp_path):
        """Overwrite with significantly shorter content."""
        target = tmp_path / "overwrite.html"
        target.write_text("very long original content here", encoding="utf-8")

        _write_html(target, "short")

        assert target.read_text(encoding="utf-8") == "short"


class TestCopyTree:
    """Tests for _copy_tree(src: Path, dst: Path) -> None."""

    def test_copies_simple_directory(self, tmp_path):
        """Normal directory copy: recursively copies all files and subdirectories."""
        src = tmp_path / "source"
        src.mkdir()
        (src / "file1.txt").write_text("content1")
        (src / "file2.txt").write_text("content2")

        dst = tmp_path / "destination"
        _copy_tree(src, dst)

        assert dst.exists()
        assert (dst / "file1.txt").read_text() == "content1"
        assert (dst / "file2.txt").read_text() == "content2"

    def test_copies_nested_subdirectories(self, tmp_path):
        """Nested subdirectories: preserves directory structure."""
        src = tmp_path / "source"
        src.mkdir()
        (src / "subdir").mkdir()
        (src / "subdir" / "nested.txt").write_text("nested content")
        (src / "subdir" / "deep").mkdir()
        (src / "subdir" / "deep" / "file.txt").write_text("deep content")

        dst = tmp_path / "destination"
        _copy_tree(src, dst)

        assert (dst / "subdir" / "nested.txt").read_text() == "nested content"
        assert (dst / "subdir" / "deep" / "file.txt").read_text() == "deep content"

    def test_copies_files_with_various_extensions(self, tmp_path):
        """Files with various extensions: .html, .css, .jpg, .json all copied."""
        src = tmp_path / "source"
        src.mkdir()
        (src / "index.html").write_text("<html></html>")
        (src / "style.css").write_text("body { }")
        (src / "data.json").write_text('{"key": "value"}')
        (src / "image.jpg").write_bytes(b"fake jpg data")

        dst = tmp_path / "destination"
        _copy_tree(src, dst)

        assert (dst / "index.html").read_text() == "<html></html>"
        assert (dst / "style.css").read_text() == "body { }"
        assert (dst / "data.json").read_text() == '{"key": "value"}'
        assert (dst / "image.jpg").read_bytes() == b"fake jpg data"

    def test_handles_destination_exists(self, tmp_path):
        """Destination exists: overwrites/merges."""
        src = tmp_path / "source"
        src.mkdir()
        (src / "new.txt").write_text("new content")

        dst = tmp_path / "destination"
        dst.mkdir()
        (dst / "old.txt").write_text("old content")

        _copy_tree(src, dst)

        assert (dst / "new.txt").read_text() == "new content"
        # Old file should still exist (merge behavior)
        assert (dst / "old.txt").read_text() == "old content"

    def test_handles_nonexistent_source(self, tmp_path):
        """Source doesn't exist: returns silently (no error)."""
        src = tmp_path / "nonexistent"
        dst = tmp_path / "destination"

        # Should not raise
        _copy_tree(src, dst)

        # Destination should not be created
        assert not dst.exists()

    def test_copies_empty_directory(self, tmp_path):
        """Empty source directory: creates empty destination directory."""
        src = tmp_path / "source"
        src.mkdir()

        dst = tmp_path / "destination"
        _copy_tree(src, dst)

        assert dst.exists()
        assert dst.is_dir()
        assert list(dst.iterdir()) == []

    def test_copies_mixed_content(self, tmp_path):
        """Complex structure: files, subdirs, and various content types."""
        src = tmp_path / "source"
        src.mkdir()
        (src / "root_file.txt").write_text("root")

        (src / "assets").mkdir()
        (src / "assets" / "style.css").write_text("css")

        (src / "pages").mkdir()
        (src / "pages" / "index.html").write_text("<html></html>")
        (src / "pages" / "nested").mkdir()
        (src / "pages" / "nested" / "sub.html").write_text("<sub></sub>")

        dst = tmp_path / "destination"
        _copy_tree(src, dst)

        assert (dst / "root_file.txt").read_text() == "root"
        assert (dst / "assets" / "style.css").read_text() == "css"
        assert (dst / "pages" / "index.html").read_text() == "<html></html>"
        assert (dst / "pages" / "nested" / "sub.html").read_text() == "<sub></sub>"
