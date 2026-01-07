# Plan migracji diablaq.com → generator statyczny (Python + Jinja) + treści w Markdown

> Data: 2026-01-05  
> Repo: GitHub Pages (statycznie)  
> Cel: Ułatwić edycję treści (bez dłubania w HTML) i wdrożyć nowe szablony z Penpot.  

## 0. Szybkie podsumowanie decyzji ("source of truth")

### 0.1. Technologie
- **Generator statyczny w Pythonie**: renderowanie HTML z **Jinja2**, treść w **Markdown + frontmatter YAML**.
- Wynik: statyczny katalog (np. `dist/`) publikowany na GitHub Pages.
- CSS: **Pico.css** jako ultra-prosty framework + lekka warstwa brandująca (`css/diablaq.css` lub nowy plik z override’ami).

### 0.2. Mockupy / wzorzec UI
- Źródło: `_penpot/*.svg` (widoki DESKTOP/MOBILE) + archiwum `_penpot/Diablaq/` (assets + manifest).
- Implementujemy layout jako szablony Jinja, nie kopiujemy wielolinijkowego HTML do Pythona.

### 0.3. URL-e (wariant A + nowe działy) — AKTUALIZACJA
Priorytet: **nie psuć istniejących linków**, redirecty mają niski priorytet.

#### 0.3.1. Legacy URL-e (zostają jako alias/redirect)
- `/spz/`, `/belzebubs/`, `/ciecio/`, `/karmiciel/`, `/kodiak/`, `/midguard/`, `/winon/`
- `/pisto/`
- `/mama/`, `/pzg/`, `/hadfield/`
- `/zvyrke/` (alias profilu autora)
- `/bzik/` (legacy landing dla BZIK z anchorami)
- `/kontakt/`

Zasada: legacy adresy są utrzymywane jako **aliasy** (strona stub/redirect) albo, tam gdzie to konieczne przez anchory (np. `/bzik/#bzik5`), jako **pełna strona landing**.

#### 0.3.2. Nowe działy (kanoniczne)
- **Publikacje (główna linia Diablaq)**: `/publikacje/<projekt>/` oraz `/publikacje/<projekt>/<wydanie>/`.
  - Przykład: **SPZ #1** → `/publikacje/spz/01/`
  - `/spz/` → przekierowanie/alias do `/publikacje/spz/`
- **Dobre Licho**: `/dobre-licho/<projekt>/` oraz `/dobre-licho/<projekt>/<wydanie>/`.
  - Przykład: **Pisto #1** → `/dobre-licho/pisto/01/`
  - `/pisto/` → przekierowanie/alias do `/dobre-licho/pisto/`
- **Mecenat**: `/mecenat/<projekt>/` oraz `/mecenat/<projekt>/<wydanie>/`.
  - Przykład: **BZIK #7** → `/mecenat/bzik/07/`
  - Specjalnie: `/bzik/` pozostaje landingiem (legacy) z anchorami i linkuje do wydań kanonicznych.
- **Studio (produkcje dla innych)**: `/studio/<projekt>/` oraz `/studio/<projekt>/<wydanie>/`.
  - Przykład: `/studio/paatrzcie/` → publikacja (komiks wydany dla PAA)

**Nowe strony listujące (kanoniczne dla listingów):**
- **Nowości**: `/nowe/` — sortowanie: **od najnowszych** (`release_date` malejąco).
- **Zapowiedzi**: `/zapowiedzi/` — sortowanie: **od najnowszych** (`release_date` malejąco).

Zasady:
- `is_new` i `is_announcement` są **wzajemnie wykluczające**.
- Listing jest agregacją; każda pozycja ma swoją **kanoniczną stronę** w odpowiedniej sekcji.

### 0.4. Priorytet przekierowań
- Redirecty (301/308) są **na końcu**; domena jest w Cloudflare, więc docelowo można użyć reguł Cloudflare.
- Na GitHub Pages można też użyć stron stub (meta/js).

---

## 1. Inwentaryzacja obecnego repo (stan wejściowy)

