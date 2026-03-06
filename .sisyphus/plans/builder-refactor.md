# Refactor builder.py into Modules

## TL;DR

> **Quick Summary**: Split the monolithic `diablaq_site/builder.py` (1131 lines) into 8 focused modules with proper test coverage, transforming the 530-line `build_site()` god-function into a thin pipeline orchestrator.
> 
> **Deliverables**:
> - 8 new modules: models, text, parsing, validation, images, urls, rendering, io
> - Slim orchestrator in builder.py (~150 lines)
> - Comprehensive test suite: unit tests per module + existing integration tests preserved
> - Golden build comparison proving zero behavioral regression
> 
> **Estimated Effort**: Medium
> **Parallel Execution**: YES - 4 waves
> **Critical Path**: Task 1 → Task 2 → Task 3 → Tasks 4-8 (parallel) → Tasks 9-10 (parallel) → Task 11 → Task 12 → F1-F4 (parallel)

---

## Context

### Original Request
Refactor `diablaq_site/builder.py` — a 1131-line monolithic Python static site generator for a Polish comic book publisher's website — into clean, testable modules with proper test coverage.

### Interview Summary
**Key Discussions**:
- **Split depth**: Full decomposition into ~8 modules (not conservative extract)
- **build_site() strategy**: Phase-based pipeline — load → process → render → finalize
- **Behavior preservation**: All external behavior preserved; minor improvements (error messages, warnings) allowed
- **Test strategy**: TDD per AGENTS.md — write tests first, then extract code

**Research Findings**:
- Full symbol inventory mapped: 9 dataclasses, ~20 helper functions, 14 identifiable phases in build_site()
- Internal coupling graph: most helpers are leaf functions; _parse_variants is most coupled (calls 6 others)
- Nested closures in build_site() capture env, nav_projects, site_url — must convert to explicit params
- Module-level constants are safe to move (no mutable globals, no import-time side effects)
- Test infrastructure: pytest + poetry, 2 integration test files, no conftest.py
- Likely untested: _generate_thumbnail, _get_cover_aspect_class, _parse_image_list, _parse_creators error paths, _slugify_tag, legacy redirects

### Metis Review
**Identified Gaps** (addressed):
- **Closure strategy**: Resolved → use explicit parameters (simplest, no new abstractions)
- **_read_markdown_file placement**: Resolved → parsing.py (primary purpose is content parsing)
- **DIABLAQ_SITE_URL handling**: Resolved → read env in orchestrator, pass as param to rendering
- **Test data strategy**: Resolved → synthetic fixtures for unit tests, keep real content for integration
- **Golden build comparison**: Added as final verification task
- **Sequential extraction**: Encoded in wave dependencies
- **Move-then-improve**: Added as guardrail

---

## Work Objectives

### Core Objective
Transform the monolithic builder.py into a well-structured package of focused modules, each independently testable, while preserving 100% behavioral compatibility.

### Concrete Deliverables
- `diablaq_site/models.py` — All 9 dataclasses
- `diablaq_site/text.py` — Polish typographic helpers
- `diablaq_site/parsing.py` — Content/frontmatter parsing
- `diablaq_site/validation.py` — ISBN validation, variant constants
- `diablaq_site/images.py` — Cover aspect detection, thumbnail generation
- `diablaq_site/urls.py` — Canonical URLs, tag slugification
- `diablaq_site/rendering.py` — Template rendering helpers
- `diablaq_site/io.py` — File/directory operations
- `diablaq_site/builder.py` — Slim orchestrator (~150 lines)
- `tests/test_models.py`, `tests/test_text.py`, `tests/test_parsing.py`, `tests/test_validation.py`, `tests/test_images.py`, `tests/test_urls.py`, `tests/test_rendering.py`, `tests/test_io.py` — Unit tests per module
- `tests/conftest.py` — Shared fixtures (sample content, temp dirs)

### Definition of Done
- [ ] `poetry run pytest` passes with all existing + new tests
- [ ] Golden build comparison: `dist/` output from refactored code is byte-identical to pre-refactor output
- [ ] `build_site(root, out_dir)` signature unchanged — cli.py works without modification
- [ ] No function in any extracted module exceeds 50 lines
- [ ] Every extracted module has corresponding test file with ≥1 happy path + ≥1 error path test

### Must Have
- 100% behavioral compatibility with current builder (same HTML output, same URL structure, same file layout)
- All 9 dataclasses in models.py with identical field names and types
- Public API: `build_site(root: Path, out_dir: Path)` unchanged
- TDD workflow: tests written BEFORE code is moved
- All existing tests continue to pass throughout refactoring

### Must NOT Have (Guardrails)
- **No new features** — RSS, sitemap, search, i18n, etc. are OUT OF SCOPE
- **No interface "improvements"** to internal functions during extraction — move code AS-IS first. The synthetic dict wrapper in `_parse_variants` calling `_parse_buy_links({"buy_links": item.get("buy_links")}, ...)` must be preserved exactly.
- **No template changes** — templates reference dataclass attributes; do not rename any fields
- **No content/CSS changes** — content files and stylesheets are untouched
- **No premature abstraction** — no base classes, no plugin systems, no strategy patterns, no builder pattern for build_site()
- **No over-commenting** — do not add docstrings that restate function names
- **No renaming of private functions** — keep `_fix_orphans`, `_parse_variants` etc. as-is (remove `_` prefix only if making them module-public)
- **No circular imports** — dataclasses in models.py, everything else imports from models. If circular import is unavoidable, use inline import with `# Circular import: <reason>` comment per AGENTS.md.

---

## Verification Strategy (MANDATORY)

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: YES (pytest in pyproject.toml)
- **Automated tests**: TDD — write failing tests first, then extract code to make them pass
- **Framework**: pytest with poetry (`poetry run pytest`)
- **Each task follows**: RED (write test for function to extract) → GREEN (move function, update imports) → REFACTOR (clean up if needed)

### QA Policy
Every task MUST include agent-executed QA scenarios.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Unit tests**: Use Bash (`poetry run pytest path/to/test.py -v`)
- **Integration tests**: Use Bash (`poetry run pytest tests/ -v`)
- **Golden build**: Use Bash (build before + after, diff output)
- **Import verification**: Use Bash (`python -c "from diablaq_site.builder import build_site"`)

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Foundation — must complete before any extraction):
├── Task 1: Create golden build snapshot [quick]
├── Task 2: Create test infrastructure (conftest.py + fixtures) [quick]

