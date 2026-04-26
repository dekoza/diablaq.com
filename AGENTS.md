# AGENTS.md — diablaq.com

This file is the authoritative guide for AI agents working on this repository.
Read it fully before making any changes.

---

## What this repository is

A **custom static site generator** for [diablaq.com](https://diablaq.com) — a Polish comics
publisher. The generator is a small Python package (`diablaq_site`) that reads Markdown content
files with YAML frontmatter, renders them through Jinja2 templates, and writes the resulting HTML
to `dist/`. The site is published via GitHub Pages from the `gh-pages` branch.

There is no framework. No Django. No Flask. No Node.js. Just Python, Jinja2, Markdown, and Pillow.

---

## Repository layout

```
diablaq.com/
├── content/                  Source content (Markdown + YAML frontmatter)
│   ├── blog/                 Blog posts    → /blog/<slug>/
│   ├── pages/                Static pages  → /<slug>/
│   ├── people/               Author profiles → /ludzie/<slug>/
│   └── projects/             Comics projects
│       └── <project>/
│           ├── project.md    Project metadata + description
│           └── editions/
│               └── <edition>.md   Edition metadata + body
│
├── css/                      Source stylesheets (copied to dist/css/)
│   ├── diablaq.css           All site styles. No Pico, no framework — owns everything.
│   └── fonts.css             CSS custom properties for typography (no @import)
│
├── img/                      Source images (copied to dist/img/)
│   └── people/               Author photos (thumbnails generated at build time)
│
├── templates/                Jinja2 templates
│   ├── base.html             Shell: nav, OG meta, footer, font <link>s
│   ├── home.html             Homepage: hero + sections + full catalog
│   ├── catalog.html          /komiksy/ — all projects grouped by line
│   ├── project.html          Multi-edition project page with breadcrumb
│   ├── edition.html          Single edition page with breadcrumb
│   ├── blog_index.html       Blog listing
│   ├── blog_post.html        Single post
│   ├── people_index.html     Authors grid
│   ├── person.html           Author detail with related editions
│   ├── page.html             Generic static page
│   ├── listing.html          Generic edition listing (used for tag pages)
│   ├── section.html          Legacy template — not rendered by the builder
│   ├── 404.html              Branded 404 page (generated to dist/404.html)
│   ├── redirect.html         Meta-refresh redirect (zvyrke only)
│   └── _partials/
│       ├── edition_tile.html        Compact cover card (grid listings)
│       ├── edition_tile_for_person.html  Same but shows person's role
│       ├── edition_details.html     Full edition detail panel (cover + specs + buy)
│       ├── project_card.html        Project cover card
│       └── blog_card.html           Blog post card
│
├── diablaq_site/             The generator package
│   ├── models.py             Frozen dataclasses (Project, Edition, Person, …)
│   ├── parsing.py            Load content from Markdown, validate, build objects
│   ├── builder.py            Orchestration: load → process → render → finalise
│   ├── rendering.py          Render each page type using Jinja2
│   ├── urls.py               Canonical URL generation + tag slugification
│   ├── images.py             Pillow: cover aspect class + thumbnail generation
│   ├── text.py               Polish orphan-word non-breaking-space insertion
│   ├── validation.py         ISBN-13 checksum; allowed variant kinds
│   ├── io.py                 _write_html, _copy_tree
│   └── cli.py                Entry point: `diablaq-build`
│
├── tests/                    pytest test suite (231 tests)
├── scripts/
│   └── nav_walkthrough.py    Playwright navigation smoke test + video recorder
│
├── dist/                     Build output — do NOT commit
├── robots.txt                Copied to dist/ on build
├── CNAME                     Copied to dist/ on build
├── .nojekyll                 Copied to dist/ on build
├── pyproject.toml
├── uv.lock                   Lock file — use `uv` for dependency management
├── Makefile                  make install / make build / make serve / make push
└── .github/workflows/pages.yml  Deploy dist/ to GitHub Pages on push to gh-pages
```

---

## Build pipeline

```
content/  +  templates/  +  css/  +  img/
       ↓
  diablaq-build
       ↓
  parsing.py      reads every .md, builds frozen dataclass objects
       ↓
  builder.py      orchestrates: load → process → render → finalise
       ↓
  rendering.py    calls Jinja2 for each page type, writes to dist/
       ↓
  dist/           static HTML + copied CSS, images, robots.txt, _redirects
```

### Key entry points

| Command | Effect |
|---------|--------|
| `uv run diablaq-build` | Build to `dist/` (default, uses `uv`) |
| `uv run diablaq-build --out /tmp/test-dist` | Build to custom dir |
| `make build` | Same, via Makefile (uses `.venv` pip install) |
| `make serve` | Build + `python -m http.server 8000 --directory dist` |
| `uv run pytest` | Run all 231 tests |

The `DIABLAQ_SITE_URL` environment variable sets the base URL for canonical links and OG tags
(set to `https://diablaq.com` in CI; empty locally produces relative-looking absolute URLs).

---

## URL structure

All project and edition pages live under `/komiksy/`:

```
/                               Homepage
/komiksy/                       Unified catalog (all projects grouped by line)
/komiksy/<project>/             Project page  (or edition page for one-shots)
/komiksy/<project>/<edition>/   Edition page
/blog/                          Blog index
/blog/<slug>/                   Blog post
/blog/tag/<tag>/                Tag listing
/ludzie/                        People index
/ludzie/<slug>/                 Author profile
/<page-slug>/                   Static page (kontakt, etc.)
/404.html                       Branded 404
```

**Publication line is NOT part of the URL.** `line` is a display grouping in the catalog only.
All lines (diablaq, dobre-licho, mecenat, studio) produce `/komiksy/…` URLs.

**One-shot convention:** if a project has a single edition named `index.md`, that edition
collapses to the project URL. The page rendered there is `edition.html`, not `project.html`.
The breadcrumb shows `Komiksy › Project Title` (no separate project page exists).

### Legacy redirects

Legacy URLs are handled by `dist/_redirects` (Netlify/Cloudflare Pages format), generated
automatically at build time from `legacy_path` fields in `project.md` files.
**Do not create HTML shim pages for redirects.** Add a `legacy_path` to the project's YAML
frontmatter — the builder handles the rest.

---

## Content schema

### `content/projects/<slug>/project.md`

```yaml
---
title: "Project Title"           # required; quote if contains commas or colons
line: diablaq                    # required; one of: diablaq | dobre-licho | mecenat | studio
summary: "One sentence."         # required (shown on cards); must NOT duplicate first body line
cover_image: /img/<file>.jpg     # required (non-draft); file must exist in img/
draft: true                      # optional; omit or false to publish; true to hide completely
legacy_path: /old-slug/          # optional; generates a redirect in _redirects
legacy_landing: true             # optional; was used for legacy full-page copy — now only
                                 # affects _redirects generation (legacy_landing=true projects
                                 # DO NOT produce an extra HTML page)
featured: false                  # not used on project level
---

Body text in Markdown. Optional. Keep it distinct from `summary`.
```

**Build-time warnings are emitted** (to stderr) when:
- `cover_image` is missing or points to a non-existent file
- `summary` is missing

### `content/projects/<slug>/editions/<edition-slug>.md`

`<edition-slug>` is the URL slug. Use `index` only for true one-shots (single-volume works
that have no separate project listing page). Use numeric slugs (`01`, `02`) for serial issues,
or descriptive slugs (`cudowni`, `drzazga`) for standalone volumes in a series.

```yaml
---
title: "Edition Title"             # required
release_date: YYYY-MM-DD           # required for published work; omit for truly TBA
release: "First Edition 2024"      # optional; shown as subtitle — omit if it duplicates release_date

# Cover
cover_image: /img/<file>.jpg       # preferred; use if single cover
cover_alt: "Alt text"
covers:                            # use instead of cover_image for multiple covers
  - image: /img/<file>.jpg
    alt: "Alt text"
    caption: "Optional caption"

# Creators
creators:
  - role: "Scenariusz"             # omit role if not applicable
    name: "Full Name"
    person_slug: slug-in-ludzie    # omit if person has no /ludzie/ page

# Simple editions (no variants)
specs:
  "Liczba stron": "128"
  "Oprawa": "miękka"
  "Wymiary": "165 x 235 mm"
  "Cena": "49,90 zł"
  "ISBN-13": "978XXXXXXXXXX"       # also accepted at top level; prefer inside specs
buy_links:
  - label: "Kup w naszym sklepie"
    url: "https://strefakomiksu.pl/..."

# Variant editions (multiple bindings / digital)
variants:
  - binding: miekka               # or: twarda
    isbn13: "978XXXXXXXXXX"        # validated with ISBN-13 checksum
    limited_print_run: 333         # optional
    numbered: true                 # requires limited_print_run
    specs:
      "Cena": "66,60 zł"
    buy_links:
      - label: "Strefa Komiksu"
        url: "https://..."
  - version: elektroniczna
    isbn13: "978XXXXXXXXXX"
    specs:
      "Cena": "29,90 zł"
    buy_links: []

# Status flags (auto-derived from release_date unless overridden)
# is_new: auto (release_date <= today <= release_date + 6 weeks)
# is_announcement: auto (release_date > today)
force_new: true                    # override: force is_new regardless of date
force_announcement: true           # override: force is_announcement
# Cannot set both at once.

# Presale
presale_url: "https://..."         # shown as CTA if is_announcement is true

# Editorial
featured: true                     # makes this edition the homepage hero
standalone: true                   # suppresses issue numbering; use for non-serial volumes

# Legacy
legacy_anchor: kodiak1             # old in-page anchor; preserved for _redirects compatibility
subseries: "eXXXtra"               # groups editions within a project for issue numbering
issue_number: 5                    # explicit issue number override
---

Body text. Rendered below the edition metadata panel.
```

**Build-time warning** if a published (non-announcement, non-TBA) edition has no buy links.

### `content/people/<slug>.md`

```yaml
---
name: "Full Name"                # optional when the person publishes only under a credit name
credit_name: "Werka Dobro"       # optional; used on comic pages / credits; falls back to `name`
photo: /img/people/<slug>.jpg      # optional; thumbnail auto-generated at build time
---

Bio in Markdown. Shown on the person's page.
```

At least one of `name` or `credit_name` must be present.

Person ↔ edition linkage works in both directions:
- Explicit: `person_slug: <slug>` in edition creators
- Implicit: creator name matches `person.name` or `person.credit_name` (case-insensitive)

### `content/blog/<YYYY-MM-DD>-<slug>.md`

```yaml
---
title: "Post title"
date: YYYY-MM-DD                   # required
summary: "One sentence."           # shown on listing cards
cover_image: /img/...              # optional
cover_alt: "..."
tags:
  - wydarzenia
draft: true                        # skip this post entirely
---

Body in Markdown.
```

### `content/pages/<slug>.md`

```yaml
---
title: "Page Title"
---

Body in Markdown. Rendered at /<slug>/.
```

---

## CSS conventions

**There is no CSS framework.** `diablaq.css` owns every rule. Key conventions:

- Custom properties are declared in `:root` in `diablaq.css`. Do not scatter them across rules.
- **Zero `!important` policy.** If you need to override a rule, fix the specificity instead.
- Font families are declared as CSS custom properties in `fonts.css` (`--diablaq-font-display`,
  `--diablaq-font-heading`, `--diablaq-font-body`). Reference them by variable everywhere.
- Google Fonts are loaded via two `<link>` tags in `base.html` (preconnect + stylesheet) —
  **not** via `@import` in CSS, which would create a render-blocking chain.
- Cover image aspect ratio is always `180 / 255` (comics portrait). Exceptions use the CSS
  classes `cover--tall`, `cover--wide`, `cover--standard` set by the builder via Pillow.
- Use `.btn.btn-primary` for the main buy CTA, `.btn.btn-secondary` for alternative links.
- The mobile nav overlay is a CSS-only checkbox hack (`#nav-toggle`). No JavaScript.

---

## Template conventions

- All templates extend `base.html`.
- `base.html` provides `{% block title %}`, `{% block og_title %}`, `{% block og_description %}`,
  `{% block og_image %}`, `{% block hero %}`, `{% block content %}`.
- Every template that shows a cover image should override `og_image`.
- Breadcrumbs are passed as a list of `{label, url}` dicts from `rendering.py` and rendered
  via the `.breadcrumb` pattern in `project.html` and `edition.html`.
- Partials in `_partials/` use the variable conventions:
  - Edition tiles: `e` (the `Edition` object)
  - Project cards: `p` (the `Project` object)
  - Blog cards: `post` (the `BlogPost` object)
  - `edition_details.html`: `edition` + `project`
  - `edition_tile_for_person.html`: `e` + `person` (for role matching)
- The `abs_url` callable is always available in context. Use it for OG image URLs:
  `{{ abs_url(edition.cover_image) }}`.
- The `format_date_pl` Jinja filter formats dates as Polish genitive: `{{ date | format_date_pl }}`
  → `"15 listopada 2024"`. Year 9999 → `"Wkrótce"`. `None` → `""`.

---

## Python package conventions

- All models are **frozen dataclasses** in `models.py`. Do not add mutable state.
- `parsing.py` functions are pure: they receive raw data and return dataclass objects.
  They emit `print(..., file=sys.stderr)` warnings but never silently swallow data problems —
  missing required fields raise `ValueError`.
- `builder.py` orchestrates: `_init_environment` → `_load_content` → `_process_content` →
  `_render_all` → `_finalize`. Each stage is a separate function.
- `rendering.py` contains one `render_*` function per page type. Each function receives the
  Jinja `env`, output dir, site URL, nav projects, content objects, and two callbacks
  (`_render_fn`, `_write_html_fn`) for testability.
- `urls.py` is the single source of truth for URL generation. **All** URL construction goes
  through `canonical_project_url` / `canonical_edition_url`. Never hardcode URL paths in
  templates or Python code.

---

## Adding content

### New project + editions

1. Create `content/projects/<slug>/project.md` with required fields (title, line, summary,
   cover_image). Put the cover image in `img/`.
2. Create `content/projects/<slug>/editions/` and add at least one `<slug>.md`.
3. For a one-shot (single volume with no series page), name the edition `index.md`.
   Its URL will be `/komiksy/<project>/` — no separate project index page is generated.
4. For a series, use numbered slugs (`01`, `02`, …) or descriptive slugs. Each gets its own
   URL `/komiksy/<project>/<edition>/`.
5. Add `buy_links` to every published edition. A build warning fires if they are missing.
6. Run `uv run diablaq-build` and inspect `dist/`.

### New person

1. Add `content/people/<slug>.md` with `name` and/or `credit_name`, plus optional `photo`.
2. Put the photo in `img/people/<slug>.jpg` (or `.png`). A thumbnail is generated at build time.
3. Link from editions via `person_slug: <slug>` in creator entries.

### New blog post

1. Create `content/blog/YYYY-MM-DD-<slug>.md`. The filename date becomes the post date
   if `date` frontmatter is not set (but setting it explicitly is preferred).

### Draft / work in progress

Set `draft: true` in the project or blog post frontmatter. The builder skips it entirely.
**Never use YAML comment hacks to disable content** (`# title: ...` or `[//]: # (...)`).

---

## Homepage hero

The hero image on the homepage is editorially controlled via `featured: true` in an edition's
frontmatter. The builder picks the first edition with `featured: true` and `cover_image` as the
hero. If none is flagged, it falls back to the first announcement with a cover image.

---

## Deployment

The site auto-deploys via GitHub Actions (`.github/workflows/pages.yml`) on every push to the
`gh-pages` branch. The workflow runs `diablaq-build --out dist` with
`DIABLAQ_SITE_URL=https://diablaq.com` and publishes `dist/` to GitHub Pages.

`dist/` is in `.gitignore` and must NOT be committed manually.

The generated `dist/_redirects` file is for Netlify/Cloudflare Pages. It is present in the
build output but is ignored by GitHub Pages (which does not support server-side redirects).
Legacy URL handling on GitHub Pages relies on the single-file `dist/zvyrke/index.html` meta-
refresh for the one non-content redirect (`/zvyrke/ → /ludzie/zvyrke/`). All other legacy paths
will 404 on GitHub Pages until the site is migrated to Netlify or Cloudflare Pages.

---

## Tests

```bash
uv run pytest             # run all 231 tests
uv run pytest tests/test_parsing.py   # one module
uv run pytest -k isbn     # by name pattern
```

Test modules:

| File | What it covers |
|------|---------------|
| `test_models.py` | Dataclass instantiation |
| `test_parsing.py` | All 20+ parsing functions (64 tests) |
| `test_urls.py` | URL generation for all lines |
| `test_builder.py` | `_process_content` — newest_anytime logic |
| `test_rendering.py` | `render_template`, `abs_url`, `format_date_pl` |
| `test_edition_variants.py` | Full build smoke test + ISBN validation |
| `test_blog_build.py` | Full build smoke test — blog output exists |
| `test_validation.py` | ISBN-13 checksum |
| `test_images.py` | Aspect class detection |
| `test_io.py` | `_write_html`, `_copy_tree` |
| `test_text.py` | Orphan-word non-breaking-space |
| `test_cli.py` | CLI argument parsing |
| `test_makefile.py` | Makefile help output |

**TDD is mandatory.** Write the failing test first, then implement. The full build smoke tests
(`test_blog_build.py`, `test_edition_variants.py`) use `tmp_path` with symlinked `templates/`,
`css/`, `img/` so they always reflect the live templates.

---

## Known limitations and gotchas

1. **GitHub Pages has no server-side redirects.** The `_redirects` file only works on
   Netlify/Cloudflare Pages. Legacy paths currently 404 on the live site except where HTML
   redirect shims were emitted (only `/zvyrke/`).

2. **`section.html` still exists but is not rendered.** The builder no longer calls
   `_write_section()`. The template is kept as dead code for now. Do not use it.

3. **`edition_card.html` partial is not used by any page template.** It was part of an older
   design. Can be deleted safely.

4. **`legacy_landing: true` no longer produces a duplicate HTML page.** It only affects
   `_redirects` generation. If you previously relied on the legacy page being present in `dist/`,
   that behaviour is gone.

5. **`obietnica` project has `draft: true`.** Its editions directory is still present but
   the project is completely hidden from the build. The editions will silently not render.

6. **Newsletter CTA in `base.html` is conditional.** It renders only when the `newsletter_url`
   template variable is defined and truthy. Currently no page passes it, so the newsletter
   section is never shown. To enable it, pass `newsletter_url="https://..."` from `builder.py`.

7. **`release` field vs `release_date`:** `release_date` is a `YYYY-MM-DD` date used for
   sorting and `is_new`/`is_announcement` logic. `release` is an optional human-readable string
   (e.g. `"Wydanie pierwsze"`) shown as a subtitle. If `release` looks like an ISO date
   (`YYYY-MM-DD` pattern), the template suppresses it to avoid duplicating the formatted date.

---

## What NOT to do

- **Do not add `!important` to CSS.** Fix specificity instead.
- **Do not create HTML shim pages for redirects.** Add `legacy_path` to frontmatter.
- **Do not inline URL paths in templates.** Use the `canonical_*` functions in `urls.py`.
- **Do not import from `diablaq_site.parsing` in templates.** All data is pre-computed before
  rendering — templates receive only the objects they need.
- **Do not commit `dist/`.** It is in `.gitignore` for good reason.
- **Do not use `@import` in CSS** for font loading. Use `<link>` tags in `base.html`.
- **Do not place raw `release_date` ISO strings in the `release` field.** That field is for
  human-readable text like edition names. Leave it empty if you have nothing to say.
- **Do not use YAML comment tricks (`#key: value`) to disable fields.** Use `draft: true`.
