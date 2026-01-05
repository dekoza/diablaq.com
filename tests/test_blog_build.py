from __future__ import annotations

from pathlib import Path

from diablaq_site.builder import build_site


def test_blog_is_built(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = tmp_path / "dist"

    build_site(root=repo_root, out_dir=out_dir)

    assert (out_dir / "blog" / "index.html").exists()
    assert (out_dir / "blog" / "testowy-wpis" / "index.html").exists()

