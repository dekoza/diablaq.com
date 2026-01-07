# Plan wdrożenia bloga w generatorze diablaq.com (Python + Jinja + Markdown)

Cel bloga: krótkie aktualności wydawnictwa (targi, zapowiedzi live, relacje), z możliwością dodawania obrazków, linków i formatowania.

## 1) IA / URL-e (wariant zgodny z resztą strony)
Proponuję:
- `/blog/` — listing wpisów (od najnowszych)
- `/blog/<slug>/` — pojedynczy wpis
- (opcjonalnie) `/blog/tag/<tag>/` — listing po tagu

Dodatkowo (opcjonalnie, ale warto):
- `/blog/rss.xml` — RSS

## 2) Struktura treści
Nowy katalog:
- `content/blog/` — wpisy Markdown (jeden plik = jeden wpis)

Konwencja nazw plików:
- `YYYY-MM-DD-slug.md` (czytelnie i naturalnie sortuje się po nazwie)

Przykład:
- `content/blog/2026-02-01-targi-w-lodzi.md`

Obrazki:
- na start trzymamy w `img/` (jak reszta strony)
- w Markdown wstawiamy zwykłe obrazki: `![](/img/nazwa.jpg)`
- (opcjonalnie później) dedykowane `img/blog/<slug>/...`

## 3) Kontrakt danych (frontmatter YAML)
Minimalne wymagane pola:
- `title` (str)
- `date` (YYYY-MM-DD; można wykorzystać istniejący parser dat)

Zalecane:
- `summary` (str) — krótki opis do listingu
- `cover_image` (str) — miniatura do listingu
- `tags` (list[str])
- `draft` (bool) — jeśli `true`, wpis nie pojawia się w buildzie

Przykład wpisu:

```yaml
---
title: "Będziemy na Targach Komiksu w Łodzi"
date: 2026-02-01
summary: "Wpadnijcie do nas na stoisko — podpisy i nowości na miejscu."
cover_image: "/img/targi-lodz-2026.jpg"
tags:
  - targi
  - wydarzenia
---

Treść w Markdown…
```

## 4) Zmiany w generatorze (backend)
Minimalny zakres prac w `diablaq_site/builder.py`:
1. Dodać model `BlogPost` (dataclass), analogicznie do `Page`.
2. Wczytać `content/blog/*.md`.
3. Parsować datę (`date`) i generować:
   - kanoniczny URL `/blog/<slug>/`
   - listing `/blog/` (sortowanie malejąco po dacie)
4. (Opcjonalnie) obsłużyć `draft: true` — pomijamy wpis.
5. Dodać canonicale dla bloga (`canonical_url=/blog/...`).

## 5) Szablony
Nowe template:
- `templates/blog_index.html` — listing (layout analogiczny do listingów)
- `templates/blog_post.html` — pojedynczy wpis

Nowe partiale (opcjonalnie):
- `_partials/blog_card.html` — kafelek wpisu na listingu

Wpis powinien renderować:
- tytuł
- datę
- (opcjonalnie) okładkę
- treść HTML z Markdown
- (opcjonalnie) tagi jako linki

## 6) CSS
- wykorzystać istniejące wzorce (`page-header`, `tiles`, `project-card`), żeby blog pasował wizualnie
- dodać lekkie style dla treści artykułu (np. szerokość tekstu, odstępy)

## 7) UX i nawigacja
- dodać link „Blog” w stopce (i opcjonalnie w menu desktop, jeśli chcesz)
- na stronie głównej można dodać sekcję „Aktualności” z 2–3 ostatnimi wpisami (opcjonalnie)

## 8) Dodatki (opcjonalnie, ale rekomendowane)
- RSS (`/blog/rss.xml`)
- sitemap (`/sitemap.xml`) — później, razem z SEO
- tagi + archiwum

## 9) Kryteria akceptacji
- `content/blog/*.md` generuje strony w `dist/blog/<slug>/`
- `/blog/` pokazuje listę wpisów w kolejności od najnowszego
- canonicale są ustawione poprawnie
- build i obecne walidacje przechodzą

