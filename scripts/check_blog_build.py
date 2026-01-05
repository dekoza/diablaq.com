from __future__ import annotations

import re
import sys
from pathlib import Path

from diablaq_site.builder import build_site


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    out_dir = root / "dist"

    build_site(root=root, out_dir=out_dir)

    expected = [
        out_dir / "blog" / "index.html",
        out_dir / "blog" / "testowy-wpis" / "index.html",
    ]

    missing = [p for p in expected if not p.exists()]
    if missing:
        print("MISSING:")
        for p in missing:
            print(f"- {p}")
        return 1

    html = (out_dir / "blog" / "index.html").read_text(encoding="utf-8")
    if "Testowy wpis" not in html:
        print("Blog index does not contain expected post title")
        return 2

    post_html = (out_dir / "blog" / "testowy-wpis" / "index.html").read_text(encoding="utf-8")
    m = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', post_html)
    if not m or m.group(1) != "/blog/testowy-wpis/":
        print("Bad canonical on blog post", m.group(1) if m else None)
        return 3

    print("ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

