# Prompt do wznowienia migracji (kopiuj-wklej)

> Cel: pozwala w dowolnym momencie wznowić przerwaną pracę bez zgadywania.

## Kontekst
Repozytorium `diablaq.com` jest statyczną stroną wydawnictwa (GitHub Pages). Chcemy je zmigrować do generatora statycznego w Pythonie, gdzie treść będzie w Markdown z frontmatter YAML, a HTML będzie renderowany przez Jinja2. Mockupy docelowego layoutu są w folderze `_penpot/` jako eksporty SVG (DESKTOP/MOBILE) oraz archiwum `_penpot/Diablaq/` z assetami.

## Założenia i decyzje
- Zachowujemy **wariant A** URL: istniejące top-level ścieżki (`/spz/`, `/bzik/`, `/mama/`, ...) działają nadal.
- Wprowadzamy nowe działy:
  - `/mecenat/` i `/mecenat/<projekt>/` (np. `/mecenat/bzik/`)
  - `/studio/` i `/studio/<projekt>/`
  - `/ludzie/` i `/ludzie/<slug>/`
  - `/diablaq/` i `/dobre-licho/` jako listingi
- `/bzik/` ma być **landing page** (legacy), który linkuje do numerów (docelowo do `/mecenat/bzik/<id>/`).
- Zachowujemy legacy anchory (hash): np. `/spz/#spz2`, `/bzik/#bzik5`.
- CSS: Pico.css + cienka warstwa brandująca (można startowo wykorzystać `css/diablaq.css` jako override zmiennych).
- Redirecty (Cloudflare) są niskim priorytetem, na końcu.

## Zadanie dla Ciebie (asystenta) po wznowieniu
1. Przeczytaj dokument planu: `_migracja/PLAN_MIGRACJI.md`.
2. Przejrzyj `_penpot/` (SVG) i zidentyfikuj komponenty/layout.
3. Zaproponuj (i potem wdroż) minimalny generator:
   - loader Markdown + frontmatter YAML
   - renderer Jinja2
   - budowanie `dist/` (kopiowanie assetów)
4. Zaimplementuj szablony zgodne z mockupami (desktop/mobile): base/nav/menu, home, project/edition, people.
5. Zmigruj treść iteracyjnie w kolejności: `spz` → `hadfield` → `bzik` → reszta → `ludzie`.
6. Dopiero na końcu rozważ canonical/redirect rules w Cloudflare.

## Miejsce na doprecyzowania (dla właściciela repo)
- Co dokładnie ma reprezentować `/zvyrke/` po migracji?
  - [x] alias profilu `/ludzie/zvyrke/`
  - [ ] strona tytułu „Obietnica” (a autor osobno)
  - [ ] inne: __________

  Doprecyzowanie:
  - Obecna treść w `/zvyrke/` to komiks pt. **„Obietnica”** i powinien mieć **własną podstronę** (osobny wpis w katalogu tytułów/wydań), niezależnie od tego, że `/zvyrke/` jest aliasem profilu.

- Czy wydania (np. BZIK #5) mają mieć zawsze osobne URL-e (np. `/mecenat/bzik/5/`), czy wystarczy landing z sekcjami?
  - [x] osobne URL-e
  - [ ] tylko landing + anchory
  - [ ] hybryda (osobne dla części): __________

- Studio: jak grupować projekty?
  - [ ] po wydawcach/klientach
  - [ ] po seriach
  - [x] chronologicznie
  - [ ] inne: __________

## Ograniczenia implementacyjne / zasady kodowania
- Inline HTML w Pythonie: tylko krótkie jednolinijkowe; wielolinijkowe fragmenty HTML idą do szablonów.
- Importy Pythona na górze plików.

---

Jeśli chcesz, zacznij od wygenerowania minimalnego szkicu generatora i jednego widoku (home) z danymi przykładowymi, a potem iteruj.
