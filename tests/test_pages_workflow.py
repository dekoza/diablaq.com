"""Regression checks for GitHub Pages deployment coordination."""

from pathlib import Path

import yaml


def test_new_push_does_not_cancel_active_pages_deployment(repo_root: Path) -> None:
    workflow_path = repo_root / ".github" / "workflows" / "pages.yml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    # Pages can keep deploying after its Actions runner is canceled, blocking
    # the next run with an "in progress deployment" error.
    assert workflow["concurrency"]["group"] == "pages"
    assert workflow["concurrency"]["cancel-in-progress"] is False