### 1.1. Typy podstron (ustalone przez właściciela treści)
- **Pojedyncze komiksy** (single): `hadfield`, `mama`, `pzg`
- **Autorzy**: `zvyrke`
- **Mecenat**: `bzik`
- **Serie głównej linii (Diablaq)**: `belzebubs`, `ciecio`, `karmiciel`, `kodiak`, `midguard`, `spz`, `winon`
- **Serie Dobre Licho**: `pisto` (+ `hadfield` jako single)

### 1.2. Ważne legacy anchory
- `spz/index.html`: sekcje `id="spz1"`, `id="spz2"` (homepage linkuje m.in. do `/spz/#spz2`).
- `bzik/index.html`: `id="bzik1".."bzik7"`, `bzik_x1`, `bzik_x2`, `bzik_x3` (homepage linkuje do `/bzik/#...`).

Wniosek: nowy system powinien potrafić zachować anchor `id` na stronach legacy.

---

## 2. Docelowa architektura informacji (IA)

### 2.1. Koncepcje domenowe
- **Linia / dział**: Diablaq, Dobre Licho, Mecenat, Studio.
- **Projekt / seria**: SPZ, BZIK, Pisto, itp.
- **Wydanie / numer / pozycja**: konkretne tomy/zeszyty/numer z okładką, specyfikacją, twórcami.
- **Osoba**: autor/rysownik/kolorysta/tłumacz (ogólniej: „ludzie”).

### 2.2. Minimalne wymagane widoki (aktualizacja URL)
- Strona główna: zapowiedzi + nowości + wyróżnienia.
- Landing pages działów:
  - `/publikacje/` (główna linia)
  - `/dobre-licho/` (imprint)
  - `/mecenat/`
  - `/studio/`
- Dział „Ludzie” (`/ludzie/`) + profile (`/ludzie/<slug>/`).
- Strony projektów (kanoniczne):
  - `/publikacje/<slug>/`, `/dobre-licho/<slug>/`, `/mecenat/<slug>/`, `/studio/<slug>/`
- Strony wydań (kanoniczne):
  - `/publikacje/<projekt>/<wydanie>/`, `/dobre-licho/<projekt>/<wydanie>/`, `/mecenat/<projekt>/<wydanie>/`, `/studio/<projekt>/<wydanie>/`
  - wyjątek: jednotomówki Studio poprzez `editions/index.md` (patrz 0.3.3).
- Legacy aliasy:
  - `/<slug>/` przekierowuje (stub) do strony kanonicznej, z wyjątkiem projektów oznaczonych jako legacy landing.

---

## 3. Model treści (bez HTML) i format edycji

### 3.1. Format
- Markdown z frontmatter YAML (łatwe dla nietechnicznych; można edytować w GitHub UI).
- Obrazy zostają w `img/` (na start), a w treściach są referencje do ścieżek.

### 3.2. Proponowana struktura katalogów treści
- `content/pages/` — strony statyczne
- `content/lines/` — działy: diablaq, dobre-licho, mecenat, studio
- `content/projects/` — serie/projekty (np. spz, bzik)
- `content/editions/` — wydania/numeracja (np. bzik/05)
- `content/people/` — profile ludzi

Alternatywa (czytelniejsza, polecana): trzymanie wydań pod projektami:
- `content/projects/bzik/editions/05.md`

### 3.3. Kontrakty danych (minimum)

#### `Line` (dział)
- `slug`: `diablaq` | `dobre-licho` | `mecenat` | `studio`
- `title`
- `description` (Markdown)

#### `Project` (seria/projekt)
- `slug`
- `title`
- `line`: `diablaq` | `dobre-licho` | `mecenat` | `studio`
- `summary`
- `cover_image`
- `legacy_path` (np. `/spz/`)
- `body` (Markdown)

