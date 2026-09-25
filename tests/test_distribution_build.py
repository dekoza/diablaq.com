"""The Pages build must work from the installed distribution, not only the source tree."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_installed_wheel_builds_site(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    wheel_dir = tmp_path / "wheels"
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(wheel_dir), str(root)],
        check=True,
        capture_output=True,
        text=True,
    )
    (wheel,) = wheel_dir.glob("*.whl")
    out_dir = tmp_path / "dist"
    env = {**os.environ, "PYTHONPATH": str(wheel), "DIABLAQ_SITE_URL": "https://diablaq.com"}
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from diablaq_site.cli import main; main()",
            "--root",
            str(root),
            "--out",
            str(out_dir),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (out_dir / "index.html").is_file()
