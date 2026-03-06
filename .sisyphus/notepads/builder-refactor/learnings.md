# Learnings — builder-refactor

Conventions, patterns, architectural decisions discovered during refactoring.

---
# Builder Refactor - Learnings

## Task 1: Golden Build Snapshot

### Key Discoveries
- **CLI invocation**: Use `.venv/bin/python -m diablaq_site.cli` (not `poetry run` or direct script call)
- **CLI arguments**: `--root` (default: current dir) and `--out` (default: <root>/dist)
- **Output scale**: Build produces 99 HTML files + 60 other assets = 159 total files
- **Dependencies**: Uses `python-frontmatter`, `jinja2`, `markdown`, `pillow`, `pyyaml`
- **uv environment**: Project uses uv for dependency management (poetry.lock exists but uv is preferred)

### Build Process Notes
- Silent success: Builder exits with code 0 and no console output on success
- Checksum strategy: 159 files checksummed for byte-identical comparison in Task 12
- File organization: Output includes HTML, images, CSS, and CNAME file for GitHub Pages

### For Future Tasks
- Golden snapshot stored in `.sisyphus/evidence/golden-build/`
- Manifest available in `.sisyphus/evidence/golden-manifest.txt`
- /tmp/dist-golden/ preserved for Task 12 comparison


## Test Infrastructure Patterns

### Fixture Design — conftest.py

1. **repo_root fixture**: Resolves project root once per test session
   - Pattern: `Path(__file__).resolve().parents[1]`
   - Use: Pass to other fixtures or access real assets (templates, css, img)

2. **sample_frontmatter fixture**: Provides minimal valid Markdown + YAML
   - Returns dict with keys: edition, project, person, blog, page
   - Each value is a complete file string (---\ntitle: ...\n---\ncontent)
   - Use: For creating test files without copying real content

3. **minimal_content_tree fixture**: Creates isolated test environment
   - Takes `tmp_path` (pytest built-in) and `repo_root` as dependencies
   - Creates: `content/{projects,people,pages,blog}/` with one synthetic file each
   - Symlinks: templates/, css/, img/ to real repo versions (avoids duplication)
   - Returns: work_root path ready for build_site(root=work_root, out_dir=...)

### Directory Symlink Pattern (from test_edition_variants.py)

Tests that call build_site() should use minimal isolated work directories:
```python
work_root = tmp_path / "work"
work_root.mkdir()
# Symlink shared resources
(work_root / "templates").symlink_to(repo_root / "templates")
(work_root / "css").symlink_to(repo_root / "css")
(work_root / "img").symlink_to(repo_root / "img")
# Create synthetic content
content_root = work_root / "content"
(content_root / "projects" / "test").mkdir(parents=True)
```

Benefits:
- Tests don't mutate real content/
- Fast symlinks avoid copying large directories
- Real templates/css/img ensure correct rendering

### Frontmatter Format

All content files follow this structure:
```markdown
---
title: Display Name
[field]: value  # Additional YAML fields per type
---

Markdown content here.
```

Types and required fields:
- **edition**: title, slug, isbn
- **project**: title, line (diablaq/mecenat/etc), summary
- **person**: name, photo (path to /img/...)
- **blog**: title, date (YYYY-MM-DD), summary, tags (list)
- **page**: title (minimal)