#### `Edition` (wydanie/numer)
- `project`: slug projektu
- `number` (opcjonalnie) lub `slug` (np. `exxxtra-2`)
- `title`
- `release` (tekstowo: `czerwiec 2025`)
- `release_date`: **wymagane**, format ISO `YYYY-MM-DD` (używane do sortowania, list „Nowości” i „Zapowiedzi” oraz ewentualnie osi czasu)
- `legacy_anchor` (np. `spz2`, `bzik5`, `bzik_x2`)
- `covers[]`: `{image, alt, caption}`
- `creators[]`: `{role, name, person_slug?}`
- `specs`: `{pages, binding, size, price, isbn}` (pola opcjonalne)
- `buy_links[]`: `{label, url}`
- `body` (Markdown)
- `status` / `highlights`:
  - `is_new: true|false` (pojawia się na `/nowe/` oraz może być wyróżnione na home)
  - `is_announcement: true|false` (pojawia się na `/zapowiedzi/` oraz może być wyróżnione na home)
  - opcjonalnie: `presale_url` (jeśli zapowiedź ma przedsprzedaż)

Walidacja:
- generator ma zgłaszać błąd builda, jeśli:
  - brakuje `release_date`
  - `is_new: true` i `is_announcement: true` jednocześnie

#### `Person` (ludzie)
- `slug`
- `name`
- `bio` (Markdown)
- `links[]` (opcjonalnie)

#### `Page` (strony statyczne)
- `slug`: np. `kontakt`
- `title`
- `body`

---

## 4. Szablony Jinja (mapa na mockupy Penpot)

### 4.1. Widoki Penpot (źródła)
- `Strona główna DESKTOP/MOBILE`
- `Zapowiedzi DESKTOP/MOBILE`
- `Nowości DESKTOP/MOBILE`
- `O Komiksie DESKTOP/MOBILE`
- `O autorze DESKTOP/MOBILE`
- `MENU MOBILE`

### 4.2. Proponowane templates/pages
- `base.html`: head, header/nav, footer, wersja mobilna menu
- `home.html`: sekcje (zapowiedzi/nowości)
- `line.html`: listing działu (`/diablaq/`, `/dobre-licho/`, `/mecenat/`, `/studio/`)
- `project.html`: projekt/seria, w tym legacy `/<slug>/`
- `edition.html`: strona wydania/numeru (mockup "O Komiksie")
- `people_index.html`: `/ludzie/`
- `person.html`: `/ludzie/<slug>/` (mockup "O autorze")
- `page.html`: np. `/kontakt/`
- `404.html`
- `listing.html`: uniwersalny listing wykorzystywany przez `/nowe/` i `/zapowiedzi/` (oraz opcjonalnie jako baza dla `/diablaq/`, `/studio/`, itp.)

### 4.3. Proponowane partials/components
- `_nav.html`
- `_mobile_menu.html`
- `_footer.html`
- `_card.html`
- `_covers.html`
- `_buy_links.html`
- `_creators.html`

---

## 5. CSS (Pico + brand)

### 5.1. Założenia
- Maksymalnie semantyczny HTML.
- Minimum klas: tylko do layoutu (grid, karty, badge, hero).

### 5.2. Plan
1. Dodać Pico.css (lokalnie w repo).
2. Dodać warstwę brandującą (można startowo bazować na obecnym `css/diablaq.css` – dziś to głównie zmienne kolorów).
3. Dopasować komponenty z mockupów: nawigacja, listing kart, układ strony "O Komiksie".

---

## 6. Plan wykonawczy (etapy) — aktualny stan i kolejne kroki

### Etap 1 — generator (MVP) [ZROBIONE]
- ✅ Loader frontmatter+Markdown.
- ✅ Jinja2 render.
- ✅ Build do `dist/`.
- ✅ Kopiowanie assetów (`img/`, `css/`, `CNAME`, `.nojekyll`).
- ✅ Listing: `/nowe/` i `/zapowiedzi/` (sortowanie: `release_date` malejąco).
- ✅ Routing kanoniczny wg działów: `/publikacje/`, `/dobre-licho/`, `/mecenat/`, `/studio/`.
- ✅ Legacy alias `/<slug>/` jako redirect-stub, wyjątek: `/bzik/` jako landing z anchorami.

