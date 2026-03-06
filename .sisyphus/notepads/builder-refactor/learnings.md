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

---

## Task 3: Extract models.py (9 dataclasses)

### TDD Workflow Success

**Phase 1: RED (Tests Fail)**
- Wrote `tests/test_models.py` with 30 tests covering:
  - Import checks for all 9 dataclasses
  - Instantiation with realistic field values
  - Frozen behavior verification (FrozenInstanceError)
  - Field type assertions (especially EditionVariant critical fields)
- Tests FAILED with `ModuleNotFoundError: No module named 'diablaq_site.models'`
- This is correct TDD red phase

**Phase 2: GREEN (Tests Pass)**
- Created `diablaq_site/models.py` with all 9 dataclasses:
  1. BuyLink: label, url
  2. EditionVariant: binding, version, isbn13, limited_print_run, numbered, buy_links, specs (NO defaults)
  3. Creator: role, name, person_slug
  4. ImageRef: image, alt, caption
  5. Edition: 24 fields including is_new, is_announcement
  6. Project: 10 fields including line, legacy_landing
  7. Person: slug, name, photo, photo_thumb, html_bio, related_editions
  8. Page: slug, title, html_body
  9. BlogPost: url, slug, title, date, summary, cover_image, cover_alt, tags, html_body

- All tests passed (30/30)
- Maintained exact field signatures, types, and ordering from original builder.py

**Phase 3: Refactor (Update builder.py)**
- Added import block after line 15:
  ```python
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
  ```
- Removed original dataclass definitions (lines 55-181)
- Note: Removed `from dataclasses import dataclass` import (no longer needed in builder.py)

### Test Coverage Highlights

1. **EditionVariant Critical Fields**
   - `isbn13: str` has NO default value (correctly enforced)
   - Attempting to instantiate without `isbn13` raises TypeError
   - All 7 fields must be provided (no defaults on any field)

2. **Edition Boolean Fields**
   - `is_new: bool` and `is_announcement: bool` are distinct fields (not methods)
   - Both fields present and type-checkable

3. **Frozen Behavior**
   - All 9 dataclasses are frozen (`@dataclass(frozen=True)`)
   - Attempts to set attributes raise FrozenInstanceError
   - Test verified with `with pytest.raises(Exception)`

4. **Regression Check**
   - All existing tests still pass (test_edition_variants.py: 5/5)
   - Full regression: 35 passed (new models + existing variants)
   - Only pre-existing failure: test_blog_is_built (unrelated to refactoring)

### Files Created/Modified
- **Created**: `diablaq_site/models.py` (135 lines, 9 dataclasses)
- **Created**: `tests/test_models.py` (388 lines, 30 tests)
- **Modified**: `diablaq_site/builder.py` (removed 127 lines of dataclass defs, added 11 lines of import)

### Evidence Saved
- `.sisyphus/evidence/task-3-models-import.txt` — All 30 tests passing
- `.sisyphus/evidence/task-3-regression-check.txt` — Regression check (35 tests passing)


## Task 4: Extract text.py (_fix_orphans module)

### TDD Workflow Success

**Phase 1: RED (Tests Fail)**
- Wrote `tests/test_text.py` with 20 comprehensive tests covering:
  - Module imports and constant existence
  - Empty string handling
  - Single and multiple orphan words with proper spacing
  - Case-insensitive matching (re.IGNORECASE)
  - Word boundary requirements (space before AND after)
  - Sentence/newline boundaries
  - Punctuation edge cases
  - Overlapping patterns and iterative replacement
- Tests FAILED initially with `ModuleNotFoundError: No module named 'diablaq_site.text'`
- This is correct TDD red phase

**Phase 2: GREEN (Tests Pass)**
- Created `diablaq_site/text.py` with exact code from builder.py:
  - `_ORPHAN_WORDS` constant (27 Polish orphan words in a set)
  - `_ORPHAN_PATTERN` regex (pre-compiled pattern)
  - `_fix_orphans(text: str) -> str` function (replaces spaces after orphan words with `&nbsp;`)
- All 20 tests passed (100%)
- Implementation moved AS-IS, no refactoring or logic changes

