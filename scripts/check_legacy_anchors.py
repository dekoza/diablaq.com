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

    checks = [
        Check(
            name="BZIK landing",
            path=dist / "bzik" / "index.html",
            needles=[
                'id="bzik5"',
                "/mecenat/bzik/05/",
            ],
        ),
        Check(
            name="SPZ landing",
            path=dist / "spolka-zlo" / "index.html",
            needles=[
                'id="spz2"',
                "/spolka-zlo/02/",
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