Wave 2 (Extract leaf modules — MAX PARALLEL, no interdependencies):
├── Task 3: Extract models.py (9 dataclasses) [quick]
├── Task 4: Extract text.py (orphan fixing) [quick]
├── Task 5: Extract validation.py (ISBN + variant constants) [quick]
├── Task 6: Extract images.py (aspect + thumbnails) [quick]
├── Task 7: Extract urls.py (canonical URLs + slugify) [quick]
├── Task 8: Extract io.py (write_html + copy_tree) [quick]

Wave 3 (Extract modules with internal dependencies):
├── Task 9: Extract parsing.py (depends: models, text, validation) [unspecified-high]
├── Task 10: Extract rendering.py (depends: models) [quick]

Wave 4 (Orchestrator + final verification):
├── Task 11: Refactor builder.py into slim orchestrator (depends: all extractions) [deep]
├── Task 12: Golden build comparison (depends: Task 11) [quick]

Wave FINAL (After ALL tasks — independent review):
├── Task F1: Plan compliance audit [deep, subagent_type=oracle]
├── Task F2: Code quality review [unspecified-high]
├── Task F3: Real QA — full build + output verification [unspecified-high]
├── Task F4: Scope fidelity check [deep]

Critical Path: Task 1 → Task 2 → Task 3 → Tasks 4-8 (parallel) → Tasks 9-10 (parallel) → Task 11 → Task 12 → F1-F4 (parallel)
Parallel Speedup: ~50% faster than sequential
Max Concurrent: 6 (Wave 2)
```

### Dependency Matrix

| Task | Depends On | Blocks |
|------|-----------|--------|
| 1 | — | 12 |
| 2 | — | 3-10 |
| 3 | 2 | 9, 10, 11 |
| 4 | 2 | 9, 11 |
| 5 | 2 | 9, 11 |
| 6 | 2 | 11 |
| 7 | 2 | 11 |
| 8 | 2 | 11 |
| 9 | 3, 4, 5 | 11 |
| 10 | 3 | 11 |
| 11 | 3-10 | 12 |
| 12 | 1, 11 | F1-F4 |
| F1-F4 | 12 | — |

### Agent Dispatch Summary

- **Wave 1**: 2 tasks — T1 → `quick`, T2 → `quick`
- **Wave 2**: 6 tasks — T3-T8 → all `quick`
- **Wave 3**: 2 tasks — T9 → `unspecified-high`, T10 → `quick`
- **Wave 4**: 2 tasks — T11 → `deep`, T12 → `quick`
- **FINAL**: 4 tasks — F1 → `deep` (subagent_type=oracle), F2-F3 → `unspecified-high`, F4 → `deep`

---

## TODOs

- [x] 1. Create golden build snapshot

  **What to do**:
  - Run `poetry run diablaq-build --out /tmp/dist-golden` to generate the current (pre-refactor) output
  - Create a manifest of all output files with their SHA256 checksums: `find /tmp/dist-golden -type f -exec sha256sum {} + | sort > /tmp/golden-manifest.txt`
  - Copy the golden snapshot to `.sisyphus/evidence/golden-build/` for later comparison
  - Copy the manifest to `.sisyphus/evidence/golden-manifest.txt`

  **Must NOT do**:
  - Do not modify any source files
  - Do not change builder.py in any way

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Single command execution + file copy, no code changes
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 2)
  - **Parallel Group**: Wave 1 (with Task 2)
  - **Blocks**: Task 12
  - **Blocked By**: None

  **References**:

  **Pattern References**:
  - `diablaq_site/cli.py:24-32` — CLI entry point showing how `diablaq-build --out` works
  - `pyproject.toml` lines with `[project.scripts]` — the `diablaq-build` console script definition

  **Acceptance Criteria**:
  - [ ] `/tmp/dist-golden/` directory exists with HTML files
  - [ ] `.sisyphus/evidence/golden-manifest.txt` exists with checksums
  - [ ] `.sisyphus/evidence/golden-build/` directory is a copy of the full output

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Golden build produces expected output structure
    Tool: Bash
    Preconditions: poetry install completed, diablaq-build CLI available
    Steps:
      1. Run: poetry run diablaq-build --out /tmp/dist-golden
      2. Assert exit code is 0
      3. Run: ls /tmp/dist-golden/index.html
      4. Assert file exists
      5. Run: find /tmp/dist-golden -name '*.html' | wc -l
      6. Assert count > 50 (site has 71+ content files)
      7. Run: find /tmp/dist-golden -type f -exec sha256sum {} + | sort > /tmp/golden-manifest.txt
      8. Assert /tmp/golden-manifest.txt has > 50 lines
    Expected Result: Build succeeds, manifest created with 50+ file checksums
    Failure Indicators: Non-zero exit code, missing index.html, fewer than 50 HTML files
    Evidence: .sisyphus/evidence/task-1-golden-build.txt
  ```

  **Commit**: YES (group with Task 2)
  - Message: `chore(tests): add golden build snapshot and test infrastructure`
  - Files: `.sisyphus/evidence/golden-manifest.txt`
  - Pre-commit: none (no code changes)

