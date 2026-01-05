# diablaq.com

Repozytorium strony wydawnictwa Diablaq.

## Edycja treści (dla nietechnicznych)
Zobacz: `_migracja/INSTRUKCJA_DLA_REDAGUJACYCH.md`.

## Blog
Wpisy są w `content/blog/` (Markdown + frontmatter YAML).
- Listing: `/blog/`
- Wpis: `/blog/<slug>/`

## Generator strony
Strona jest generowana statycznie z treści w Markdown (folder `content/`) i szablonów Jinja (folder `templates/`).

### Szybki start (lokalnie)
```bash
python -m pip install -U pip
pip install .
diablaq-build --out dist
```

## Deployment (GitHub Pages)
Publikujemy wyłącznie katalog `dist/` (generator). Foldery `_migracja/` i `_penpot/` zostają w repo, ale nie są częścią publikowanej strony.

Instrukcja: `_migracja/DEPLOY_GITHUB_PAGES.md`.
