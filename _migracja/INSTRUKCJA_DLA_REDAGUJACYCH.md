# Jak edytować treści na stronie diablaq.com (dla osób nietechnicznych)

## TL;DR
- Treści edytujemy w `content/` (nie w `dist/`).
- Obrazki dodajemy do `img/` i linkujemy jako `/img/nazwa-pliku.jpg`.
- `release_date` w wydaniach jest **zalecane**, ale może być puste/brak (wtedy pozycja jest zapowiedzią).
- Nowości i zapowiedzi wyliczają się automatycznie podczas builda (bez ręcznego przerzucania między listami).
- `is_new: true` i `is_announcement: true` **nie mogą** być ustawione jednocześnie.
- Nazwy folderów/plików w `content/` są częścią adresu URL — nie zmieniaj ich bez konsultacji.
- **Numeracja wydań** jest automatyczna (chronologicznie). Dla jednotomówek użyj `standalone: true`.
- **Podserie** (np. BZIK eXXXtra) mają własną numerację — użyj `subseries: "nazwa"`.

Ta strona jest generowana automatycznie z plików tekstowych (Markdown). Nie trzeba edytować HTML.

## Jak wygląda praca (workflow)
1. Zrób kopię repozytorium (fork) i sklonuj ją na komputer.
2. Utwórz nową gałąź (branch) do zmian.
3. Edytuj lub dodaj pliki treści (Markdown) w folderze `content/`.
4. Sprawdź podgląd lokalnie (opcjonalnie, jeśli masz środowisko uruchomieniowe).
5. Wypchnij zmiany i otwórz Pull Request.

> W Pull Requeście najlepiej opisać: co zostało dodane/zmienione oraz wkleić linki do wygenerowanych podstron (po deployu preview) lub screeny.

---

## Szybkie uzupełnianie wielu stron projektów naraz
Jeśli trzeba szybko dopisać lub poprawić opisy w wielu plikach `content/projects/*/project.md`, najwygodniej użyć skoroszytu roboczego.
To jest jedna zbiorcza lista projektów do uzupełnienia, zamiast ręcznego otwierania każdego pliku osobno.

### Krok 1: wygeneruj skoroszyt
```bash
uv run diablaq-project-workbook export
```

Po tym poleceniu w katalogu głównym repo pojawi się plik `project-page-workbook.md`.
Domyślnie są tam tylko projekty, które mają braki (np. pusty opis, brak `summary`, pusty `project.md`).

Jeśli chcesz zobaczyć wszystkie projekty, użyj:
```bash
uv run diablaq-project-workbook export --all
```

### Krok 2: uzupełnij treść w jednym pliku
Otwórz `project-page-workbook.md` i edytuj tylko zawartość między markerami:
- `<!-- FRONTMATTER START: ... -->` i `<!-- FRONTMATTER END: ... -->`
- `<!-- BODY START: ... -->` i `<!-- BODY END: ... -->`

Każda sekcja zawiera już:
- ścieżkę do właściwego pliku,
- informację, czego w nim brakuje,
- obecne pola `title`, `line`, `summary`, `cover_image`,
- pomocnicze notatki z plików wydań.

Dzięki temu da się szybko uzupełnić opisy nawet wtedy, gdy część stron projektów jest pusta.

### Krok 3: zapisz zmiany z powrotem do plików projektu
```bash
uv run diablaq-project-workbook import
```

Ważne:
- jeśli YAML/frontmatter jest błędny, import zatrzyma się przed zapisem,
- niezmienione sekcje są pomijane,
- projekty bez zmian nie są nadpisywane.

### Krok 4: sprawdź wynik
```bash
uv run diablaq-build
```

---

## Gdzie są treści
Treści znajdują się w folderze `content/` i są podzielone na typy:
- `content/pages/` — strony statyczne (np. Kontakt)
- `content/projects/` — serie/projekty (np. SPZ, BZIK)
- `content/projects/<projekt>/editions/` — wydania/numeracja (np. BZIK #05)
- `content/people/` — profile osób ("Ludzie")

> Uwaga: nazwy folderów i plików są częścią adresu strony (URL), więc nie zmieniaj ich bez konsultacji.

---

## Gdzie wrzucać okładki i obrazki
Wszystkie obrazy trzymamy w katalogu `img/`.

Zasady:
- Plik okładki / podglądu dodaj do `img/`.
- W treści **zawsze** odwołuj się ścieżką zaczynającą się od `/img/…`.
- Najlepiej używać formatów: `.jpg` (zwykle) lub `.png`.
- Nazwy plików staramy się robić krótkie i jednoznaczne.

Przykłady:
- okładka tomu: `/img/spz1.jpg`
- alternatywna okładka: `/img/spz1-blank.jpg`
- podgląd strony: `/img/spz1-page1.jpg`

> Jeśli obrazek jest duży, warto go wstępnie skompresować (żeby strona szybko się ładowała), ale to nie jest twardy wymóg na tym etapie.

---

## Format plików (Markdown + nagłówek YAML)
Każdy plik ma:
1) nagłówek (YAML) między `---` i `---`
2) treść w Markdown poniżej.