- [x] 2. Create test infrastructure (conftest.py + shared fixtures)

  **What to do**:
  - Create `tests/conftest.py` with shared pytest fixtures:
    - `repo_root` fixture returning `Path(__file__).resolve().parents[1]`
    - `build_output` fixture that builds site to tmp_path and returns the output dir
    - `sample_frontmatter` fixture providing minimal valid edition/project/person/blog YAML+Markdown strings
    - `minimal_content_tree` fixture that creates a minimal content/ directory in tmp_path with one project, one edition, one person, one page, one blog post — using synthetic test data, not real content
  - Verify existing tests still pass after adding conftest.py: `poetry run pytest tests/test_blog_build.py tests/test_edition_variants.py -v`
  - Ensure `poetry install` has been run so `diablaq_site` is importable

  **Must NOT do**:
  - Do not modify existing test files (test_blog_build.py, test_edition_variants.py)
  - Do not add unnecessary fixtures — only what's needed for upcoming module tests
  - Do not add pytest plugins or extra test dependencies

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Creating one test file with fixtures, straightforward Python
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 1)
  - **Parallel Group**: Wave 1 (with Task 1)
  - **Blocks**: Tasks 3-10
  - **Blocked By**: None

  **References**:

  **Pattern References**:
  - `tests/test_edition_variants.py:30-65` — Existing pattern for creating minimal work_root with symlinked templates/css/img
  - `tests/test_blog_build.py:7-10` — Pattern for repo_root resolution

  **API/Type References**:
  - `diablaq_site/builder.py:603-610` — `build_site(root: Path, out_dir: Path)` signature

  **Test References**:
  - `tests/test_edition_variants.py:33-50` — How symlinks to templates/css/img are created for isolated test builds

  **Acceptance Criteria**:
  - [ ] `tests/conftest.py` exists with fixtures: repo_root, sample_frontmatter, minimal_content_tree
  - [ ] `poetry run pytest tests/test_blog_build.py tests/test_edition_variants.py -v` passes (existing tests unbroken)
  - [ ] `poetry run pytest tests/conftest.py --collect-only` shows no collection errors

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Existing tests pass with new conftest.py
    Tool: Bash
    Preconditions: poetry install completed
    Steps:
      1. Run: poetry run pytest tests/test_blog_build.py tests/test_edition_variants.py -v
      2. Assert all tests pass (exit code 0)
      3. Assert output contains 'passed'
    Expected Result: All pre-existing tests pass, no import errors
    Failure Indicators: ImportError, test failures, conftest syntax errors
    Evidence: .sisyphus/evidence/task-2-existing-tests-pass.txt

  Scenario: Conftest fixtures are importable and valid
    Tool: Bash
    Preconditions: conftest.py created
    Steps:
      1. Run: poetry run pytest --collect-only -q tests/
      2. Assert exit code 0 (collection succeeds)
      3. Assert output lists existing test functions
    Expected Result: Pytest collects all tests without errors
    Failure Indicators: Collection errors, conftest import errors
    Evidence: .sisyphus/evidence/task-2-conftest-collection.txt
  ```

  **Commit**: YES (group with Task 1)
  - Message: `chore(tests): add golden build snapshot and test infrastructure`
  - Files: `tests/conftest.py`
  - Pre-commit: `poetry run pytest tests/ -v`

- [x] 3. Extract models.py (9 dataclasses)

  **What to do**:
  - TDD: Write `tests/test_models.py` FIRST with tests for:
    - Import all 9 dataclasses from `diablaq_site.models`
    - Instantiate each dataclass with minimal valid data
    - Verify frozen behavior (attempting to set attribute raises FrozenInstanceError)
    - Verify Edition.is_new and Edition.is_announcement fields exist (bool type)
    - Verify EditionVariant field types: `binding: str | None`, `version: str | None`, `isbn13: str` (required), `limited_print_run: int | None`, `numbered: bool`, `buy_links: list[BuyLink]`, `specs: dict[str, str]` — note: NO default values on any field
  - Run tests — they should FAIL (models.py doesn't exist yet)
  - Create `diablaq_site/models.py`:
    - Move all 9 dataclasses from builder.py (lines 56-181): BuyLink, EditionVariant, Creator, ImageRef, Edition, Project, Person, Page, BlogPost
    - Move `from __future__ import annotations` and `from dataclasses import dataclass` imports
    - Move `from datetime import date` (used in Edition, BlogPost type hints)
    - Move `from pathlib import Path` (used in type hints)
  - Update `diablaq_site/builder.py` to import from models: `from diablaq_site.models import BuyLink, EditionVariant, Creator, ImageRef, Edition, Project, Person, Page, BlogPost`
  - Run tests — they should PASS
  - Run existing tests to verify no regression

  **Must NOT do**:
  - Do not rename any dataclass or field
  - Do not add methods, properties, or validators to dataclasses
  - Do not change default values or field ordering
  - Do not add `__all__` to models.py

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Mechanical code move + simple test, no complex logic
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO (first extraction, must complete before other Wave 2 tasks)
  - **Parallel Group**: Wave 2 (lead task)
  - **Blocks**: Tasks 4-10, Task 11
  - **Blocked By**: Task 2

  **References**:

  **Pattern References**:
  - `diablaq_site/builder.py:56-181` — All 9 dataclass definitions to move (exact lines)
  - `diablaq_site/builder.py:1-6` — Module-level imports needed by dataclasses

  **API/Type References**:
  - `diablaq_site/builder.py:62-96` — EditionVariant fields with complex defaults (most important to preserve exactly)
  - `diablaq_site/builder.py:111-138` — Edition fields including is_new, is_announcement, status_label

  **Acceptance Criteria**:
  - [ ] `diablaq_site/models.py` exists with all 9 dataclasses
  - [ ] `tests/test_models.py` exists with tests for each dataclass
  - [ ] `poetry run pytest tests/test_models.py -v` passes
  - [ ] `poetry run pytest tests/ -v` passes (all tests including existing)
  - [ ] `python -c "from diablaq_site.models import Edition, Project, Person"` succeeds

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: All dataclasses importable from models module
    Tool: Bash
    Preconditions: models.py created, poetry install done
    Steps:
      1. Run: poetry run python -c "from diablaq_site.models import BuyLink, EditionVariant, Creator, ImageRef, Edition, Project, Person, Page, BlogPost; print('All 9 imported')"
      2. Assert output contains 'All 9 imported'
      3. Run: poetry run pytest tests/test_models.py -v
      4. Assert all tests pass
    Expected Result: All 9 dataclasses importable, all model tests pass
    Failure Indicators: ImportError, missing dataclass, field mismatch
    Evidence: .sisyphus/evidence/task-3-models-import.txt

  Scenario: Existing integration tests still pass after extraction
    Tool: Bash
    Preconditions: builder.py updated with import from models
    Steps:
      1. Run: poetry run pytest tests/test_blog_build.py tests/test_edition_variants.py -v
      2. Assert all tests pass (exit code 0)
    Expected Result: Zero regressions in existing tests
    Failure Indicators: ImportError in builder.py, test failures
    Evidence: .sisyphus/evidence/task-3-regression-check.txt
  ```

  **Commit**: YES (group with Wave 2)
  - Message: `refactor(builder): extract leaf modules (models, text, validation, images, urls, io)`
  - Files: `diablaq_site/models.py`, `tests/test_models.py`, `diablaq_site/builder.py`
  - Pre-commit: `poetry run pytest tests/ -v`

