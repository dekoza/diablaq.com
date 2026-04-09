"""Regression tests for Makefile diagnostics."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path


def _write_fake_python(script_path: Path, *, has_venv: bool) -> None:
    script_path.write_text(
        textwrap.dedent(
            f"""\
            #!{sys.executable}
            import sys

            args = sys.argv[1:]

            if args[:2] == ["-c", 'import sys; print(f"{{sys.version_info.major}}.{{sys.version_info.minor}}")']:
                print("3.11")
                raise SystemExit(0)

            if args[:2] == ["-c", "import venv"]:
                raise SystemExit(0 if {str(has_venv)} else 1)

            if args[:2] == ["-m", "venv"]:
                raise SystemExit(0 if {str(has_venv)} else 1)

            raise SystemExit(0)
            """
        ),
        encoding="utf-8",
    )
    script_path.chmod(0o755)


def _run_make(
    repo_root: Path, workdir: Path, target: str, *, env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    make_bin = shutil.which("make")
    assert make_bin is not None, "make must be available to run Makefile tests"

    return subprocess.run(
        [make_bin, "-f", str(repo_root / "Makefile"), target],
        cwd=workdir,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def _write_minimal_project_files(workdir: Path) -> None:
    (workdir / "pyproject.toml").write_text(
        "[project]\nname='demo'\nversion='0.1.0'\n", encoding="utf-8"
    )
    package_dir = workdir / "diablaq_site"
    package_dir.mkdir(exist_ok=True)
    (package_dir / "cli.py").write_text("def main():\n    return 0\n", encoding="utf-8")


def _write_successful_fake_python(script_path: Path, log_path: Path) -> None:
    script_path.write_text(
        textwrap.dedent(
            f"""\
            #!{sys.executable}
            import sys
            from pathlib import Path

            log_path = Path({str(log_path)!r})
            args = sys.argv[1:]

            if args[:2] == ["-c", 'import sys; print(f"{{sys.version_info.major}}.{{sys.version_info.minor}}")']:
                print("3.11")
                raise SystemExit(0)

            if args[:2] == ["-c", "import venv"]:
                raise SystemExit(0)

            if args[:2] == ["-m", "venv"]:
                target = Path(args[2])
                (target / "bin").mkdir(parents=True, exist_ok=True)
                (target / "pyvenv.cfg").write_text("home = /tmp\\n", encoding="utf-8")
                pip_script = target / "bin" / "pip"
                pip_script.write_text(
                    "#!/bin/sh\\n"
                    f"echo pip >> {str(log_path)!r}\\n"
                    "exit 0\\n",
                    encoding="utf-8",
                )
                pip_script.chmod(0o755)
                build_script = target / "bin" / "diablaq-build"
                build_script.write_text("#!/bin/sh\\nexit 0\\n", encoding="utf-8")
                build_script.chmod(0o755)
                raise SystemExit(0)

            raise SystemExit(0)
            """
        ),
        encoding="utf-8",
    )
    script_path.chmod(0o755)


def _write_failing_venv_python(script_path: Path, log_path: Path) -> None:
    script_path.write_text(
        textwrap.dedent(
            f"""\
            #!{sys.executable}
            import sys
            from pathlib import Path

            log_path = Path({str(log_path)!r})
            args = sys.argv[1:]

            if args[:2] == ["-c", 'import sys; print(f"{{sys.version_info.major}}.{{sys.version_info.minor}}")']:
                print("3.11")
                raise SystemExit(0)

            if args[:2] == ["-c", "import venv"]:
                raise SystemExit(0)

            if args[:2] == ["-m", "venv"]:
                target = Path(args[2])
                (target / "bin").mkdir(parents=True, exist_ok=True)
                (target / "pyvenv.cfg").write_text("home = /tmp\\n", encoding="utf-8")
                pip_script = target / "bin" / "pip"
                pip_lines = [
                    "#!/bin/sh",
                    f"echo pip >> {str(log_path)!r}",
                    'if [ "$1" = "install" ] && [ "$2" = "." ]; then exit 1; fi',
                    "exit 0",
                ]
                pip_script.write_text("\\n".join(pip_lines) + "\\n", encoding="utf-8")
                pip_script.chmod(0o755)
                build_script = target / "bin" / "diablaq-build"
                build_script.write_text("#!/bin/sh\\nexit 0\\n", encoding="utf-8")
                build_script.chmod(0o755)
                raise SystemExit(0)

            raise SystemExit(0)
            """
        ),
        encoding="utf-8",
    )
    script_path.chmod(0o755)


def test_install_reports_missing_python_venv_dependency(repo_root: Path, tmp_path: Path) -> None:
    _write_minimal_project_files(tmp_path)
    fake_python = tmp_path / "fake-python"
    _write_fake_python(fake_python, has_venv=False)

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    (fake_bin / "apt-get").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    (fake_bin / "apt-get").chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = str(fake_bin)
    env["PYTHON"] = str(fake_python)

    result = _run_make(repo_root, tmp_path, "install", env=env)
    output = result.stdout + result.stderr

    assert result.returncode != 0
    assert "Błąd: Python jest zainstalowany, ale brakuje modułu venv." in output
    assert "sudo apt install python3-venv" in output


def test_install_reports_missing_system_build_tools(repo_root: Path, tmp_path: Path) -> None:
    _write_minimal_project_files(tmp_path)
    fake_python = tmp_path / "fake-python"
    _write_fake_python(fake_python, has_venv=True)

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    (fake_bin / "apt-get").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    (fake_bin / "apt-get").chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = str(fake_bin)
    env["PYTHON"] = str(fake_python)

    result = _run_make(repo_root, tmp_path, "install", env=env)
    output = result.stdout + result.stderr

    assert result.returncode != 0
    assert "Błąd: Brakuje narzędzi systemowych potrzebnych do instalacji zależności." in output
    assert (
        "sudo apt install build-essential python3-dev pkg-config libjpeg-dev zlib1g-dev" in output
    )


def test_build_reports_generator_failure_with_guidance(repo_root: Path, tmp_path: Path) -> None:
    _write_minimal_project_files(tmp_path)
    venv_bin = tmp_path / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    (tmp_path / ".venv" / "pyvenv.cfg").write_text("home = /tmp\n", encoding="utf-8")
    (tmp_path / ".venv" / ".installed").write_text("ok\n", encoding="utf-8")

    build_script = venv_bin / "diablaq-build"
    build_script.write_text("#!/bin/sh\necho 'boom' >&2\nexit 2\n", encoding="utf-8")
    build_script.chmod(0o755)

    result = _run_make(repo_root, tmp_path, "build", env=os.environ.copy())
    output = result.stdout + result.stderr

    assert result.returncode != 0
    assert "Błąd: Generator strony zakończył się niepowodzeniem." in output
    assert (
        "Jeśli problem dotyczy brakujących zależności systemowych, uruchom: make install" in output
    )


def test_install_does_not_leave_success_stamp_after_failed_pip_install(
    repo_root: Path, tmp_path: Path
) -> None:
    _write_minimal_project_files(tmp_path)
    log_path = tmp_path / "pip.log"
    fake_python = tmp_path / "fake-python"
    _write_failing_venv_python(fake_python, log_path)

    env = os.environ.copy()
    env["PYTHON"] = str(fake_python)

    result = _run_make(repo_root, tmp_path, "install", env=env)
    output = result.stdout + result.stderr

    assert result.returncode != 0
    assert "Błąd: instalacja zależności Pythona nie powiodła się." in output
    assert not (tmp_path / ".venv" / ".installed").exists()


def test_build_skips_reinstall_when_install_stamp_exists(repo_root: Path, tmp_path: Path) -> None:
    _write_minimal_project_files(tmp_path)
    log_path = tmp_path / "pip.log"
    fake_python = tmp_path / "fake-python"
    _write_successful_fake_python(fake_python, log_path)

    env = os.environ.copy()
    env["PYTHON"] = str(fake_python)

    install_result = _run_make(repo_root, tmp_path, "install", env=env)
    assert install_result.returncode == 0
    assert (tmp_path / ".venv" / ".installed").exists()
    assert log_path.read_text(encoding="utf-8").count("pip") == 2

    build_result = _run_make(repo_root, tmp_path, "build", env=env)

    assert build_result.returncode == 0
    assert log_path.read_text(encoding="utf-8").count("pip") == 2


def test_doctor_reports_success_when_requirements_are_available(
    repo_root: Path, tmp_path: Path
) -> None:
    _write_minimal_project_files(tmp_path)
    log_path = tmp_path / "pip.log"
    fake_python = tmp_path / "fake-python"
    _write_successful_fake_python(fake_python, log_path)

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    for tool_name in ("cc", "make", "pkg-config", "apt-get"):
        tool_path = fake_bin / tool_name
        tool_path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        tool_path.chmod(0o755)

    env = os.environ.copy()
    env["PYTHON"] = str(fake_python)
    env["PATH"] = f"{fake_bin}:{env['PATH']}"

    result = _run_make(repo_root, tmp_path, "doctor", env=env)
    output = result.stdout + result.stderr

    assert result.returncode == 0
    assert "Sprawdzam wymagania systemowe..." in output
    assert "✓ Podstawowe wymagania systemowe są dostępne." in output


def test_build_reinstalls_when_generator_source_changes(repo_root: Path, tmp_path: Path) -> None:
    log_path = tmp_path / "pip.log"
    fake_python = tmp_path / "fake-python"
    _write_successful_fake_python(fake_python, log_path)

    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='demo'\nversion='0.1.0'\n", encoding="utf-8"
    )
    package_dir = tmp_path / "diablaq_site"
    package_dir.mkdir()
    source_file = package_dir / "cli.py"
    source_file.write_text("print('v1')\n", encoding="utf-8")

    env = os.environ.copy()
    env["PYTHON"] = str(fake_python)

    install_result = _run_make(repo_root, tmp_path, "install", env=env)
    assert install_result.returncode == 0
    assert log_path.read_text(encoding="utf-8").count("pip") == 2

    source_file.write_text("print('v2')\n", encoding="utf-8")

    build_result = _run_make(repo_root, tmp_path, "build", env=env)

    assert build_result.returncode == 0
    assert log_path.read_text(encoding="utf-8").count("pip") == 4
