SHELL := /bin/bash
.DEFAULT_GOAL := build
.PHONY: build serve push install help doctor check-python check-build-tools

.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c

VENV := .venv
INSTALL_STAMP := $(VENV)/.installed
PYTHON ?= python3
PIP := $(VENV)/bin/pip
BUILD_CMD := $(VENV)/bin/diablaq-build
DIST := dist
PORT := 8000
PACKAGE_SOURCES := $(wildcard diablaq_site/*.py)

detect-package-manager = \
	if command -v apt-get >/dev/null 2>&1; then echo apt; \
	elif command -v dnf >/dev/null 2>&1; then echo dnf; \
	elif command -v pacman >/dev/null 2>&1; then echo pacman; \
	elif command -v brew >/dev/null 2>&1; then echo brew; \
	else echo unknown; fi

print-system-deps = \
	case "$$package_manager" in \
		apt) \
			echo "Debian/Ubuntu:"; \
			echo "  sudo apt install build-essential python3-dev pkg-config libjpeg-dev zlib1g-dev"; \
			;; \
		dnf) \
			echo "Fedora/RHEL:"; \
			echo "  sudo dnf install gcc gcc-c++ make python3-devel pkgconf-pkg-config libjpeg-turbo-devel zlib-devel"; \
			;; \
		pacman) \
			echo "Arch:"; \
			echo "  sudo pacman -S base-devel python pkgconf libjpeg-turbo zlib"; \
			;; \
		brew) \
			echo "macOS (Homebrew):"; \
			echo "  xcode-select --install"; \
			echo "  brew install pkg-config jpeg-turbo"; \
			;; \
		*) \
			echo "Zainstaluj pakiety zapewniające: kompilator C, make, pkg-config, nagłówki Pythona, libjpeg i zlib."; \
			;; \
	esac

print-venv-deps = \
	case "$$package_manager" in \
		apt) \
			echo "Debian/Ubuntu:"; \
			echo "  sudo apt install python3-venv"; \
			;; \
		dnf) \
			echo "Fedora/RHEL:"; \
			echo "  sudo dnf install python3"; \
			;; \
		pacman) \
			echo "Arch:"; \
			echo "  sudo pacman -S python"; \
			;; \
		brew) \
			echo "macOS (Homebrew):"; \
			echo "  brew install python"; \
			;; \
		*) \
			echo "Zainstaluj pełny pakiet Python 3.11+ z obsługą środowisk wirtualnych (venv)."; \
			;; \
	esac

help:
	@echo "Dostępne polecenia:"
	@echo "  make            — Zbuduj stronę (domyślne)"
	@echo "  make serve      — Zbuduj i uruchom podgląd lokalny"
	@echo "  make push       — Wyślij zmiany na serwer"
	@echo "  make install    — Sprawdź wymagania systemowe i zainstaluj zależności"
	@echo "  make doctor     — Sprawdź, czy system jest gotowy do instalacji"
	@echo "  make help       — Pokaż tę pomoc"

doctor: check-python check-build-tools
	@echo "Sprawdzam wymagania systemowe..."
	@echo "✓ Podstawowe wymagania systemowe są dostępne."
	@echo "  Uwaga: ten test nie sprawdza wszystkich bibliotek natywnych wymaganych przez Pillow."

install: $(INSTALL_STAMP)

check-python:
	@if ! command -v "$(PYTHON)" >/dev/null 2>&1; then \
		echo "Błąd: Nie znaleziono interpretera $(PYTHON)."; \
		echo "Zainstaluj Python 3.11 lub nowszy i uruchom ponownie make install."; \
		exit 1; \
	fi
	@python_version=$$($(PYTHON) -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
	@if ! $(PYTHON) -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then \
		echo "Błąd: Wymagany Python 3.11 lub nowszy, masz $$python_version"; \
		exit 1; \
	fi
	@if ! $(PYTHON) -c "import venv" >/dev/null 2>&1; then \
		package_manager="$$($(detect-package-manager))"; \
		echo "Błąd: Python jest zainstalowany, ale brakuje modułu venv."; \
		echo "To zwykle oznacza brak pakietu systemowego dla środowisk wirtualnych."; \
		echo; \
		$(print-venv-deps); \
		exit 1; \
	fi

check-build-tools:
	@missing_tools=""
	@if ! command -v cc >/dev/null 2>&1 && ! command -v gcc >/dev/null 2>&1; then \
		missing_tools="$$missing_tools kompilator-C"; \
	fi
	@if ! command -v make >/dev/null 2>&1; then \
		missing_tools="$$missing_tools make"; \
	fi
	@if ! command -v pkg-config >/dev/null 2>&1; then \
		missing_tools="$$missing_tools pkg-config"; \
	fi
	@if [ -n "$$missing_tools" ]; then \
		package_manager="$$($(detect-package-manager))"; \
		echo "Błąd: Brakuje narzędzi systemowych potrzebnych do instalacji zależności."; \
		echo "Brakuje:$$missing_tools"; \
		echo "Najczęstsza przyczyna: brak kompilatora C, make albo pkg-config."; \
		echo; \
		$(print-system-deps); \
		exit 1; \
	fi

$(INSTALL_STAMP): pyproject.toml $(PACKAGE_SOURCES) | check-python check-build-tools
	@echo "Tworzenie środowiska wirtualnego..."
	@if ! $(PYTHON) -m venv $(VENV); then \
		echo "Błąd: Nie udało się utworzyć środowiska wirtualnego w $(VENV)."; \
		echo "Najpierw upewnij się, że Python ma moduł venv i że katalog roboczy jest zapisywalny."; \
		rm -f $(INSTALL_STAMP); \
		exit 1; \
	fi
	@if ! $(PIP) install --upgrade pip; then \
		echo "Błąd: Aktualizacja pip nie powiodła się."; \
		echo "Sprawdź połączenie z internetem oraz konfigurację Pythona/pip na tym systemie."; \
		rm -f $(INSTALL_STAMP); \
		exit 1; \
	fi
	@if ! $(PIP) install .; then \
		package_manager="$$($(detect-package-manager))"; \
		rm -f $(INSTALL_STAMP); \
		echo; \
		echo "Błąd: instalacja zależności Pythona nie powiodła się."; \
		echo "Najczęstsze przyczyny:"; \
		echo "- brak python3-venv,"; \
		echo "- brak narzędzi budujących,"; \
		echo "- brak bibliotek systemowych dla Pillow."; \
		echo; \
		$(print-system-deps); \
		echo; \
		echo "Po instalacji pakietów systemowych uruchom ponownie: make install"; \
		exit 1; \
	fi
	@touch $(INSTALL_STAMP)
	@echo "✓ Zależności zainstalowane."

build: $(INSTALL_STAMP)
	@if ! $(BUILD_CMD) --out $(DIST); then \
		echo; \
		echo "Błąd: Generator strony zakończył się niepowodzeniem."; \
		echo "Jeśli problem dotyczy brakujących zależności systemowych, uruchom: make install"; \
		echo "Jeśli zależności są już zainstalowane, sprawdź treści i szablony wejściowe."; \
		exit 1; \
	fi
	@echo "✓ Strona zbudowana w katalogu $(DIST)/"
	@echo "  Podgląd: make serve | Publikacja: make push"

serve: build
	@echo "Uruchamiam podgląd na http://localhost:$(PORT)"
	@echo "Aby zakończyć, naciśnij Ctrl+C"
	$(PYTHON) -m http.server $(PORT) --directory $(DIST)
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