- [x] 4. Extract text.py (Polish typographic helpers)

  **What to do**:
  - TDD: Write `tests/test_text.py` FIRST with tests for:
    - `fix_orphans(html)` correctly inserts `&nbsp;` (HTML entity) after Polish orphan words. The actual word list is: a, i, o, u, w, z, k, do, na, od, po, za, ze, we, ku, to, co, że, by, są, je, go, mu, ją, mi, ty, on, my, wy
    - Empty string input returns empty string
    - HTML without orphan words is returned unchanged
    - Multiple orphan words in one string all get fixed
    - The function iterates until no more substitutions are made (handles overlapping patterns)
  - Run tests — they should FAIL
  - Create `diablaq_site/text.py`:
    - Move `_ORPHAN_WORDS` set (lines 19-26)
    - Move `_ORPHAN_PATTERN` compiled regex (lines 29-32)
    - Move `_fix_orphans` function (lines 35-52)
    - Rename to `fix_orphans` (remove underscore — now module-public)
  - Update `diablaq_site/builder.py` to import: `from diablaq_site.text import fix_orphans`
  - Update the call site in `_read_markdown_file` (which calls `_fix_orphans`)
  - Run tests — they should PASS
  - Run existing tests to verify no regression

  **Must NOT do**:
  - Do not change the regex pattern or orphan word list
  - Do not add new text processing functions

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Small function extraction (~20 lines), simple regex logic
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 5-8)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 9, Task 11
  - **Blocked By**: Task 3 (models must be extracted first so builder.py imports are stable)

  **References**:

  **Pattern References**:
  - `diablaq_site/builder.py:18-52` — `_ORPHAN_WORDS` (lines 19-26), `_ORPHAN_PATTERN` (lines 29-32), and `_fix_orphans` function (lines 35-52) to move
  - `diablaq_site/builder.py:235` — Call site: `_fix_orphans(html_body)` inside `_read_markdown_file`

  **Acceptance Criteria**:
  - [ ] `diablaq_site/text.py` exists with `fix_orphans` function
  - [ ] `tests/test_text.py` exists with happy path + edge case tests
  - [ ] `poetry run pytest tests/test_text.py -v` passes
  - [ ] `poetry run pytest tests/ -v` passes (all tests)

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Orphan fixing works correctly for Polish text
    Tool: Bash
    Preconditions: text.py created
    Steps:
      1. Run: poetry run python -c "from diablaq_site.text import fix_orphans; result = fix_orphans('To jest w domu i na polu'); print(repr(result))"
      2. Assert output contains '&nbsp;' (HTML entity non-breaking space, NOT \xa0 Unicode)
      3. Run: poetry run pytest tests/test_text.py -v
      4. Assert all tests pass
    Expected Result: Non-breaking spaces inserted after Polish orphan words
    Failure Indicators: Missing &nbsp;, regex errors, ImportError
    Evidence: .sisyphus/evidence/task-4-text-orphans.txt

  Scenario: No regression in existing tests
    Tool: Bash
    Steps:
      1. Run: poetry run pytest tests/test_blog_build.py tests/test_edition_variants.py -v
      2. Assert all pass
    Expected Result: Zero regressions
    Evidence: .sisyphus/evidence/task-4-regression.txt
  ```

  **Commit**: YES (group with Wave 2)
  - Message: `refactor(builder): extract leaf modules (models, text, validation, images, urls, io)`
  - Files: `diablaq_site/text.py`, `tests/test_text.py`, `diablaq_site/builder.py`
  - Pre-commit: `poetry run pytest tests/ -v`

- [x] 5. Extract validation.py (ISBN validation + variant constants)

  **What to do**:
  - TDD: Write `tests/test_validation.py` FIRST with tests for:
    - `normalize_isbn13('978-83-123-4567-8')` returns `'9788312345678'`
    - `normalize_isbn13('9788312345678')` returns same (already clean)
    - `is_valid_isbn13('9788312345678')` returns True for valid checksum
    - `is_valid_isbn13('9788312345679')` returns False for invalid checksum
    - `is_valid_isbn13('978-83-123-4567-8')` works with hyphens (after normalization)
    - Edge cases: empty string, too short, non-digits
    - Constants `ALLOWED_BINDINGS`, `ALLOWED_VERSIONS`, `ALLOWED_VARIANT_KINDS` are importable sets
  - Run tests — they should FAIL
  - Create `diablaq_site/validation.py`:
    - Move `_normalize_isbn13` (lines 380-382), rename to `normalize_isbn13`
    - Move `_is_valid_isbn13` (lines 385-399), rename to `is_valid_isbn13`
    - Move `_ALLOWED_BINDINGS`, `_ALLOWED_VERSIONS`, `_ALLOWED_VARIANT_KINDS` constants (lines ~401-405), rename to `ALLOWED_BINDINGS`, etc.
  - Update builder.py imports
  - Run tests — PASS

  **Must NOT do**:
  - Do not change ISBN validation logic
  - Do not add new validation functions beyond what's being extracted

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Pure function extraction, well-defined inputs/outputs
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 4, 6-8)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 9, Task 11
  - **Blocked By**: Task 3

  **References**:

  **Pattern References**:
  - `diablaq_site/builder.py:380-399` — ISBN normalization and validation functions
  - `diablaq_site/builder.py:401-405` — Variant kind/binding/version allowed-value constants
  - `tests/test_edition_variants.py:67-95` — Existing ISBN test pattern (parametrized, tests via build_site)

  **Acceptance Criteria**:
  - [ ] `diablaq_site/validation.py` exists with ISBN functions + variant constants
  - [ ] `tests/test_validation.py` passes with unit-level ISBN tests
  - [ ] `poetry run pytest tests/ -v` passes (all tests)

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: ISBN validation works correctly
    Tool: Bash
    Steps:
      1. Run: poetry run python -c "from diablaq_site.validation import normalize_isbn13, is_valid_isbn13; print(is_valid_isbn13(normalize_isbn13('978-83-66712-90-1')))"
      2. Assert output is 'True' (or a valid ISBN from the repo)
      3. Run: poetry run python -c "from diablaq_site.validation import ALLOWED_BINDINGS; print(type(ALLOWED_BINDINGS))"
      4. Assert output shows set or frozenset
    Expected Result: ISBN validation and constants importable and working
    Evidence: .sisyphus/evidence/task-5-validation.txt
  ```

  **Commit**: YES (group with Wave 2)
  - Files: `diablaq_site/validation.py`, `tests/test_validation.py`, `diablaq_site/builder.py`
  - Pre-commit: `poetry run pytest tests/ -v`