### Krótka zasada
- **Nagłówek YAML**: dane (tytuł, data, parametr, okładki, linki)
- **Markdown pod spodem**: opis

---

## Projekty/serie/jednotomówki (`content/projects/<slug>/project.md`)
To jest strona "serii" albo "projektu".

### Najważniejsze pola (YAML)
- `title` (tekst) — nazwa projektu/serii, np. `"Spółka ZŁO"`
- `line` (tekst) — do jakiej sekcji należy projekt:
  - `diablaq` → `/publikacje/<slug>/`
  - `dobre-licho` → `/dobre-licho/<slug>/`
  - `mecenat` → `/mecenat/<slug>/`
  - `studio` → `/studio/<slug>/`
- `summary` (tekst, opcjonalne) — krótki opis do kafelków/listingów
- `cover_image` (ścieżka, opcjonalne, ale zalecane) — okładka reprezentatywna projektu (do kafelków sekcji), np. `"/img/spz1.jpg"`
- `legacy_path` (ścieżka, opcjonalne) — stary adres (np. `/spz/`) dla zgodności linków
- `legacy_landing` (`true/false`, opcjonalne) — czy pod starym adresem ma być landing z treścią (zamiast przekierowania)

### Jednotomówki (np. `mama`, `pzg`)
Jednotomówka nadal jest trzymana jako „projekt", ale zwykle ma **tylko jedno wydanie** w folderze `editions/`:
- `content/projects/mama/editions/index.md`
- `content/projects/pzg/editions/index.md`

> **Konwencja nazewnictwa plików wydań:**
> - **Jednotomówki** (standalone): używaj `index.md`
> - **Serie numerowane**: używaj `01.md`, `02.md`, `03.md`...
> - **Podserie**: możesz używać prefixu np. `x1.md`, `x2.md` dla eXXXtra
> - **Wydania specjalne**: używaj opisowych nazw np. `cudowni.md`, `drzazga.md`

To znaczy: dane są takie jak w serii, ale **strona projektu** w serwisie jest wygodniejsza:
- jeśli projekt ma dokładnie **1 wydanie**, strona projektu pokaże od razu szczegóły (okładka, metryczka, opis),
- jeśli projekt ma **2+ wydań**, strona projektu pokaże listę wydań.

Jeśli w przyszłości pojawi się np. wznowienie, dodajemy nowe wydanie (np. `02.md`) **albo** (jeśli treść się nie zmienia) dokładamy nową okładkę w polu `covers` w istniejącym wydaniu.

---

## Przykład: uzupełnienie brakującej okładki
Jeśli w pliku wydania widzisz uwagę w stylu: „Okładka do uzupełnienia…”, zrób to tak:
1. Dodaj plik do `img/` (np. `img/paatrzcie.jpg`).
2. W pliku wydania dodaj pole:
   - `cover_image: "/img/paatrzcie.jpg"`
3. Zapisz i wyślij Pull Request.

---

## Wydania (`content/projects/<slug>/editions/<edition>.md`)
To jest strona konkretnego tomu/numeru.

### Pola obowiązkowe
- `title` — tytuł wydania (np. `"Spółka ZŁO #1"`)

### Daty i automatyczne „Nowości” / „Zapowiedzi”
- `release_date` (zalecane) — data premiery w formacie `YYYY-MM-DD` (np. `2025-06-01`).

Generator podczas builda automatycznie klasyfikuje wydania:
1. Jeśli `release_date` jest puste lub nie ma go w pliku → **Zapowiedzi**.
2. Jeśli `release_date` jest w przyszłości → **Zapowiedzi**.
3. Jeśli `release_date` jest dziś lub w przeszłości → **Nowości** przez **6 tygodni** od premiery.

Po 6 tygodniach pozycja wypada z „Nowości”.

### Override (wymuszenie pozycji)
Jeżeli chcesz wymusić obecność na liście niezależnie od daty, użyj:
- `is_announcement: true` — wymusza „Zapowiedzi”
- `is_new: true` — wymusza „Nowości”

