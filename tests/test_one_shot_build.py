from __future__ import annotations

from pathlib import Path

from diablaq_site.builder import build_site


def test_selected_one_shots_render_at_project_url(tmp_path: Path) -> None:
    """Full one-shot treatment collapses selected titles to the project URL."""
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = tmp_path / "dist"

    build_site(root=repo_root, out_dir=out_dir)

    assert (out_dir / "komiksy" / "hadfield" / "index.html").exists()
    assert not (out_dir / "komiksy" / "hadfield" / "01" / "index.html").exists()
    assert (out_dir / "komiksy" / "paatrzcie-co-oni-robia" / "index.html").exists()
    assert not (
        out_dir / "komiksy" / "paatrzcie-co-oni-robia" / "01" / "index.html"
    ).exists()


def test_build_redirects_old_one_shot_issue_urls(tmp_path: Path) -> None:
    """Collapsed one-shots keep redirects from their old issue URLs."""
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = tmp_path / "dist"

    build_site(root=repo_root, out_dir=out_dir)

    redirects = (out_dir / "_redirects").read_text(encoding="utf-8")

    assert "/komiksy/hadfield/01/*  /komiksy/hadfield/:splat  301" in redirects
    assert (
        "/komiksy/paatrzcie-co-oni-robia/01/*  /komiksy/paatrzcie-co-oni-robia/:splat  301"
        in redirects
    )
