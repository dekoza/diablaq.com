SHELL := /bin/bash
.DEFAULT_GOAL := build
.PHONY: build serve push install help

VENV := .venv
PYTHON := python3
PIP := $(VENV)/bin/pip
BUILD_CMD := $(VENV)/bin/diablaq-build
DIST := dist
PORT := 8000

help:
	@echo "Dostępne polecenia:"
	@echo "  make            — Zbuduj stronę (domyślne)"
	@echo "  make serve      — Zbuduj i uruchom podgląd lokalny"
	@echo "  make push       — Wyślij zmiany na serwer"
	@echo "  make install    — Zainstaluj zależności (automatyczne przy budowaniu)"
	@echo "  make help       — Pokaż tę pomoc"

install: $(VENV)/pyvenv.cfg

$(VENV)/pyvenv.cfg:
	@echo "Tworzenie środowiska wirtualnego..."
	@python_version=$$($(PYTHON) -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")') && \
	required_version=3.11 && \
	if [ "$$(printf '%s\n' "$$required_version" "$$python_version" | sort -V | head -n1)" != "$$required_version" ]; then \
		echo "Błąd: Wymagany Python 3.11 lub nowszy, masz $$python_version"; \
		exit 1; \
	fi
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install .
	@echo "✓ Zależności zainstalowane."

build: $(VENV)/pyvenv.cfg
	$(BUILD_CMD) --out $(DIST)
	@echo "✓ Strona zbudowana w katalogu $(DIST)/"
	@echo "  Podgląd: make serve | Publikacja: make push"

serve: build
	@echo "Uruchamiam podgląd na http://localhost:$(PORT)"
	@echo "Aby zakończyć, naciśnij Ctrl+C"
	$(PYTHON) -m http.server $(PORT) --directory $(DIST)

.ONESHELL:
push:
	@set -e
	git add -A
	@if git diff --cached --quiet; then \
		echo "Brak zmian do wysłania."; \
		exit 0; \
	fi
	@if ! command -v gh &> /dev/null; then \
		echo "Błąd: Brak narzędzia gh CLI. Zainstaluj: https://cli.github.com/"; \
		exit 1; \
	fi
	@if ! gh auth status >/dev/null 2>&1; then \
		echo "Błąd: gh CLI nie jest uwierzytelnione. Uruchom: gh auth login"; \
		exit 1; \
	fi
	git commit -m "Aktualizacja strony: $$(date '+%Y-%m-%d %H:%M')"
	git push origin HEAD
	IS_FORK=$$(gh repo view --json isFork -q '.isFork')
	@if [ "$$IS_FORK" = "true" ]; then \
		echo "To jest fork. Tworzę pull request..."; \
		gh pr create --fill --base gh-pages; \
	else \
		echo "✓ Zmiany wysłane i opublikowane."; \
	fi
