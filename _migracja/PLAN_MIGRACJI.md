# Plan migracji diablaq.com → generator statyczny (Python + Jinja) + treści w Markdown
  - Decyzja: TBD.
- Czy ceny, ISBN i daty premiery są obowiązkowe w każdym wpisie?
### 8.3. Wymagane pola katalogowe

  - Decyzja: TBD.
- Jak grupować projekty studia? (wg klienta, serii, roku?)
### 8.2. Studio

  - Decyzja: TBD (wymaga doprecyzowania, bo obecnie to mieszany przypadek).
- Czy `/zvyrke/` ma zostać jako alias profilu, czy ma stać się stroną tytułu ("Obietnica")?
  - Decyzja: **landing** (ustalone).
- Czy `/bzik/` ma zawsze być landingiem (bez redirectów), czy kiedykolwiek przekierować go na `/mecenat/bzik/`?
### 8.1. URL-e i kanoniczność

## 8. Miejsce na doprecyzowania (dla Ciebie)

---

- Fonty w SVG z Penpot odnoszą się do `localhost` — nie kopiować 1:1; zdecydować osobno o hostowaniu fontów.
- Duplikacja treści (alias vs kanoniczny URL): ogarniać przez canonical/Cloudflare – ale dopiero po stabilizacji.
- Anchory legacy: muszą zostać na stronach, które mają historyczne linki.
## 7. Ryzyka i decyzje do obserwacji

---

- Cloudflare redirect rules (301/308) dla tych przypadków, które chcemy domknąć.
- Canonical URLs dla aliasów (`/bzik/` vs `/mecenat/bzik/`).
### Etap 5 — SEO i redirecty (najniższy priorytet)

Cel: pełny katalog z filtrowaniem po działach.
### Etap 4 — działy: `/mecenat/`, `/studio/`, `/ludzie/`, `/diablaq/`, `/dobre-licho/`

5. ludzie: `zvyrke` → `/ludzie/zvyrke/` + powiązania
4. reszta serii i single
3. `bzik` (dużo sekcji + listy autorów + anchory)
2. `hadfield` (single)
1. `spz` (kilka wydań + multi okładki)
Proponowana kolejność (stres-test danych):
### Etap 3 — migracja treści (inkrementalnie)

- Karty katalogowe + listingi.
- Implementacja `base.html`, nav, mobile menu.
Cel: mieć działającą stronę w docelowym układzie i responsywności.
### Etap 2 — implementacja layoutu z Penpot

- Skopiować assety (`img/`, `css/`, `CNAME`, `.nojekyll`).
- Wprowadzić Jinja+render.
- Wprowadzić podstawowy loader frontmatter+Markdown.
Cel: wygenerować `home`, `projekt`, `kontakt` z prostymi danymi.
### Etap 1 — generator (MVP)

- Uzgodnić minimalne komendy: build + local preview.
- Wybrać docelowy katalog wyjściowy (np. `dist/`).
### Etap 0 — przygotowanie pracy (bez zmian w treści)

## 6. Plan wykonawczy (etapy)

---

3. Dopasować komponenty z mockupów: nawigacja, listing kart, układ strony "O Komiksie".
2. Dodać warstwę brandującą (na start można bazować na obecnym `css/diablaq.css` – dziś to głównie zmienne kolorów).
1. Dodać Pico.css (lokalnie w repo).
### 5.2. Plan

- Minimum klas: tylko do layoutu (grid, karty, badge, hero).
- Maksymalnie semantyczny HTML.
### 5.1. Założenia

## 5. CSS (Pico + brand)

---

- `_creators.html`
- `_buy_links.html`
- `_covers.html`
- `_cards.html` / `_card.html`
- `_footer.html`
- `_mobile_menu.html`
- `_nav.html`
### 4.3. Proponowane partials/components