> Te pola działają jako override (wymuszenie). Nadal nie wolno ustawiać obu naraz.

### Pola bardzo często używane
- `release` (tekst, opcjonalne) — ludzki opis daty, np. `"premiera - grudzień 2024"`
- `presale_url` (URL, opcjonalne) — link do przedsprzedaży (zwykle tylko dla zapowiedzi)

Ważne:
- Pozycja **nie może** mieć jednocześnie `is_new: true` i `is_announcement: true`.

### Okładki i podglądy
Możesz użyć dwóch sposobów:

1) Pojedyncza okładka (najprostsze)
- `cover_image: "/img/..."`
- `cover_alt: "..."` (opis alternatywny, opcjonalny)

2) Wiele okładek (gdy są warianty)
- `covers:` — lista okładek (pierwsza z listy jest traktowana jako główna do skrótów, jeśli nie ma `cover_image`)

Przykład:
```yaml
cover_image: "/img/spz1.jpg"
cover_alt: "Spółka ZŁO #1 – okładka"

covers:
  - image: "/img/spz1.jpg"
    alt: "Spółka ZŁO #1 – okładka standard"
    caption: "Standard"
  - image: "/img/spz1-blank.jpg"
    alt: "Spółka ZŁO #1 – okładka blank"
    caption: "Blank"

previews:
  - image: "/img/spz1-page1.jpg"
    alt: "Spółka ZŁO #1 – strona 1"
    caption: "Strona 1"
```

### Twórcy
Pole `creators` jest listą. Najczęściej używamy formatu obiektowego:
```yaml
creators:
  - role: "Scenariusz"
    name: "Imię Nazwisko"
  - role: "Rysunki"
    name: "Imię Nazwisko"
```

Jeśli dana osoba ma profil w `content/people/`, można dodać linkowanie:
```yaml
  - role: "Rysunki"
    name: "Zvyrke"
    person_slug: "zvyrke"
```

### Parametry wydania (metryczka)
- `specs:` — słownik (klucz → wartość), np. liczba stron, format, cena, ISBN.

Przykład:
```yaml
specs:
  "Liczba stron": "24"
  "Oprawa": "zeszytowa"
  "Wymiary": "170 x 240 mm"
  "Cena": "19,99 zł"
  "ISBN-13": "978..."
```

### Linki do zakupu
- `buy_links:` — lista linków, każdy ma `label` i `url`.

Przykład:
```yaml
buy_links:
  - label: "Kup w naszym sklepie"
    url: "https://..."
```

### Pola legacy (zgodność ze starymi linkami)
- `legacy_anchor` — jeśli stara strona miała linki w stylu `/bzik/#bzik3`.

### Numeracja wydań (automatyczna)

Generator automatycznie nadaje numery wydaniom w serii na podstawie `release_date` (chronologicznie od najstarszego). Numer wyświetlany jest jako badge na okładce (np. `#01`, `#02`).

#### Jednotomówki (bez numeracji)
Jeśli komiks jest jednotomówką i nie powinien mieć numeru, dodaj:
```yaml
standalone: true
```

Przykład (`content/projects/mama/editions/index.md`):
```yaml
---
title: "Mama zabiła mi psa"
release_date: 2024-08-12
standalone: true
cover_image: "/img/mama.jpg"
---
```

#### Podserie (niezależna numeracja)
Jeśli projekt ma kilka podserii z niezależną numeracją (np. BZIK ma serię główną i eXXXtra), użyj pola `subseries`:

```yaml
# Seria główna (bez subseries) - numeracja: #01, #02, #03...
---
title: "BZIK #1"
release_date: 2024-01-01
---

# Podseria eXXXtra - własna numeracja: #01, #02, #03...
---
title: "BZIK eXXXtra #1"
release_date: 2024-05-01
subseries: "eXXXtra"
---
```

#### Ręczne nadpisanie numeru
Jeśli chcesz wymusić konkretny numer (np. dla numerów specjalnych), użyj:
```yaml
issue_number: 0
```

---

## Profile osób (`content/people/<slug>.md`)
- `name` — imię i nazwisko / pseudonim

Treść Markdown poniżej to bio / opis.

---

## Strony statyczne (`content/pages/<slug>.md`)
- `title` — tytuł strony

Treść Markdown poniżej to zawartość strony.

---

## Dodanie nowego wydania (krok po kroku)
1. Znajdź projekt/serię, np. `content/projects/spz/`.
2. Wejdź do `editions/`.
3. Skopiuj istniejący plik wydania i zmień:
   - nazwę pliku (np. `02.md` → `03.md`)
   - pola w nagłówku YAML
   - opis w Markdown