**Phase 3: Refactor (Update builder.py)**
- Added import after line 32 (after images import):
  ```python
  from diablaq_site.text import _fix_orphans
  ```
- Removed original code (lines 35-70 in original numbering, was 29 lines of definition)
- Function now imported and re-exported via builder.py

### Critical Implementation Details

1. **Regex Pattern Behavior**
   - Pattern requires whitespace BEFORE and AFTER the orphan word
   - Matches: ` a test` → ` a&nbsp;test` (space before and after)
   - No match: `a test` (no space before)
   - No match: ` a!` (no space after)
   - Uses `re.IGNORECASE` so `A` and `a` both match

2. **HTML Entity Usage**
   - Uses `&nbsp;` (HTML entity), not `\xa0` (Unicode character)
   - This is critical for correct rendering in templates

3. **Iterative Replacement**
   - Function iterates until no more replacements (while loop)
   - Handles overlapping patterns correctly: ` a i to ` → ` a&nbsp;i&nbsp;to&nbsp;`

### Test Coverage Highlights

- 20 tests covering all edge cases
- Tests specifically verify:
  - Whitespace requirements (before AND after)
  - Case insensitivity
  - Boundary conditions (empty string, leading/trailing)
  - Overlapping patterns via iteration
  - Punctuation handling
  - Newline as valid whitespace

### Files Created/Modified

- **Created**: `diablaq_site/text.py` (37 lines: 2 constants + 1 function)
- **Created**: `tests/test_text.py` (176 lines, 20 tests)
- **Modified**: `diablaq_site/builder.py` (added 1-line import, removed 36-70 lines)

### Regression Check Results

- Full test suite: **143 passed, 1 pre-existing failed**
- New text tests: **20/20 passed**
- Models tests: **30/30 passed** (from Task 3)
- Variants tests: **5/5 passed**
- Blog test: **1 pre-existing failure** (test_blog_build.py, unrelated)

### Evidence Saved

- `.sisyphus/evidence/task-4-text-extraction.txt` — All 20 tests passing, no regressions

## Task 8: Extract io.py module

### TDD Workflow Success

**Phase 1: RED (Tests Fail)**
- Wrote `tests/test_io.py` with 16 tests covering:
  - `_write_html`: 9 tests (UTF-8 encoding, parent dir creation, nested dirs, overwrites, special chars, empty files, large content, newlines)
  - `_copy_tree`: 7 tests (simple copy, nested dirs, various file extensions, destination exists, nonexistent source, empty dirs, mixed content)
- Tests FAILED with `ModuleNotFoundError: No module named 'diablaq_site.io'`
- This is correct TDD red phase

**Phase 2: GREEN (Tests Pass)**
- Created `diablaq_site/io.py` with exactly 2 functions extracted from builder.py:
  - `_write_html(path: Path, html: str) -> None`: Creates parent dirs with `parents=True, exist_ok=True`, writes UTF-8 text
  - `_copy_tree(src: Path, dst: Path) -> None`: Wraps shutil.copytree with silent return if source missing
- All 16 tests passed immediately (exact implementation match)

**Phase 3: Refactor (Update builder.py)**
- Added import: `from diablaq_site.io import _write_html, _copy_tree` (line 15)
- Removed function definitions from builder.py (lines 237-241 and 292-296 after line renumbering during edits)
- Verified imports work: builder.py can still use both functions

### Test Coverage (16 tests, all passing)

**`_write_html` Tests (9):**
1. Writes file with UTF-8 encoding
2. Creates missing parent directory
3. Creates multiple nested parent directories
4. Overwrites existing file
5. Writes UTF-8 special characters (Polish chars)
6. Writes empty content
7. Writes large content (10KB+)
8. Preserves newlines in content
9. Overwrites with different length content

**`_copy_tree` Tests (7):**
1. Copies simple directory with files
2. Copies nested subdirectories preserving structure
3. Copies files with various extensions (.html, .css, .jpg, .json)
4. Handles destination exists (merge behavior)
5. Handles nonexistent source (returns silently)
6. Copies empty directory
7. Copies complex mixed content structure

### Regression Check

- Test suite: 143 passed (127 existing + 16 new)
- Only pre-existing failure: test_blog_is_built (unrelated to io.py extraction)
- No new failures introduced