- `404.html`
- `page.html`: np. `/kontakt/`
- `person.html`: `/ludzie/<slug>/` (mockup "O autorze")
- `people_index.html`: `/ludzie/`
- `edition.html`: strona wydania/numeru (mockup "O Komiksie")
  - render listy wydań (jeśli są)
  - dla legacy `/<slug>/` (serie/one-shot w starych URL-ach)
- `project.html`:
- `line.html`: listing działu (`/diablaq/`, `/dobre-licho/`, `/mecenat/`, `/studio/`)
- `home.html`: sekcje (zapowiedzi/nowości)
- `base.html`: head, header/nav, footer, wersja mobilna menu
### 4.2. Proponowane templates/pages

- `MENU MOBILE`
- `O autorze DESKTOP/MOBILE`
- `O Komiksie DESKTOP/MOBILE`
- `Nowości DESKTOP/MOBILE`
- `Zapowiedzi DESKTOP/MOBILE`
- `Strona główna DESKTOP/MOBILE`
### 4.1. Widoki Penpot (źródła)

## 4. Szablony Jinja (mapa na mockupy Penpot)

---

- `body`
- `title`
- `slug`: np. `kontakt`
#### `Page` (strony statyczne)

- `links[]` (opcjonalnie)
- `bio` (Markdown)
- `name`
- `slug`
#### `Person` (ludzie)

- `body` (Markdown)
- `buy_links[]`: `{label, url}`
- `specs`: `{pages, binding, size, price, isbn}` (pola opcjonalne)
- `creators[]`: `{role, name, person_slug?}`
- `covers[]`: `{image, alt, caption}`
- `legacy_anchor` (np. `spz2`, `bzik5`, `bzik_x2`)
- `release` (tekstowo, np. `czerwiec 2025`)
- `title`
- `number` (opcjonalnie) lub `slug` (np. `exxxtra-2`)
- `project`: slug projektu
#### `Edition` (wydanie/numer)

- `body` (Markdown)
- `legacy_path` (np. `/spz/`)
- `cover_image`
- `summary`
- `line`: `diablaq` | `dobre-licho` | `mecenat` | `studio`
- `title`
- `slug`
#### `Project` (seria/projekt)

- `description` (Markdown)
- `title`
- `slug`: `diablaq` | `dobre-licho` | `mecenat` | `studio`
#### `Line` (dział)

### 3.3. Kontrakty danych (minimum)

- `content/projects/bzik/editions/05.md`
Alternatywa: trzymanie wydań pod folderami projektów (czytelniejsze):

- `content/people/` — profile ludzi
- `content/editions/` — wydania/numeracja (np. bzik/05)
- `content/projects/` — serie/projekty (np. spz, bzik)
- `content/lines/` — działy: diablaq, dobre-licho, mecenat, studio
- `content/pages/` — strony statyczne

*(docelowa dla generatora; do wykonania w kolejnych etapach)*
### 3.2. Proponowana struktura katalogów treści

- Obrazy zostają w `img/` (na start), a w treściach referencje do ścieżek.
- Markdown z frontmatter YAML (łatwe dla nietechnicznych; można edytować w GitHub UI).
### 3.1. Format

## 3. Model treści (bez HTML) i format edycji

---

- Strona serii (legacy: `/<slug>/`) oraz strona wydania (kanoniczna: jak w BZIK).
- Dział „Ludzie” + profile.
- Dział „Studio” + projekty.
- Dział „Mecenat” + projekt (BZIK).
- Listing “Diablaq”, listing “Dobre Licho”.
- Strona główna: zapowiedzi + nowości + wyróżnienia.
### 2.2. Minimalne wymagane widoki

- **Osoba**: autor/rysownik/kolorysta/tłumacz (ogólniej: „ludzie”).
- **Wydanie / numer / pozycja**: konkretne tomy/zeszyty/numer z okładką, specyfikacją, listą twórców.
- **Seria / projekt**: SPZ, BZIK, Pisto… (u Ciebie większość legacy katalogów).
- **Linia / dział**: Diablaq, Dobre Licho, Mecenat, Studio.
### 2.1. Koncepcje domenowe

## 2. Docelowa architektura informacji (IA)

