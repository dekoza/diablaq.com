from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Check:
    name: str
    path: Path
    needles: list[str]


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    dist = repo / "dist"

    # SPZ #2 (kanonicznie pod /publikacje/)
    spz2 = dist / "publikacje" / "spz" / "02" / "index.html"

    checks = [
        Check(
            name="SPZ #2 edition page",
            path=spz2,
            needles=[
                "Parametry",
                "Gdzie kupić",
                "Strefa Komiksu",
                "Przedsprzedaż",
            ],
        ),
        Check(
            name="BZIK #5 edition page",
            path=dist / "mecenat" / "bzik" / "05" / "index.html",
            needles=[
                "Parametry",
                "Gdzie kupić",
                "Strefa Komiksu",
            ],
        ),
    ]

    ok = True
    for c in checks:
        check_ok = True

        if not c.path.exists():
            print(f"FAIL {c.name}: missing file {c.path}")
            ok = False
            continue

        html = c.path.read_text(encoding="utf-8")
        for needle in c.needles:
            if needle not in html:
                print(f"FAIL {c.name}: missing {needle!r}")
                ok = False
                check_ok = False

        if check_ok:
            print(f"OK {c.name}")

    if ok:
        print("ALL OK")

    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
