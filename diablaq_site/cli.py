from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(prog="diablaq-build")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Katalog repo (domyślnie: bieżący).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Katalog wynikowy (domyślnie: <root>/dist).",
    )
    args = parser.parse_args()

    root: Path = args.root.resolve()
    out_dir = (args.out or (root / "dist")).resolve()

    from diablaq_site.builder import build_site

    try:
        build_site(root=root, out_dir=out_dir)
    except ValueError as exc:
        print(f"Błąd treści wejściowych: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