### Files Created/Modified

- **Created**: `diablaq_site/io.py` (16 lines, 2 functions)
- **Created**: `tests/test_io.py` (210 lines, 16 tests)
- **Modified**: `diablaq_site/builder.py` (added 1-line import, removed 8 lines of function defs)

### Key Implementation Details

Both functions moved AS-IS with no refactoring:
- `_write_html`: Uses pathlib.Path, UTF-8 encoding, creates parents
- `_copy_tree`: Uses shutil.copytree with dirs_exist_ok=True, silent return if src missing
- No error handling added, no logging added, no behavioral changes

### Extraction Strategy Notes

- Functions are internal (_prefix) and only called from builder.py
- No other modules import these functions
- Clean boundary: all I/O logic consolidated in one module
- Future tasks can import from io.py instead of builder.py if needed

## Task 5: Extract validation.py (ISBN-13 + variant kinds)

### TDD Workflow Success

**Phase 1: RED (Tests Fail)**
- Wrote `tests/test_validation.py` with 21 tests covering:
  - Import checks for `_is_valid_isbn13` and `_ALLOWED_VARIANT_KINDS`
  - Valid ISBN-13 validation (3 real examples: 9780306406157, 9780140328721, 9780010350616)
  - Valid ISBN-13 with leading zeros: 9780000000002
  - Invalid checksums (wrong digits)
  - Length validation (too short, too long, empty string)
  - Non-digit characters (hyphens, spaces, letters)
  - Edge cases (all zeros, all nines, single digit pattern)
  - Type validation (None, integer inputs)
- Tests FAILED with `ModuleNotFoundError: No module named 'diablaq_site.validation'`
- This is correct TDD red phase

**Phase 2: GREEN (Tests Pass)**
- Created `diablaq_site/validation.py` (23 lines):
  - Function: `_is_valid_isbn13(isbn13: str) -> bool`
  - Constants: `_ALLOWED_BINDINGS`, `_ALLOWED_VERSIONS`, `_ALLOWED_VARIANT_KINDS`
- Extracted exact code from builder.py (lines 322-341):
  - ISBN-13 checksum: weights 1,3,1,3... alternating, modulo-10 validation
  - Variant kinds: union of bindings {miekka, twarda} and versions {elektroniczna}
- All 21 tests passed (100%)
- Maintained exact implementation without refactoring

**Phase 3: Refactor (Update builder.py)**
- Added import: `from diablaq_site.validation import _is_valid_isbn13, _ALLOWED_VARIANT_KINDS`
- Removed lines 322-341 from builder.py (function + constants)
- Verified no duplicate definitions remain

### Test Coverage

- 4 tests for variant kinds (set type, membership, cardinality)
- 3 tests for valid ISBNs (real examples with correct checksums)
- 2 tests for invalid checksums (wrong digit variants)
- 6 tests for format validation (length, non-digits, empty)
- 2 tests for edge cases (all zeros, all nines)
- 2 tests for type handling (None, integer)
- 2 tests for real-world patterns (single digit sequence, leading zeros)
- **Total: 21 tests, all passing**

### Files Created/Modified

- **Created**: `diablaq_site/validation.py` (23 lines, 1 function + 3 constants)
- **Created**: `tests/test_validation.py` (109 lines, 21 tests)
- **Modified**: `diablaq_site/builder.py` (added import, removed 20 lines of code)

### Regression Check

- Test results: **143 passed, 1 pre-existing failure**
- New tests: 21 validation tests (all passing)
- Existing tests: 122 tests (all still passing)
- Pre-existing failure: test_blog_is_built (unrelated)
- No regressions introduced

### Key Insights

1. **ISBN-13 Algorithm**: Alternating weights 1,3,1,3... summed then modulo 10
2. **Real ISBN examples**: Must manually verify checksum (9780306406157 ✓, 9780140328721 ✓)
3. **Constant naming**: Task mentioned `_VARIANT_KINDS`, but actual code uses `_ALLOWED_VARIANT_KINDS`
4. **No refactoring during extraction**: Moved code AS-IS, including comments and exact formatting
5. **TDD catches edge cases**: Tests revealed need to handle None and integer types properly