### Etap 2 — migracja treści (inkrementalnie) [W TOKU]
- ✅ SPZ (landing legacy + kanoniczne strony wydań pod `/publikacje/spz/...`).
- ✅ BZIK (landing legacy `/bzik/` + kanoniczne wydania pod `/mecenat/bzik/..` z wiodącym zerem dla 1–9).
- ✅ Dobre Licho: Pisto (kanonicznie `/dobre-licho/pisto/...`).
- ✅ Pojedyncze komiksy: mama, pzg, hadfield.
- ✅ Obietnica jako osobny tytuł + `/zvyrke/` jako alias profilu.
- ✅ Studio: `paatrzcie` jako jednotomówka pod `/studio/paatrzcie/`.

Następne rzeczy do zmigrowania (treści):
- [ ] pozostałe serie/landing pages: belzebubs, ciecio, karmiciel, kodiak, midguard, winon — uzupełnić opisy projektów + spiąć ewentualne brakujące wydania.
- [ ] uzupełnić profile ludzi (`content/people/*.md`) i podlinkować `person_slug` w twórcach.
- [ ] dopracować daty `release_date` (zwłaszcza tam gdzie dziś są placeholdery „brak dokładnej daty”).

### Etap 3 — layout z Penpot [ZROBIONE]
- ✅ Przeniesione szablony MVP na układ zgodny z mockupami (topbar, listingi, karty).
- ✅ Pico.css lokalnie + brand overlay w `css/diablaq.css`.
- ✅ Nawigacja mobilna (mockup MENU MOBILE) + spójna kolejność linków.

### Etap 4 — Instrukcja dla redagujących [ZROBIONE]
- ✅ Instrukcja edycji treści (projekty / wydania / ludzie / nowości i zapowiedzi): `_migracja/INSTRUKCJA_DLA_REDAGUJACYCH.md`.
- ✅ Zasady PR workflow (branch, małe zmiany, checklist, weryfikacja builda): w tej instrukcji.

Skrót dla redagujących (TL;DR):
- Treści edytujemy tylko w `content/`.
- Obrazki wrzucamy do `img/` i linkujemy ścieżką `/img/...`.
- `release_date` (YYYY-MM-DD) jest obowiązkowe w wydaniach.
- `is_new` i `is_announcement` są wzajemnie wykluczające.

Walidacje (dla maintainerów):
- `python scripts/check_edition_fields.py`
- `python scripts/check_legacy_anchors.py`

### Etap 5 — SEO i redirecty (najniższy priorytet)
- [ ] `rel="canonical"` dla stron będących aliasem treści.
- [ ] Rozważyć Cloudflare redirect rules (301/308) po stabilizacji.

---

## 7. Ryzyka i decyzje do obserwacji
- Anchory legacy: muszą zostać na stronach, które mają historyczne linki.
- Duplikacja treści (alias vs kanoniczny URL): ogarniać przez canonical/Cloudflare – ale dopiero po stabilizacji.
- Fonty w SVG z Penpot odnoszą się do `localhost` — nie kopiować 1:1; osobna decyzja o hostowaniu fontów.

Doprecyzowania (ustalone):
- `/zvyrke/` po migracji jest **aliasem profilu** `/ludzie/zvyrke/`.
- Obecna treść w `/zvyrke/` opisuje komiks **„Obietnica”** i ten tytuł dostaje **własną podstronę** (osobny wpis w katalogu tytułów/wydań).
- Wydania BZIK mają **osobne URL-e** (np. `/mecenat/bzik/5/`), a `/bzik/` pozostaje landingiem.
- Projekty w dziale `/studio/` grupujemy **chronologicznie**.

---

## 8. Miejsce na doprecyzowania (dla Ciebie)

### 8.1. `/zvyrke/` po migracji
Obecnie `/zvyrke/` wygląda jak strona produktu ("Obietnica") przypisana do autora.

Do rozstrzygnięcia:
- [x] `/zvyrke/` zostaje jako alias profilu `/ludzie/zvyrke/`
- [x] "Obietnica" staje się osobną podstroną tytułu (a profil autora jest osobno)
- [ ] inne: __________

### 8.2. Studio
- Jak grupować projekty studia? (klient, seria, rok?)
  - [x] chronologicznie
  - [ ] inne: __________

### 8.3. Wymagane pola katalogowe
- Czy ceny, ISBN i daty premiery są obowiązkowe w każdym wpisie?
  - Decyzja: TBD.
