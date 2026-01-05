# Jak edytować treści na stronie diablaq.com (dla osób nietechnicznych)

## TL;DR
- Treści edytujemy w `content/` (nie w `dist/`).
- Obrazki dodajemy do `img/` i linkujemy jako `/img/nazwa-pliku.jpg`.
- Wydania muszą mieć `release_date: YYYY-MM-DD`.
- `is_new: true` i `is_announcement: true` **nie mogą** być ustawione jednocześnie.
- Nazwy folderów/plików w `content/` są częścią adresu URL — nie zmieniaj ich bez konsultacji.

Ta strona jest generowana automatycznie z plików tekstowych (Markdown). Nie trzeba edytować HTML.

## Jak wygląda praca (workflow)
1. Zrób kopię repozytorium (fork) i sklonuj ją na komputer.
2. Utwórz nową gałąź (branch) do zmian.
3. Edytuj lub dodaj pliki treści (Markdown) w folderze `content/`.
4. Sprawdź podgląd lokalnie (opcjonalnie, jeśli masz środowisko uruchomieniowe).
5. Wypchnij zmiany i otwórz Pull Request.

> W Pull Requeście najlepiej opisać: co zostało dodane/zmienione oraz wkleić linki do wygenerowanych podstron (po deployu preview) lub screeny.

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
Jednotomówka nadal jest trzymana jako „projekt”, ale zwykle ma **tylko jedno wydanie** w folderze `editions/`:
- `content/projects/mama/editions/01.md`
- `content/projects/pzg/editions/01.md`

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
- `release_date` — **obowiązkowe**, format `YYYY-MM-DD` (np. `2025-06-01`)

### Pola bardzo często używane
- `release` (tekst, opcjonalne) — ludzki opis daty, np. `"premiera - grudzień 2024"`
- `is_new: true` — jeśli ma trafić na `/nowe/`
- `is_announcement: true` — jeśli ma trafić na `/zapowiedzi/`
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

## Checklist przed wysłaniem Pull Request
- Czy `release_date` jest w formacie `YYYY-MM-DD`?
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