### Verification

```bash
PYTHONPATH=. uv run pytest tests/test_validation.py -v  # 21/21 ✓
PYTHONPATH=. uv run pytest tests/ -v                     # 143/144 ✓ (1 pre-existing fail)
python3 -c "from diablaq_site.builder import _is_valid_isbn13, _ALLOWED_VARIANT_KINDS"  # ✓
```

## Task 6: Extract images.py (3 image functions)

### TDD Workflow Success

**Phase 1: RED (Tests Fail)**
- Wrote `tests/test_images.py` with 26 comprehensive tests covering:
  - `get_cover_aspect_class`: 11 tests (None, empty, missing, tall<0.6, wide>0.75, standard 0.6-0.75, boundaries, leading slash, corrupted, PNG)
  - `generate_thumbnail`: 7 tests (creates thumbnail, preserves aspect ratio, missing file, parent dirs, RGBA→RGB, custom size, large image downsampling)
  - `thumb_path_from_photo`: 8 tests (simple filename, paths, extensions, nested dirs, absolute paths, return type)
- Tests FAILED with `ModuleNotFoundError: No module named 'diablaq_site.images'`
- This is correct TDD red phase

**Phase 2: GREEN (Tests Pass)**
- Created `diablaq_site/images.py` with all 3 functions moved AS-IS from builder.py:
  1. `get_cover_aspect_class(cover_path, root)` — aspect ratio classification
  2. `generate_thumbnail(src, dst, size)` — JPEG thumbnail generation with Pillow
  3. `thumb_path_from_photo(photo_path)` — thumbnail path derivation
- All 26 tests passed (26/26)
- Preserved exact implementation, thresholds (0.6, 0.75), JPEG quality (85), thumbnail size (300x300 default)

**Phase 3: Refactor (Update builder.py)**
- Added import block after line 14:
  ```python
  from diablaq_site.images import (
      get_cover_aspect_class,
      generate_thumbnail,
      thumb_path_from_photo,
  )
  ```
- Removed original function definitions (lines ~243-289 in original)
- Removed unused `from PIL import Image` import from builder.py
- Updated 5 call sites in builder.py to use public names (removed underscore prefixes)
- Note: PIL import moved to images.py where it's actually used

### Test Coverage Highlights

1. **get_cover_aspect_class Boundaries**
   - Correctly handles ratio < 0.6 (tall)
   - Correctly handles ratio > 0.75 (wide)
   - Correctly handles 0.6 ≤ ratio ≤ 0.75 (standard)
   - Returns "cover--standard" for missing files (graceful degradation, NOT error)
   - Returns "cover--standard" for corrupted images (graceful degradation)
   - Handles leading slash stripping in paths

2. **generate_thumbnail Safety**
   - Handles missing source file (no-op, no error)
   - Creates parent directories automatically
   - Converts RGBA/P to RGB for JPEG compatibility
   - Preserves aspect ratio (thumbnail mode)
   - Respects custom size parameter

3. **thumb_path_from_photo String Handling**
   - Handles simple filenames, nested paths, absolute paths
   - Correctly uses `Path.stem` for extension handling
   - Returns string (not Path object)

### Files Created/Modified
- **Created**: `diablaq_site/images.py` (55 lines, 3 functions)
- **Created**: `tests/test_images.py` (267 lines, 26 tests)
- **Modified**: `diablaq_site/builder.py` (removed 47 lines, added 5-line import block, removed PIL import)

### Evidence Saved
- 26/26 tests passing for test_images.py
- Full test suite: 143 passed (143 = 26 new + 117 existing), 1 pre-existing failure (test_blog_is_built)
- Zero regressions from extraction

### Critical Implementation Notes
- **Aspect ratio thresholds are NOT inclusive**: ratio > 0.75 for wide, ratio < 0.6 for tall (0.6-0.75 range is standard)
- **Graceful degradation**: Missing/corrupted images return "cover--standard", NOT empty string or error
- **Thumbnail size is default 300x300** but can be customized (used as max dimension with aspect ratio preservation)
- **JPEG quality hardcoded at 85** for thumbnails (acceptable quality/size tradeoff)
- **Color mode conversion**: RGBA and P (palette) mode images converted to RGB before saving as JPEG