- [x] 6. Extract images.py (cover aspect + thumbnail generation)

  **What to do**:
  - TDD: Write `tests/test_images.py` FIRST with tests for:
    - `get_cover_aspect_class(cover_path, root)` returns `'cover--tall'` for a tall image (ratio < 0.6)
    - `get_cover_aspect_class(cover_path, root)` returns `'cover--wide'` for a wide image (ratio > 0.75)
    - `get_cover_aspect_class(cover_path, root)` returns `'cover--standard'` for ratios between 0.6 and 0.75
    - `get_cover_aspect_class(path, root)` returns `'cover--standard'` for non-existent file (NOT empty string — this is the current behavior)
    - `generate_thumbnail(source, dest, size=(300,300))` creates a JPEG thumbnail
    - `thumb_path_from_photo(photo_path)` returns path with `_thumb.jpg` suffix
    - Create small test images (e.g., 100x200, 200x100, 150x150) in tmp_path using PIL for tests
  - Run tests — FAIL
  - Create `diablaq_site/images.py`:
    - Move `_get_cover_aspect_class` (lines 243-271)
    - Move `_generate_thumbnail` (lines 272-285)
    - Move `_thumb_path_from_photo` (lines 286-289)
    - Remove `_` prefixes
  - Update builder.py imports
  - Run tests — PASS

  **Must NOT do**:
  - Do not change aspect ratio thresholds or thumbnail size defaults
  - Do not add image optimization (WebP, etc.) — that's a new feature

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Three small functions with clear PIL dependency
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 4-5, 7-8)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 11
  - **Blocked By**: Task 3

  **References**:

  **Pattern References**:
  - `diablaq_site/builder.py:243-289` — All three image functions to move
  - `diablaq_site/builder.py:1120-1127` — How thumbnails are generated in build_site (call pattern)

  **Acceptance Criteria**:
  - [ ] `diablaq_site/images.py` exists with 3 functions
  - [ ] `tests/test_images.py` passes with synthetic image tests
  - [ ] `poetry run pytest tests/ -v` passes

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Aspect class detection works
    Tool: Bash
    Steps:
      1. Run: poetry run python -c "from diablaq_site.images import get_cover_aspect_class; print('imported')"
      2. Assert output is 'imported'
      3. Run: poetry run pytest tests/test_images.py -v
      4. Assert all tests pass
    Expected Result: All image helper functions work correctly
    Evidence: .sisyphus/evidence/task-6-images.txt
  ```

  **Commit**: YES (group with Wave 2)
  - Files: `diablaq_site/images.py`, `tests/test_images.py`, `diablaq_site/builder.py`
  - Pre-commit: `poetry run pytest tests/ -v`

- [x] 7. Extract urls.py (canonical URLs + tag slugification)

  **What to do**:
  - TDD: Write `tests/test_urls.py` FIRST with tests for:
    - `canonical_project_url(line='diablaq', slug='belzebubs')` returns `'/publikacje/belzebubs/'`
    - `canonical_project_url(line='dobre-licho', slug='some-slug')` returns `'/dobre-licho/some-slug/'`
    - `canonical_project_url(line='mecenat', slug='x')` returns `'/mecenat/x/'`
    - `canonical_project_url(line='studio', slug='x')` returns `'/studio/x/'`
    - `canonical_edition_url(line=, project_slug=, edition_slug='index')` returns project URL (delegates to `canonical_project_url`) — NO `is_index` parameter; uses `edition_slug == "index"` check as current code does
    - `canonical_edition_url(line=, project_slug=, edition_slug='vol-1')` returns full edition URL with all path segments
    - `slugify_tag('Tag Name')` returns URL-encoded slug
  - Run tests — FAIL
  - Create `diablaq_site/urls.py`:
    - Move `_canonical_project_url` (lines 578-586)
    - Move `_canonical_edition_url` (lines 589-601)
    - Move `_slugify_tag` (lines 182-186)
    - Remove `_` prefixes
  - Update builder.py imports
  - Run tests — PASS

  **Must NOT do**:
  - Do not change URL patterns — they affect all existing links and SEO
  - Do not add new URL generation functions

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Pure functions with string inputs/outputs, well-defined
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 4-6, 8)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 11
  - **Blocked By**: Task 3

  **References**:

  **Pattern References**:
  - `diablaq_site/builder.py:578-601` — URL generation functions to move
  - `diablaq_site/builder.py:182-186` — `_slugify_tag` function
  - `content/projects/belzebubs/project.md` — Example project with `line: diablaq` to verify URL pattern

  **Acceptance Criteria**:
  - [ ] `diablaq_site/urls.py` exists with 3 functions
  - [ ] `tests/test_urls.py` passes with URL pattern tests
  - [ ] `poetry run pytest tests/ -v` passes

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: URL generation matches expected patterns
    Tool: Bash
    Steps:
      1. Run: poetry run python -c "from diablaq_site.urls import canonical_project_url; print(canonical_project_url(line='diablaq', slug='belzebubs'))"
      2. Assert output is '/publikacje/belzebubs/'
      3. Run: poetry run pytest tests/test_urls.py -v
      4. Assert all tests pass
    Expected Result: URLs match current patterns exactly
    Evidence: .sisyphus/evidence/task-7-urls.txt
  ```

  **Commit**: YES (group with Wave 2)
  - Files: `diablaq_site/urls.py`, `tests/test_urls.py`, `diablaq_site/builder.py`
  - Pre-commit: `poetry run pytest tests/ -v`

