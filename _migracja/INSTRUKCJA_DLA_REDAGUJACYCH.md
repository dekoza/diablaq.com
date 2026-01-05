# Jak edytować treści na stronie diablaq.com (dla osób nietechnicznych)

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
- `content/projects/<projekt>/editions/` — wydania/numeracja (np. BZIK #5)
- `content/people/` — profile osób ("Ludzie")

> Uwaga: nazwy folderów i plików są częścią adresu strony (URL), więc nie zmieniaj ich bez konsultacji.

---

## Format plików (Markdown + nagłówek YAML)
Każdy plik ma:
1) nagłówek (YAML) między `---` i `---`  
2) treść w Markdown poniżej.

Przykład (schemat):
- Na górze: tytuł, data premiery, ISBN, okładka, link do sklepu itp.
- Poniżej: opis (zwykły tekst, listy, pogrubienia).

### Najczęściej edytowane pola (wydanie/numer)
- `title` — tytuł / nazwa wydania
- `release` — np. "czerwiec 2025"
- `covers` — okładki (plik w `img/`)
- `creators` — twórcy
- `specs` — parametry: strony, format, cena, ISBN
- `buy_links` — linki do sklepu

### Nowości i zapowiedzi
Pozycje mogą być oznaczone do listingów:
- `is_new: true` → trafia na `/nowe/` (Nowości)
- `is_announcement: true` → trafia na `/zapowiedzi/` (Zapowiedzi)
- opcjonalnie: `presale_url` → link do przedsprzedaży

---

## Dodanie nowego wydania (krok po kroku)
1. Znajdź projekt/seri ę, np. `content/projects/spz/`.
2. Wejdź do `editions/`.
3. Skopiuj istniejący plik wydania i zmień:
   - nazwę pliku (np. `02.md` → `03.md`)
   - pola w nagłówku YAML
   - opis w Markdown
4. Dodaj okładkę do `img/` (jeśli to nowy plik) i wpisz ścieżkę w `covers`.
5. Jeśli to zapowiedź, ustaw `is_announcement: true`. Jeśli nowość, `is_new: true`.

---

## Czego nie robić
- Nie edytuj plików w `dist/` (jeśli istnieje) — to katalog generowany.
- Nie zmieniaj masowo nazw folderów/plików w `content/` (to zmienia adresy URL).
- Nie wklejaj dużych bloków HTML do treści — używaj Markdown.

---

## Pytania / pomoc
Jeśli nie masz pewności, jak coś dodać (np. nowy typ treści, nietypowa okładka, wiele wariantów okładki), dopisz komentarz w Pull Requeście: „Pytanie do maintainerów” i opisz, czego potrzebujesz.

