# Deployment na GitHub Pages (diablaq.com)

## Założenia
- Repozytorium zawiera **źródła** (treści w `content/`, szablony w `templates/`, assety w `img/` i `css/`).
- Katalog `dist/` jest wynikiem builda i **nie jest** commitowany.
- Foldery `_migracja/` i `_penpot/` zostają w repo jako materiały robocze, ale **nie trafiają do publikacji**, bo publikujemy wyłącznie `dist/`.

## 1) Konfiguracja GitHub Pages
1. Wejdź w: `Settings → Pages`.
2. W sekcji **Build and deployment** ustaw:
   - **Source**: `GitHub Actions`.

To wszystko. Deployem zajmie się workflow.

## 2) Workflow GitHub Actions
W repo jest plik: `.github/workflows/pages.yml`.

Działa tak:
- na push do gałęzi `gh-pages` buduje stronę do `dist/`
- uploaduje `dist/` jako artifact
- publikuje artifact na GitHub Pages

### Uwaga o kanonicznych URL-ach
Workflow ustawia zmienną środowiskową:
- `DIABLAQ_SITE_URL=https://<owner>.github.io/<repo>`

Dzięki temu `rel="canonical"` w HTML jest absolutny.

Jeżeli docelowo użyjesz domeny niestandardowej (np. `diablaq.com`), podmień w workflow:
- `DIABLAQ_SITE_URL: https://diablaq.com`

## 3) Jak sprawdzić lokalnie

```bash
python -m pip install -U pip
pip install .
diablaq-build --out dist
```

Potem podejrzyj statycznie `dist/` (np. dowolnym serwerem plików).

## 4) Co jest publikowane
Publikujemy TYLKO zawartość `dist/`.

Z tego powodu:
- `_migracja/` i `_penpot/` nie są publikowane
- nie musimy ich usuwać z repo

## 5) Dodawanie wpisu na blogu
1. Dodaj plik w `content/blog/`, np. `2026-02-01-targi-w-lodzi.md`.
2. W YAML podaj minimum:

```yaml
---
title: "Targi w Łodzi"
date: 2026-02-01
---
```

3. Dodaj treść w Markdown (możesz używać obrazków z `img/` przez `/img/...`).
4. Push do `gh-pages` → workflow zrobi deploy.

