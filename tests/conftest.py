"""Shared pytest fixtures for diablaq.com tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def repo_root() -> Path:
    """Return the project root directory (one level up from tests/)."""
    return PROJECT_ROOT


@pytest.fixture
def sample_frontmatter() -> dict[str, str]:
    """Provide minimal valid Markdown+YAML frontmatter for test content types.

    Returns a dictionary with keys: edition, project, person, blog, page.
    Each value is a complete Markdown file with YAML frontmatter header.
    """
    return {
        "edition": """\
---
title: Test Edition
slug: test-edition
isbn: "9788397237216"
---

Test edition content.
""",
        "project": """\
---
title: Test Project
line: diablaq
summary: A test project for CI/CD
---

Test project content.
""",
        "person": """\
---
name: Test Author
photo: /img/people/test.jpg
---

Test person biography.
""",
        "blog": """\
---
title: Test Blog Post
date: 2026-01-15
summary: A test blog post
tags:
  - test
---

Test blog content.
""",
        "page": """\
---
title: Test Page
---

Test page content.
""",
    }


@pytest.fixture
def minimal_content_tree(tmp_path: Path, repo_root: Path) -> Path:
    """Create a minimal content directory structure for testing.

    Returns the work_root path containing symlinked templates/css/img
    and synthetic test content in content/ subdirectories.

    Creates:
      - content/projects/ with one test project
      - content/people/ with one test person
      - content/pages/ with one test page
      - content/blog/ with one test blog post
      - Symlinks to real templates/, css/, img/ from repo_root
    """
    work_root = tmp_path / "work"
    work_root.mkdir(parents=True, exist_ok=True)

    # Symlink shared resources
    (work_root / "templates").symlink_to(repo_root / "templates")
    (work_root / "css").symlink_to(repo_root / "css")
    (work_root / "img").symlink_to(repo_root / "img")

    # Create content directories
    content_root = work_root / "content"
    (content_root / "projects" / "test-project").mkdir(parents=True)
    (content_root / "people").mkdir(parents=True)
    (content_root / "pages").mkdir(parents=True)
    (content_root / "blog").mkdir(parents=True)

    # Create synthetic test files
    (content_root / "projects" / "test-project" / "project.md").write_text(
        """\
---
title: Test Project
line: diablaq
summary: A synthetic test project
---

Test project content for CI/CD.
"""
    )

    (content_root / "people" / "test-author.md").write_text(
        """\
---
name: Test Author
photo: /img/people/test.jpg
---

Test author biography.
"""
    )

    (content_root / "pages" / "test-page.md").write_text(
        """\
---
title: Test Page
---

Test page content.
"""
    )

    (content_root / "blog" / "test-post.md").write_text(
        """\
---
title: Test Blog Post
date: 2026-01-15
summary: A test blog post
tags:
  - test
---

Test blog post content.
"""
    )

    return work_root
