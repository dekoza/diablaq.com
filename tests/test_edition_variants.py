from __future__ import annotations

from pathlib import Path

import pytest

from diablaq_site.builder import build_site


def _ensure_removed(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
        return
    for child in path.iterdir():
        _ensure_removed(child)
    path.rmdir()


def test_build_with_products(tmp_path: Path) -> None:
    """Smoke test: build succeeds when an edition uses products."""
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = tmp_path / "dist"

    build_site(root=repo_root, out_dir=out_dir)

    assert (out_dir / "komiksy" / "belzebubs" / "t01" / "index.html").exists()
    assert (out_dir / "komiksy" / "belzebubs" / "t02" / "index.html").exists()


@pytest.mark.parametrize(
    "isbn,is_valid",
    [
        ("9788397237216", True),
        ("978-83-972372-1-6", True),
        ("9788397237217", False),
        ("123", False),
    ],
)
def test_isbn13_is_validated_by_build(tmp_path: Path, isbn: str, is_valid: bool) -> None:
    """ISBN validation still happens at build time through the new products schema."""

    repo_root = Path(__file__).resolve().parents[1]
    work_root = tmp_path / "repo"
    work_root.mkdir(parents=True, exist_ok=True)

    (work_root / "templates").symlink_to(repo_root / "templates")
    (work_root / "css").symlink_to(repo_root / "css")
    (work_root / "img").symlink_to(repo_root / "img")

    content_root = work_root / "content"
    (content_root / "pages").mkdir(parents=True)

    blog_link = content_root / "blog"
    _ensure_removed(blog_link)
    blog_link.symlink_to(repo_root / "content" / "blog")

    (content_root / "projects").mkdir(parents=True)
    (content_root / "projects" / "belzebubs").mkdir(parents=True)
    (content_root / "projects" / "belzebubs" / "editions").mkdir(parents=True)

    (content_root / "projects" / "belzebubs" / "project.md").write_text(
        (repo_root / "content" / "projects" / "belzebubs" / "project.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    edition_md = (
        "---\n"
        "title: Test\n"
        "release_date: 2024-09-01\n"
        "primary_cover:\n"
        "  image: /img/belzebubs1.jpg\n"
        "products:\n"
        "  - format: miekka\n"
        f"    isbn13: '{isbn}'\n"
        "    buy_links:\n"
        "      - label: Sklep\n"
        "        url: https://example.com\n"
        "---\n"
        "\n"
        "Body\n"
    )
    (content_root / "projects" / "belzebubs" / "editions" / "test.md").write_text(
        edition_md,
        encoding="utf-8",
    )

    out_dir = tmp_path / "dist"

    if is_valid:
        build_site(root=work_root, out_dir=out_dir)
        assert (out_dir / "komiksy" / "belzebubs" / "test" / "index.html").exists()
    else:
        with pytest.raises(ValueError):
            build_site(root=work_root, out_dir=out_dir)
