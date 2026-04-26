# diablaq.com

Repozytorium strony wydawnictwa Diablaq.

## Edycja treści (dla nietechnicznych)
Zobacz: `_migracja/INSTRUKCJA_DLA_REDAGUJACYCH.md`.

## Skoroszyt do szybkiego uzupełniania stron projektów
Jeśli trzeba szybko uzupełnić wiele pustych albo zbyt krótkich opisów w `content/projects/*/project.md`, użyj skoroszytu roboczego.
To wygodniejsza metoda niż otwieranie kilkudziesięciu plików osobno.

### Eksport skoroszytu
```bash
uv run diablaq-project-workbook export
```

Polecenie tworzy plik `project-page-workbook.md` w katalogu głównym repozytorium.
Domyślnie trafiają tam tylko projekty, które nadal wymagają uzupełnienia.

Aby uwzględnić wszystkie strony projektów:
```bash
uv run diablaq-project-workbook export --all
```

### Uzupełnianie treści
Otwórz `project-page-workbook.md` i edytuj tylko bloki między markerami:
- `<!-- FRONTMATTER START: ... -->` / `<!-- FRONTMATTER END: ... -->`
- `<!-- BODY START: ... -->` / `<!-- BODY END: ... -->`

Każda sekcja projektu zawiera już:
- ścieżkę do pliku,
- podsumowanie braków,
- obecne wartości `title`, `line`, `summary`, `cover_image`,
- pomocnicze informacje z plików wydań.

### Import zmian z powrotem do plików projektu
```bash
uv run diablaq-project-workbook import
```

Import jest celowo rygorystyczny:
- błędny YAML/frontmatter zatrzyma import przed zapisem zmian,
- niezmienione szablonowe sekcje są ignorowane,
- projekty bez zmian są pomijane.

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