### Wave 2 Status
- This is part of parallel Wave 2 (Tasks 3-8)
- Task 3 (models.py) is prerequisite but extraction can proceed independently
- Confirmed Task 8 (io.py) has been extracted in parallel (io imports visible in builder.py)

## Task 7: Extract urls.py (canonical URLs + tag slugification)

### Extraction Summary

**Extracted 3 URL generation functions from builder.py:**
- `_slugify_tag(tag: str) -> str` — URL-safe tag encoding (UTF-8 percent-encoding via `quote`)
- `_canonical_project_url(line: str, slug: str) -> str` — Project listing URLs by publication line
- `_canonical_edition_url(line: str, project_slug: str, edition_slug: str) -> str` — Edition/issue URLs with special `index` handling

**Key Implementation Detail**: The `_canonical_edition_url` function uses `edition_slug == "index"` check directly (no `is_index` parameter). When edition_slug is "index", it delegates to `canonical_project_url` — this is NOT a conditional parameter, but a content-based check.

### TDD Workflow (Verified)

1. **RED**: Wrote `tests/test_urls.py` with 25 comprehensive tests
   - 7 tests for `canonical_project_url` (diablaq, dobre-licho, mecenat, studio, unknown line, special chars, empty slug)
   - 8 tests for `canonical_edition_url` (index handling, each line type, special chars)
   - 10 tests for `slugify_tag` (spaces, leading/trailing spaces, special chars, unicode, empty, punctuation, case preservation, ampersand)
   - All tests FAILED with ModuleNotFoundError (expected)

2. **GREEN**: Created `diablaq_site/urls.py` with exact extracted implementations
   - All 25 tests immediately passed without modification
   - Functions work as-is, no refactoring needed

3. **REFACTOR**: Updated builder.py imports and call sites
   - Added `from diablaq_site.urls import canonical_project_url, canonical_edition_url, slugify_tag`
   - Updated 4 call sites: 2 for edition_url, 2 for tag slugify
   - Removed underscore prefixes from function calls (imported as public names)
   - Cleaned up function definitions from builder.py (3 functions removed)

### Files Created/Modified

- **Created**: `diablaq_site/urls.py` (76 lines, 3 functions)
- **Created**: `tests/test_urls.py` (222 lines, 25 tests)
- **Modified**: `diablaq_site/builder.py`
  - Added: 5 lines of import block
  - Removed: 3 function definitions (~25 lines total)
  - Updated: 4 function call sites (underscore removal)

### Regression Verification

- **URLs tests**: 25/25 PASS
- **Full test suite**: 143 PASS, 1 FAIL (pre-existing: test_blog_is_built)
- **No new failures introduced** by extraction
- **Bundle tests**: test_blog_build.py + test_edition_variants.py all pass with new module

### Interaction with Previous Extractions

Task 7 depends on Tasks 3-6 being complete:
- Task 6 (images.py) created without importing in builder.py
- Task 4-6 removed functions but didn't add all imports
- Had to manually add `from diablaq_site.images import get_cover_aspect_class, generate_thumbnail, thumb_path_from_photo` after URLs extraction
- This indicates Task 4-6 extractions may need import verification

### Code Quality Notes

1. **quote() behavior**: The `slugify_tag` function uses `quote(tag.strip(), safe="")` which:
   - Strips whitespace before encoding
   - Percent-encodes all special characters except unreserved characters
   - Handles Unicode by UTF-8 encoding then percent-encoding
   - Converts spaces to `%20` (as per comment in original code)

2. **Index edition special case**: The `edition_slug == "index"` check is deliberate — not a parameter-based design but a content-based URL optimization.

3. **Line parameter**: Both URL functions take `line` as keyword-only parameter (used internally for conditional routing).

### Test Insights

- The 25 tests cover both happy paths and edge cases
- Unicode handling in `slugify_tag` works seamlessly (test passes for Łódź → percent-encoded)
- All publication line types (diablaq, dobre-licho, mecenat, studio) have dedicated tests
- Index edition special case verified with multiple line types
- Empty/whitespace edge cases properly handled