---

Wniosek: nowy system powinien potrafić zachować anchor `id` na stronach legacy.

- `bzik/index.html`: `id="bzik1".."bzik7"`, `bzik_x1` itd. (homepage linkuje do `/bzik/#...`).
- `spz/index.html`: sekcje `id="spz1"`, `id="spz2"` (homepage linkuje m.in. do `/spz/#spz2`).
### 1.2. Ważne legacy anchory

- **Serie Dobre Licho**: `pisto` (+ `hadfield` jako single).
- **Serie głównej linii (Diablaq)**: `belzebubs`, `ciecio`, `karmiciel`, `kodiak`, `midguard`, `spz`, `winon`.
- **Mecenat**: `bzik`.
- **Autorzy**: `zvyrke`.
  - Uwaga: `hadfield` należy do Dobre Licho.
- **Pojedyncze komiksy** (single): `hadfield`, `mama`, `pzg`  
### 1.1. Typy podstron (ustalone przez właściciela treści)

## 1. Inwentaryzacja obecnego repo (stan wejściowy)

---

- Na GitHub Pages można robić redirect-y stronami stub (meta/js), ale to nie musi być teraz.
- Redirecty (301/308) są **na końcu**; domena jest w Cloudflare, więc docelowo można użyć reguł Cloudflare.
### 0.4. Priorytet przekierowań

- Anchory typu `/bzik/#bzik5` są ważne (hash nie idzie do serwera), więc w landing page utrzymujemy sekcje z `id="bzik5"`, `id="bzik_x2"` itd.
- Kanoniczne strony numerów BZIK: `/mecenat/bzik/<id>/` (np. `/mecenat/bzik/5/`).
- `/bzik/` staje się **landing page** (legacy), linkujący do poszczególnych numerów.
**Specjalna decyzja dla BZIK:**

- **Linie wydawnicze jako listingi**: `/diablaq/` oraz `/dobre-licho/`.
- **Ludzie**: `/ludzie/` oraz `/ludzie/<slug>/` (np. `/ludzie/zvyrke/`).
- **Studio (produkcje dla innych)**: `/studio/` oraz `/studio/<projekt>/`.
- **Mecenat**: `/mecenat/` oraz `/mecenat/<projekt>/` (np. `/mecenat/bzik/`).
- `/_` nie dotyczy URL; to tylko repo.  
**Nowe działy (kanoniczne):**

- `/kontakt/`
- `/zvyrke/` (obecnie strona powiązana z autorem/tytułem)
- `/mama/`, `/pzg/`, `/hadfield/` (single)
- `/pisto/` (Dobre Licho)
- `/spz/`, `/belzebubs/`, `/ciecio/`, `/karmiciel/`, `/kodiak/`, `/midguard/`, `/winon/` (serie głównej linii)
**Legacy URL-e (zostają):**

Priorytet: **nie psuć istniejących linków**, redirecty mają niski priorytet.
### 0.3. URL-e (wariant A + nowe działy)

- Implementujemy layout jako szablony Jinja, nie kopiujemy wielolinijkowego HTML do Pythona.
- Źródło: `_penpot/*.svg` (widoki DESKTOP/MOBILE) + archiwum `_penpot/Diablaq/` (assets + manifest).
### 0.2. Mockupy / wzorzec UI

- CSS: **Pico.css** jako ultra-prosty framework + lekka warstwa brandująca (`css/diablaq.css` lub nowy plik z override’ami).
- Wynik: statyczny katalog (np. `dist/`) publikowany na GitHub Pages.
- **Generator statyczny w Pythonie**: renderowanie HTML z **Jinja2**, treść w **Markdown + frontmatter YAML**.
### 0.1. Technologie

## 0. Szybkie podsumowanie decyzji ("source of truth")

> Cel: Ułatwić edycję treści (bez dłubania w HTML) i wdrożyć nowe szablony z Penpot.  
> Repo: GitHub Pages (statycznie)  
> Data: 2026-01-05  