- [x] 8. Extract io.py (file writing + directory copying)

  **What to do**:
  - TDD: Write `tests/test_io.py` FIRST with tests for:
    - `write_html(path, html_content)` creates file and parent dirs
    - `write_html(path, html_content)` writes UTF-8 content
    - `copy_tree(src, dst)` copies directory tree
    - `copy_tree(src, dst)` is no-op when src doesn't exist (no error)
  - Run tests — FAIL
  - Create `diablaq_site/io.py`:
    - Move `_write_html` (lines 292-294)
    - Move `_copy_tree` (lines 237-241)
    - Remove `_` prefixes
  - Update builder.py imports
  - Run tests — PASS

  **Must NOT do**:
  - Do not add logging to IO operations
  - Do not change write encoding (must stay UTF-8)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Two tiny functions, filesystem ops with tmp_path testing
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 4-7)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 11
  - **Blocked By**: Task 3

  **References**:

  **Pattern References**:
  - `diablaq_site/builder.py:237-241` — `_copy_tree` function
  - `diablaq_site/builder.py:292-294` — `_write_html` function

  **Acceptance Criteria**:
  - [ ] `diablaq_site/io.py` exists with 2 functions
  - [ ] `tests/test_io.py` passes
  - [ ] `poetry run pytest tests/ -v` passes

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: write_html creates file with correct encoding
    Tool: Bash
    Steps:
      1. Run: poetry run pytest tests/test_io.py -v
      2. Assert all tests pass
    Expected Result: File writing and directory copying work correctly
    Evidence: .sisyphus/evidence/task-8-io.txt
  ```

  **Commit**: YES (group with Wave 2)
  - Message: `refactor(builder): extract leaf modules (models, text, validation, images, urls, io)`
  - Files: `diablaq_site/io.py`, `tests/test_io.py`, `diablaq_site/builder.py`
  - Pre-commit: `poetry run pytest tests/ -v`

- [ ] 9. Extract parsing.py (content/frontmatter parsing)

  **What to do**:
  - TDD: Write `tests/test_parsing.py` FIRST with tests for:
    - `read_markdown_file(path)` returns (metadata_dict, html_body_string)
    - `read_markdown_file` applies orphan fixing to output HTML
    - `parse_date('2024-01-15', source_path=Path('test.md'))` returns `date(2024, 1, 15)` — note: requires keyword-only `source_path` param
    - `parse_date('invalid', source_path=Path('test.md'))` raises ValueError with source_path in message
    - `parse_optional_date(None, source_path=Path('test.md'))` returns None
    - `parse_optional_date('2024-01-15', source_path=Path('test.md'))` returns date object
    - `derive_flags(release_date=, today=)` returns correct (is_new, is_announcement) tuples — note: keyword-only args:
      - Future date → (False, True)
      - Within 6 weeks → (True, False)
      - Old date → (False, False)
      - None → (False, True)
    - `coerce_str_list(value)` handles str, list, None
    - `pick_cover(meta)` extracts cover_image and cover_alt — note: NO source_path parameter
    - `parse_image_list(meta, key, *, source_path)` returns list of ImageRef — note: takes `meta` dict + `key` string + keyword-only `source_path`
    - `parse_buy_links(meta, source_path)` returns list of BuyLink
    - `parse_variants(meta, source_path)` returns list of EditionVariant (happy path + error cases)
    - `parse_creators(meta, source_path)` handles both legacy list and dict formats
    - `parse_specs(meta)` normalizes key/value pairs — note: NO source_path parameter
    - Error cases: missing required fields, wrong types, invalid ISBN in variant
  - Run tests — FAIL
  - Create `diablaq_site/parsing.py`:
    - Move ALL parsing functions from builder.py:
      - `_read_markdown_file` (lines 227-236) — depends on `text.fix_orphans`
      - `_parse_date` (lines 187-196)
      - `_parse_optional_date` (lines 197-204)
      - `_derive_flags` (lines 205-226)
      - `_coerce_str_list` (lines 302-307)
    - Move `_pick_cover` (lines 310-329) — note: signature is `_pick_cover(meta: dict)` with NO source_path param
      - `_parse_image_list` (lines 332-351) — signature: `_parse_image_list(meta: dict, key: str, *, source_path: Path)` — creates ImageRef from models
      - `_as_str` (lines 354-355)
      - `_parse_buy_links` (lines 358-377) — creates BuyLink from models
      - `_parse_variants` (lines 407-517) — uses validation.normalize_isbn13, validation.is_valid_isbn13, validation.ALLOWED_* constants; creates EditionVariant from models
      - `_parse_creators` (lines 520-557) — creates Creator from models
      - `_parse_specs` (lines 560-575) — signature: `_parse_specs(meta: dict)` — NO source_path param
    - Import dependencies: `from diablaq_site.models import ...`, `from diablaq_site.text import fix_orphans`, `from diablaq_site.validation import ...`
    - Remove `_` prefixes on all functions
    - **CRITICAL**: Preserve the synthetic dict wrapper in `_parse_variants` calling `_parse_buy_links({"buy_links": item.get("buy_links")}, source_path=source_path)` exactly as-is
  - Update builder.py to import from parsing
  - Run tests — PASS

  **Must NOT do**:
  - Do not refactor internal function signatures (especially the dict-wrapper pattern in _parse_variants)
  - Do not add new validation beyond what currently exists
  - Do not change error messages (tests may depend on exact wording)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Largest extraction with most internal dependencies; 14 functions, cross-module imports, careful coupling management
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 10)
  - **Parallel Group**: Wave 3 (with Task 10)
  - **Blocks**: Task 11
  - **Blocked By**: Tasks 3 (models), 4 (text), 5 (validation)

  **References**:

  **Pattern References**:
  - `diablaq_site/builder.py:182-575` — All parsing functions to move (exact line ranges per function listed above)
  - `diablaq_site/builder.py:407-517` — `_parse_variants` — most complex function, calls 6 others internally

  **API/Type References**:
  - `diablaq_site/models.py` — BuyLink, EditionVariant, Creator, ImageRef dataclasses used as return types
  - `diablaq_site/text.py` — `fix_orphans` called by `read_markdown_file`
  - `diablaq_site/validation.py` — ISBN functions + ALLOWED_* constants used by `parse_variants`

  **External References**:
  - `python-frontmatter` — Used by `read_markdown_file` for YAML frontmatter parsing
  - `markdown` library — Used by `read_markdown_file` for Markdown → HTML conversion

  **Acceptance Criteria**:
  - [ ] `diablaq_site/parsing.py` exists with all 14 parsing functions
  - [ ] `tests/test_parsing.py` exists with comprehensive unit tests (happy paths + error cases)
  - [ ] `poetry run pytest tests/test_parsing.py -v` passes
  - [ ] `poetry run pytest tests/ -v` passes (all tests)
  - [ ] The synthetic dict wrapper in parse_variants is preserved exactly

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: All parsing functions importable and working
    Tool: Bash
    Steps:
      1. Run: poetry run python -c "from diablaq_site.parsing import read_markdown_file, parse_date, parse_variants, parse_creators; print('All imported')"
      2. Assert output is 'All imported'
      3. Run: poetry run pytest tests/test_parsing.py -v
      4. Assert all tests pass
    Expected Result: All parsing functions work correctly in isolation
    Evidence: .sisyphus/evidence/task-9-parsing.txt

  Scenario: Variant parsing with ISBN validation integration
    Tool: Bash
    Steps:
      1. Run: poetry run pytest tests/test_parsing.py -k 'variant' -v
      2. Assert tests covering valid/invalid ISBN in variants pass
    Expected Result: ISBN validation works through parsing pipeline
    Evidence: .sisyphus/evidence/task-9-variants.txt

  Scenario: No regression in full test suite
    Tool: Bash
    Steps:
      1. Run: poetry run pytest tests/ -v
      2. Assert all pass (exit code 0)
    Expected Result: Zero regressions
    Evidence: .sisyphus/evidence/task-9-regression.txt
  ```

  **Commit**: YES
  - Message: `refactor(builder): extract parsing and rendering modules`
  - Files: `diablaq_site/parsing.py`, `tests/test_parsing.py`, `diablaq_site/builder.py`
  - Pre-commit: `poetry run pytest tests/ -v`

