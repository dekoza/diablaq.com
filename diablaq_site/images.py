"""Image processing utilities for cover aspect detection and thumbnail generation."""

from pathlib import Path

from PIL import Image


def get_cover_aspect_class(cover_path: str | None, root: Path) -> str:
    """Zwraca klasę CSS na podstawie proporcji okładki.

    - cover--tall: ratio < 0.6 (wysoka okładka) -> object-position: top
    - cover--wide: ratio > 0.75 (szeroka okładka) -> object-fit: contain
    - cover--standard: pozostałe -> object-position: center
    """
    if not cover_path:
        return "cover--standard"

    # Usuń leading slash i znajdź plik
    relative_path = cover_path.lstrip("/")
    full_path = root / relative_path

    if not full_path.exists():
        return "cover--standard"

    try:
        with Image.open(full_path) as img:
            ratio = img.width / img.height
            if ratio > 0.75:
                return "cover--wide"
            elif ratio < 0.6:
                return "cover--tall"
            return "cover--standard"
    except Exception:
        return "cover--standard"


def generate_thumbnail(src: Path, dst: Path, size: tuple[int, int] = (300, 300)) -> None:
    """Generuje miniaturę zdjęcia o podanym rozmiarze (domyślnie 300x300)."""
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as img:
        # Konwersja do RGB jeśli potrzeba (np. dla RGBA/PNG)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        # Thumbnail zachowuje proporcje i mieści się in podanym rozmiarze
        img.thumbnail(size, Image.Resampling.LANCZOS)
        img.save(dst, "JPEG", quality=85, optimize=True)


def thumb_path_from_photo(photo_path: str) -> str:
    """Generuje ścieżkę do miniatury na podstawie ścieżki do zdjęcia."""
    p = Path(photo_path)
    return str(p.parent / f"{p.stem}_thumb.jpg")
