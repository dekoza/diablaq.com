# diablaq.com

Repozytorium strony wydawnictwa Diablaq.

## Edycja treści (dla nietechnicznych)
Zobacz: `_migracja/INSTRUKCJA_DLA_REDAGUJACYCH.md`.

## Skoroszyt do szybkiego uzupełniania stron projektów i wydań
Jeśli trzeba szybko uzupełnić wiele pustych albo zbyt krótkich opisów w `content/projects/*/project.md` i `content/projects/*/editions/*.md`, użyj skoroszytu roboczego.
To wygodniejsza metoda niż otwieranie kilkudziesięciu plików osobno.

### Eksport skoroszytu
```bash
uv run diablaq-project-workbook export
```

Polecenie tworzy plik `project-page-workbook.md` w katalogu głównym repozytorium.
Domyślnie trafiają tam tylko projekty, które same mają braki albo zawierają wydania wymagające uzupełnienia.

Aby uwzględnić wszystkie projekty i wszystkie istniejące wydania:
```bash
uv run diablaq-project-workbook export --all
```

### Uzupełnianie treści
Otwórz `project-page-workbook.md` i edytuj tylko bloki między markerami:
- `<!-- FRONTMATTER START: ... -->` / `<!-- FRONTMATTER END: ... -->`
- `<!-- BODY START: ... -->` / `<!-- BODY END: ... -->`
- `<!-- EDITION FRONTMATTER START: projekt/slug-wydania -->` / `<!-- EDITION FRONTMATTER END: projekt/slug-wydania -->`
- `<!-- EDITION BODY START: projekt/slug-wydania -->` / `<!-- EDITION BODY END: projekt/slug-wydania -->`

Każda sekcja jest już wypełniona szkieletem pól:
- pola opcjonalne są zakomentowane,
- przy polach z krótką listą dozwolonych wartości pojawiają się podpowiedzi (`line`, `kind`, `binding`, `true | false` itd.),
- sekcja projektu zawiera też pomocnicze informacje z istniejących plików wydań.

Aby dodać nowe wydanie:
1. znajdź sekcję `Szablon nowego wydania`,
2. skopiuj oba bloki z identyfikatorem `__new_edition__`,
3. zmień identyfikator w obu markerach na docelowy slug, np. `bzik/09` albo `mama/index`,
4. dopiero potem uzupełnij frontmatter i opis.

### Import zmian z powrotem do plików treści
```bash
uv run diablaq-project-workbook import
```

Import jest celowo rygorystyczny:
- parsuje wyłącznie bloki między markerami; cała reszta skoroszytu jest ignorowana,
- błędny YAML/frontmatter w dowolnym projekcie albo wydaniu zatrzyma import przed zapisem zmian,
- zapisuje tylko `content/projects/<slug>/project.md` i `content/projects/<slug>/editions/<edition>.md`,
- może utworzyć brakujący plik wydania, ale tylko wewnątrz istniejącego katalogu projektu,
- nie tworzy nowych katalogów projektów,
- niezmienione sekcje i nietknięte szablony `__new_edition__` są pomijane,
- jeśli zmienisz treść szablonu `__new_edition__`, ale nie zmienisz jego identyfikatora, import zakończy się błędem.

### Podgląd efektu
```bash
uv run diablaq-build
```

## Blog
Wpisy są w `content/blog/` (Markdown + frontmatter YAML).
- Listing: `/blog/`
- Wpis: `/blog/<slug>/`

## Generator strony
Strona jest generowana statycznie z treści w Markdown (folder `content/`) i szablonów Jinja (folder `templates/`).

### Szybki start (lokalnie)
```bash
make install
make build
```

`make install` sprawdza wymagania systemowe, tworzy `.venv` i instaluje zależności projektu.
`make build` uruchamia generator już z przygotowanego środowiska.
Jeśli chcesz sprawdzić sam system bez instalacji, uruchom `make doctor`.
To jest tylko wstępny test: potwierdza Pythona i podstawowe narzędzia, ale nie gwarantuje obecności wszystkich bibliotek natywnych potrzebnych przez `Pillow`.

### Wymagania systemowe
Najwygodniej uruchamiać projekt na systemie z Pythonem 3.11+ oraz obsługą `venv`.

Jeśli `make install` albo `make build` kończy się błędem instalacji zależności, najczęściej brakuje pakietów systemowych potrzebnych do utworzenia środowiska i instalacji `Pillow`.

Debian/Ubuntu:
```bash
sudo apt install python3-venv build-essential python3-dev pkg-config libjpeg-dev zlib1g-dev
```

Fedora/RHEL:
```bash
sudo dnf install gcc gcc-c++ make python3-devel pkgconf-pkg-config libjpeg-turbo-devel zlib-devel
```

Arch:
```bash
sudo pacman -S python base-devel pkgconf libjpeg-turbo zlib
```

macOS (Homebrew):
```bash
xcode-select --install
brew install python pkg-config jpeg-turbo
```

Potem uruchom ponownie:
```bash
make install
make build
```

## Deployment (GitHub Pages)
Publikujemy wyłącznie katalog `dist/` (generator). Foldery `_migracja/` i `_penpot/` zostają w repo, ale nie są częścią publikowanej strony.

Instrukcja: `_migracja/DEPLOY_GITHUB_PAGES.md`.