- [ ] 10. Extract rendering.py (template rendering helpers)

  **What to do**:
  - TDD: Write `tests/test_rendering.py` FIRST with tests for:
    - `render_template(env, template_name, **context)` renders a Jinja2 template with given context
    - Function accepts nav_projects and site_url as explicit parameters
    - Template not found raises appropriate Jinja2 error
    - Context variables are accessible in template
  - Run tests — FAIL
  - Create `diablaq_site/rendering.py`:
    - Move `_render` (lines 297-299)
    - Create a public `render_template(env, template_name, *, nav_projects, site_url, **ctx)` that wraps `_render` with the standard context injection (replacing the nested closure in build_site)
    - Move the `_abs_url` helper logic into a `make_abs_url(site_url)` function that returns a callable (or just a simple `abs_url(site_url, path)` function)
  - Update builder.py to import from rendering
  - Remove the nested `render()` and `_abs_url()` closures from build_site and replace with rendering module calls
  - Run tests — PASS

  **Must NOT do**:
  - Do not change template variable names — templates depend on them
  - Do not add template caching or other optimizations

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Small extraction, but requires careful closure-to-params conversion
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 9)
  - **Parallel Group**: Wave 3 (with Task 9)
  - **Blocks**: Task 11
  - **Blocked By**: Task 3 (models)

  **References**:

  **Pattern References**:
  - `diablaq_site/builder.py:297-299` — `_render` function to move
  - `diablaq_site/builder.py:892-905` — Nested `render()` and `_abs_url()` closures in build_site that capture env, nav_projects, site_url — these closures define the interface the new module must replicate

  **API/Type References**:
  - `jinja2.Environment` — Passed to render functions
  - All 18 templates in `templates/` — Template names referenced in build_site render calls

  **Acceptance Criteria**:
  - [ ] `diablaq_site/rendering.py` exists with `render_template` + `abs_url` functions
  - [ ] `tests/test_rendering.py` passes
  - [ ] `poetry run pytest tests/ -v` passes

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Template rendering works with explicit params
    Tool: Bash
    Steps:
      1. Run: poetry run python -c "from diablaq_site.rendering import render_template; print('imported')"
      2. Assert output is 'imported'
      3. Run: poetry run pytest tests/test_rendering.py -v
      4. Assert all tests pass
    Expected Result: Rendering functions work without closures
    Evidence: .sisyphus/evidence/task-10-rendering.txt
  ```

  **Commit**: YES (group with Task 9)
  - Message: `refactor(builder): extract parsing and rendering modules`
  - Files: `diablaq_site/rendering.py`, `tests/test_rendering.py`, `diablaq_site/builder.py`
  - Pre-commit: `poetry run pytest tests/ -v`

- [ ] 11. Refactor builder.py into slim pipeline orchestrator

  **What to do**:
  This is the culmination task. After all modules are extracted, builder.py should be a slim orchestrator.
  - First, verify current state: `wc -l diablaq_site/builder.py` — should already be significantly reduced after Tasks 3-10
  - Refactor `build_site()` into a clear pipeline:
    1. `_init_environment(root, out_dir)` → returns (env, content_dir, out_dir, site_url)
    2. `_load_content(content_dir, root)` → returns (projects, editions, people, pages, blog_posts)
    3. `_process_content(projects, editions, people, blog_posts)` → returns (new_editions, announcements, newest_anytime, people_with_editions, nav_projects, sorted_blog)
    4. `_render_all(env, out_dir, site_url, nav_projects, ...)` → renders all pages
    5. `_finalize(root, out_dir, people)` → copies assets, generates thumbnails, copies CNAME
  - `build_site(root, out_dir)` becomes ~20 lines calling these 5 phases
  - Each phase function lives in builder.py (they orchestrate, not compute)
  - All computation is delegated to imported modules (parsing, rendering, images, etc.)
  - Run full test suite to verify

  **Must NOT do**:
  - Do not create new abstractions (no Pipeline class, no Builder pattern, no plugin system)
  - Do not change the content loading order (pages → projects/editions → people → blog)
  - Do not change the rendering order
  - Do not extract the pipeline phases into separate modules — they stay in builder.py as private functions

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Most complex task — restructuring 530 lines of orchestration while preserving exact behavior across 14 phases
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4 (sequential)
  - **Blocks**: Task 12
  - **Blocked By**: Tasks 3-10 (all extractions)

  **References**:

  **Pattern References**:
  - `diablaq_site/builder.py:603-1131` — Current build_site() function (will be significantly reduced after Tasks 3-10)
  - `diablaq_site/builder.py:892-905` — Current nested closure pattern (should be replaced by Task 10)

  **API/Type References**:
  - `diablaq_site/models.py` — All dataclasses used in orchestration
  - `diablaq_site/parsing.py` — All content loading/parsing functions
  - `diablaq_site/rendering.py` — Template rendering with explicit params
  - `diablaq_site/images.py` — Thumbnail generation
  - `diablaq_site/urls.py` — Canonical URL generation
  - `diablaq_site/io.py` — File writing, directory copying
  - `diablaq_site/text.py` — Typography (used by parsing, but may be needed directly)
  - `diablaq_site/validation.py` — Constants (used by parsing, but may be needed directly)

  **Acceptance Criteria**:
  - [ ] `diablaq_site/builder.py` is ~150 lines (down from 1131)
  - [ ] `build_site()` function is ~20 lines calling 5 phase functions
  - [ ] `poetry run pytest tests/ -v` passes (ALL tests)
  - [ ] `poetry run diablaq-build --out /tmp/dist-test` succeeds
  - [ ] `wc -l diablaq_site/builder.py` output is < 200

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Slim builder still produces correct output
    Tool: Bash
    Preconditions: All modules extracted (Tasks 3-10 complete)
    Steps:
      1. Run: wc -l diablaq_site/builder.py
      2. Assert line count < 200 (down from 1131)
      3. Run: poetry run diablaq-build --out /tmp/dist-refactored
      4. Assert exit code 0
      5. Run: find /tmp/dist-refactored -name '*.html' | wc -l
      6. Assert HTML file count matches golden build
    Expected Result: Builder is slim AND produces correct output
    Failure Indicators: Line count > 200, build failure, missing HTML files
    Evidence: .sisyphus/evidence/task-11-slim-builder.txt

  Scenario: build_site function is a clean pipeline
    Tool: Bash
    Steps:
      1. Run: grep -c 'def ' diablaq_site/builder.py
      2. Assert function count is ~6 (build_site + 5 phase functions)
      3. Run: poetry run pytest tests/ -v
      4. Assert all tests pass
    Expected Result: builder.py contains only orchestration, no business logic
    Evidence: .sisyphus/evidence/task-11-pipeline.txt
  ```

  **Commit**: YES
  - Message: `refactor(builder): slim down build_site orchestrator into 5-phase pipeline`
  - Files: `diablaq_site/builder.py`
  - Pre-commit: `poetry run pytest tests/ -v`

