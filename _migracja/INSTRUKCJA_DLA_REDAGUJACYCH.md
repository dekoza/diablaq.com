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

## Szybkie uzupełnianie wielu stron projektów i wydań naraz
Jeśli trzeba szybko dopisać lub poprawić opisy w wielu plikach `content/projects/*/project.md` i `content/projects/*/editions/*.md`, najwygodniej użyć skoroszytu roboczego.
To jest jedna zbiorcza lista do uzupełnienia, zamiast ręcznego otwierania każdego pliku osobno.

### Krok 1: wygeneruj skoroszyt
```bash
uv run diablaq-project-workbook export
```

Po tym poleceniu w katalogu głównym repo pojawi się plik `project-page-workbook.md`.
Domyślnie są tam tylko projekty, które same mają braki albo zawierają wydania wymagające uzupełnienia.

Jeśli chcesz zobaczyć wszystkie projekty i wszystkie istniejące wydania, użyj:
```bash
uv run diablaq-project-workbook export --all
```

### Krok 2: uzupełnij treść w jednym pliku
Otwórz `project-page-workbook.md` i edytuj tylko zawartość między markerami:
- `<!-- FRONTMATTER START: ... -->` i `<!-- FRONTMATTER END: ... -->`
- `<!-- BODY START: ... -->` i `<!-- BODY END: ... -->`
- `<!-- EDITION FRONTMATTER START: projekt/slug-wydania -->` i `<!-- EDITION FRONTMATTER END: projekt/slug-wydania -->`
- `<!-- EDITION BODY START: projekt/slug-wydania -->` i `<!-- EDITION BODY END: projekt/slug-wydania -->`

Każda sekcja zawiera już:
- ścieżkę do właściwego pliku,
- informację, czego w nim brakuje,
- gotowy szkielet pól z zakomentowanymi opcjami,
- podpowiedzi przy polach z krótką listą możliwych wartości (`line`, `kind`, `format`, `true | false` itd.),
- pomocnicze notatki z istniejących plików wydań.

Dzięki temu da się szybko uzupełnić opis projektu, opis konkretnego wydania albo oba naraz.

### Krok 2a: jak dodać nowe wydanie przez skoroszyt
W każdej sekcji projektu jest też `Szablon nowego wydania`.

Aby go użyć:
1. skopiuj oba bloki z identyfikatorem `__new_edition__`,
2. zmień identyfikator w obu markerach na docelowy slug, np. `bzik/09` albo `mama/index`,
3. dopiero potem wpisz właściwy frontmatter i opis.

Jeżeli zmienisz treść szablonu, ale zostawisz identyfikator `__new_edition__`, import zakończy się błędem — to zabezpieczenie przed przypadkowym zapisaniem szablonu jako prawdziwego pliku.

### Krok 3: zapisz zmiany z powrotem do plików treści
```bash
uv run diablaq-project-workbook import
```

Ważne:
- import parsuje tylko bloki między markerami; reszta skoroszytu jest ignorowana,
- jeśli YAML/frontmatter jest błędny, import zatrzyma się przed zapisem,
- niezmienione sekcje są pomijane,
- zapis trafia tylko do `content/projects/<slug>/project.md` i `content/projects/<slug>/editions/<edition>.md`,
- import może utworzyć nowy plik wydania, ale tylko wewnątrz istniejącego projektu,
- import nie tworzy nowych katalogów projektów.

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

Jeśli w przyszłości pojawi się np. wznowienie, dodajemy nowe wydanie (np. `02.md`) **albo** (jeśli treść się nie zmienia) dokładamy nową okładkę w polu `alternate_covers` w istniejącym wydaniu.

---

## Przykład: uzupełnienie brakującej okładki
Jeśli w pliku wydania widzisz uwagę w stylu: „Okładka do uzupełnienia…”, zrób to tak:
1. Dodaj plik do `img/` (np. `img/paatrzcie.jpg`).
2. W pliku wydania uzupełnij `primary_cover.image`, np.:
   - `primary_cover:`
   - `  image: "/img/paatrzcie.jpg"`
3. Opcjonalnie dopisz `alt`, `artist_name` i `person_slug`.
4. Zapisz i wyślij Pull Request.

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

### Okładki, podglądy i produkty
Wydanie ma teraz jeden spójny układ:

#### 1) Główna okładka
```yaml
primary_cover:
  label: "Standardowa"          # opcjonalne
  image: "/img/spz1.jpg"
  alt: "Spółka ZŁO #1 – okładka standardowa"
  artist_name: "Piotr Burzyński" # opcjonalne
  person_slug: "piotr-burzynski" # opcjonalne
```

#### 2) Okładki alternatywne
Każda alternatywna okładka ma własne `id`, bo produkty mogą się do niej odwoływać przez `cover_id`.

```yaml
alternate_covers:
  - id: limitowana
    label: "Limitowana"
    image: "/img/spz1-limitowana.jpg"
    alt: "Spółka ZŁO #1 – okładka limitowana"
    artist_name: "Kacper Wilk"
    person_slug: "kacper-wilk"
```

#### 3) Podglądy wnętrza
```yaml
previews:
  - image: "/img/spz1-page1.jpg"
    alt: "Spółka ZŁO #1 – strona 1"
    caption: "Strona 1"
```

#### 4) Twórcy
`creators` służy do scenariusza, rysunków, tłumaczenia itd. **Nie duplikujemy tutaj ról okładkowych** — autorów okładek wpisujemy w `primary_cover` albo `alternate_covers`.

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

#### 5) Wspólne parametry wydania
- `edition_specs:` — słownik dla faktów wspólnych dla całego wydania (np. liczba stron, wymiary).

```yaml
edition_specs:
  "Liczba stron": "24"
  "Wymiary": "170 x 240 mm"
```

#### 6) Produkty / warianty sprzedażowe
Zamiast dawnych `buy_links` + `variants` używamy jednego pola `products:`.
Każdy produkt to konkretna oferta sprzedażowa: format, opcjonalna okładka, cena, ISBN, limitacja i linki do sklepów.

```yaml
products:
  - format: zeszyt               # zeszyt | miekka | twarda | ebook
    cover_id: primary            # opcjonalne; domyślnie główna okładka
    label: "Standardowa"         # opcjonalne
    isbn13: "978..."
    ean2: "02"                   # opcjonalne, np. dla alternatywnej okładki
    price: "19,99 zł"
    limited: true                # opcjonalne
    numbered_copies: 333         # opcjonalne; tylko gdy limited=true
    specs:
      "Oprawa": "miękka ze skrzydełkami"
    buy_links:
      - label: "Strefa Komiksu"
        url: "https://..."
      - label: "Gildia"
        url: "https://..."
```

Ważne:
- `label` i `cover_id` są opcjonalne, ale pomagają przy kilku okładkach tego samego formatu.
- `numbered_copies` wpisujemy tylko wtedy, gdy egzemplarze są numerowane.
- `limited: true` można ustawić także bez `numbered_copies`.
- Nazwy sklepów w `buy_links[*].label` powinny być krótkie: `Strefa Komiksu`, `Gildia`, `Gov.pl` itd.

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
primary_cover:
  image: "/img/mama.jpg"
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
primary_cover:
  image: "/img/pisto1.jpg"
---
```

### Krok 2: Dodaj kolejne wydanie
Utwórz `content/projects/pisto/editions/02.md`:
```yaml
---
title: "Pisto #2"
release_date: 2025-08-01
primary_cover:
  image: "/img/pisto2.jpg"
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