4. Dodaj okładkę do `img/` (jeśli to nowy plik) i wpisz ścieżkę w `cover_image` lub w `covers`.
5. Jeśli to zapowiedź, ustaw `is_announcement: true`. Jeśli nowość, `is_new: true`.

---

## Dodanie nowego projektu/serii (krok po kroku)
1. Utwórz folder w `content/projects/` o nazwie będącej slug-iem (krótka nazwa bez spacji, np. `nowa-seria`).
2. W tym folderze utwórz plik `project.md`:
   ```yaml
   ---
   title: "Nowa Seria"
   line: "diablaq"  # lub mecenat, dobre-licho, studio
   summary: "Krótki opis do listingów"
   cover_image: "/img/nowa-seria.jpg"
   ---
   
   Dłuższy opis projektu/serii (opcjonalny).
   ```
3. Utwórz folder `editions/` wewnątrz projektu.
4. Dodaj pierwsze wydanie (np. `01.md`) - patrz sekcja "Dodanie nowego wydania".

---

## Zmiana jednotomówki w serię

Jeśli jednotomówka (np. "Pisto") dostaje kontynuację i staje się serią:

### Krok 1: Zmień nazwę pliku i usuń `standalone: true`
Zmień nazwę `content/projects/pisto/editions/index.md` → `01.md` i edytuj:
```yaml
---
title: "Pisto #1"
release_date: 2025-02-01
# standalone: true  ← USUŃ tę linię
cover_image: "/img/pisto1.jpg"
---
```

### Krok 2: Dodaj kolejne wydanie
Utwórz `content/projects/pisto/editions/02.md`:
```yaml
---
title: "Pisto #2"
release_date: 2025-08-01
cover_image: "/img/pisto2.jpg"
---
```

### Krok 3: Zaktualizuj tytuł (opcjonalnie)
Jeśli pierwszy tom nie miał numeru w tytule, zaktualizuj go:
- `title: "Pisto"` → `title: "Pisto #1"`

Po rebuildzie strona projektu automatycznie zmieni się z widoku jednotomówki na listę wydań z numeracją.

---

## Zmiana serii w jednotomówkę (rzadki przypadek)

Jeśli seria zostaje wycofana i zostaje tylko jeden tom:

1. Usuń niepotrzebne pliki wydań z `editions/`.
2. Zmień nazwę pozostałego pliku na `index.md`.
3. Do pozostałego wydania dodaj `standalone: true`.
4. Opcjonalnie usuń numer z tytułu.

---

## Checklist przed wysłaniem Pull Request
- Czy `release_date` (jeśli podane) jest w formacie `YYYY-MM-DD`?
- Czy obrazki są w `img/` i mają ścieżki `/img/...`?
- Czy nie ustawiono jednocześnie `is_new` i `is_announcement`?
- Czy nie zmieniono nazw folderów/plików w `content/` bez potrzeby?

---

## Czego nie robić
- Nie edytuj plików w `dist/` (jeśli istnieje) — to katalog generowany.
- Nie zmieniaj masowo nazw folderów/plików w `content/` (to zmienia adresy URL).
- Nie wklejaj dużych bloków HTML do treści — używaj Markdown.

---

## Pytania / pomoc
Jeśli nie masz pewności, jak coś dodać (np. nowy typ treści, nietypowa okładka, wiele wariantów okładki), dopisz komentarz w Pull Requeście: „Pytanie do maintainerów” i opisz, czego potrzebujesz.

---

## Standard nazewnictwa plików w `img/` (zalecane)
Żeby utrzymać porządek, polecamy prosty standard nazw plików:

### Okładki wydań
- serie numerowane: `<slug-projektu><numer>.<ext>`
  - np. `spz1.jpg`, `spz2a.jpg` (wariant A), `spz2b.jpg` (wariant B)
- jednotomówki: `<slug-projektu>.<ext>`
  - np. `mama.jpg`, `pzg.jpg`, `tesla.jpg`
- wydania nienumeryczne (slug wydania): `<slug-projektu>_<slug-wydania>.<ext>`
  - np. `midguard_cudowni_0.jpg` (jeśli tak już jest w repo, zachowujemy)

### Podglądy stron / sample
- `<slug-projektu><numer>-page<nr>.<ext>`
  - np. `spz1-page1.jpg`, `spz1-page2.jpg`

### Ikony/UI
- assety UI trzymamy w `img/ui/` (np. `menu.svg`, `close.svg`).

> To są zalecenia, nie twarde wymaganie. Jeśli w repo istnieją już stare nazwy, nie zmieniamy ich masowo.