- [ ] 12. Golden build comparison (regression verification)

  **What to do**:
  - Run `poetry run diablaq-build --out /tmp/dist-refactored`
  - Generate manifest: `find /tmp/dist-refactored -type f -exec sha256sum {} + | sort > /tmp/refactored-manifest.txt`
  - Compare with golden manifest: `diff /tmp/golden-manifest.txt /tmp/refactored-manifest.txt`
  - If differences exist:
    - Identify which files differ
    - For HTML files: check if differences are only whitespace/timestamp related (acceptable) vs content differences (unacceptable)
    - Report any content differences as failures
  - Save comparison results to evidence

  **Must NOT do**:
  - Do not modify builder code to fix differences — report them and stop
  - Do not accept content-level differences as "close enough"

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Command execution and diff comparison, no code changes
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4 (after Task 11)
  - **Blocks**: F1-F4
  - **Blocked By**: Tasks 1, 11

  **References**:

  **Pattern References**:
  - `.sisyphus/evidence/golden-manifest.txt` — Golden build checksum manifest from Task 1
  - `.sisyphus/evidence/golden-build/` — Full golden build output for file-level diff if needed

  **Acceptance Criteria**:
  - [ ] `diff /tmp/golden-manifest.txt /tmp/refactored-manifest.txt` shows no differences (or only acceptable timestamp diffs)
  - [ ] Comparison results saved to evidence
  - [ ] If differences found: each one documented with explanation

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Refactored build is byte-identical to golden build
    Tool: Bash
    Preconditions: Golden build from Task 1 exists, Task 11 complete
    Steps:
      1. Run: poetry run diablaq-build --out /tmp/dist-refactored
      2. Assert exit code 0
      3. Run: find /tmp/dist-refactored -type f -exec sha256sum {} + | sort > /tmp/refactored-manifest.txt
      4. Run: diff /tmp/golden-manifest.txt /tmp/refactored-manifest.txt
      5. Assert diff output is empty (exit code 0)
    Expected Result: Zero differences between golden and refactored output
    Failure Indicators: Any line in diff output indicates a regression
    Evidence: .sisyphus/evidence/task-12-golden-comparison.txt

  Scenario: HTML file count matches
    Tool: Bash
    Steps:
      1. Run: find /tmp/dist-golden -name '*.html' | wc -l
      2. Run: find /tmp/dist-refactored -name '*.html' | wc -l
      3. Assert both counts are identical
    Expected Result: Same number of HTML files produced
    Evidence: .sisyphus/evidence/task-12-file-count.txt
  ```

  **Commit**: YES
  - Message: `test: verify golden build comparison passes after refactor`
  - Files: `.sisyphus/evidence/task-12-golden-comparison.txt`
  - Pre-commit: `poetry run pytest tests/ -v`

---
## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Rejection → fix → re-run.

- [ ] F1. **Plan Compliance Audit** — `deep` (run as `oracle` subagent, not category-based)
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, run command). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in .sisyphus/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `poetry run pytest`. Review all new/changed files for: `as any`/`@ts-ignore` equivalents, empty catches, print() in prod, commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, generic names (data/result/item/temp). Verify no function exceeds 50 lines. Verify no circular imports.
  Output: `Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real QA — Full Build + Output Verification** — `unspecified-high`
  Run `poetry run diablaq-build --out /tmp/dist-refactored`. Verify: all expected HTML files exist, no broken internal links (grep for href and check targets exist), templates render without Jinja errors, thumbnails generated. Compare against golden snapshot from Task 1.
  Output: `Build [PASS/FAIL] | Files [N expected/N found] | Diff [CLEAN/N differences] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff (git log/diff). Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance. Detect cross-task contamination. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **After Wave 1**: `chore(tests): add golden build snapshot and test infrastructure`
- **After Wave 2**: `refactor(builder): extract leaf modules (models, text, validation, images, urls, io)`
- **After Wave 3**: `refactor(builder): extract parsing and rendering modules`
- **After Wave 4**: `refactor(builder): slim down build_site orchestrator` + `test: verify golden build comparison passes`

---

## Success Criteria

### Verification Commands
```bash
poetry run pytest -v                              # Expected: all tests pass
poetry run pytest --tb=short 2>&1 | tail -1       # Expected: "X passed" with 0 failures
poetry run diablaq-build --out /tmp/dist-test      # Expected: successful build, exit code 0
diff -rq /tmp/dist-golden /tmp/dist-test           # Expected: no differences (or only timestamp-related)
python -c "from diablaq_site.builder import build_site; print('OK')"  # Expected: OK
wc -l diablaq_site/builder.py                      # Expected: ~150 lines (down from 1131)
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] All tests pass (existing + new)
- [ ] builder.py reduced to ~150 lines
- [ ] Each module has corresponding test file
- [ ] Golden build comparison passes
- [ ] cli.py unchanged and working
