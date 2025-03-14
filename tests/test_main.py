from __future__ import annotations

import functools
import os
import shlex
import shutil
import subprocess
from pathlib import Path

import pkginfo

TEST_DIR = Path(__file__).parent
ROOT_DIR = TEST_DIR.parent
testing_assets = TEST_DIR / "assets"
plugin_source_dir = ROOT_DIR / "poetry_plugin_version"


def copy_assets(source_name: str, testing_dir: Path) -> None:
    package_path = testing_assets / source_name
    shutil.copytree(package_path, testing_dir)


def run_by_subprocess(cmd: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        shlex.split(cmd),
        cwd=cwd,
        capture_output=True,
        encoding="utf-8",
    )


def build_package(
    testing_dir: Path, command: str = "poetry build"
) -> subprocess.CompletedProcess[str]:
    cmd = f"coverage run --source {plugin_source_dir} --parallel-mode -m {command}"
    result = run_by_subprocess(cmd, cwd=testing_dir)
    coverage_path = list(testing_dir.glob(".coverage*"))[0]
    dst_coverage_path = ROOT_DIR / coverage_path.name
    shutil.copy(coverage_path, dst_coverage_path)
    return result


def test_defaults(tmp_path: Path) -> None:
    testing_dir = tmp_path / "testing_package"
    copy_assets("no_packages", testing_dir)
    result = build_package(testing_dir=testing_dir)
    assert (
        "poetry-plugin-version: Using __init__.py file at "
        "test_custom_version/__init__.py for dynamic version" in result.stdout
    )
    assert (
        "poetry-plugin-version: Setting package dynamic version to __version__ "
        "variable from __init__.py: 0.0.1" in result.stdout
    )
    assert "Built test_custom_version-0.0.1-py3-none-any.whl" in result.stdout
    wheel_path = testing_dir / "dist" / "test_custom_version-0.0.1-py3-none-any.whl"
    info = pkginfo.get_metadata(str(wheel_path))
    assert info and info.version == "0.0.1"


class TestVersionDotPy:
    asset_dir = "version_dot_py"
    version_file = "version.py"

    def test_custom_version_file(self, tmp_path: Path) -> None:
        testing_dir = tmp_path / "testing_package"
        copy_assets(self.asset_dir, testing_dir)
        result = build_package(testing_dir=testing_dir)
        assert (
            f"poetry-plugin-version: Using {self.version_file} file at "
            "test_custom_version/version.py for dynamic version" in result.stdout
        )
        assert (
            "poetry-plugin-version: Setting package dynamic version to __version__ "
            f"variable from {self.version_file}: 0.0.8" in result.stdout
        )
        assert "Building test-custom-version (0.0.8)" in result.stdout
        wheel_path = testing_dir / "dist" / "test_custom_version-0.0.8-py3-none-any.whl"
        info = pkginfo.get_metadata(str(wheel_path))
        assert info and info.version == "0.0.8"


class TestWithDirname(TestVersionDotPy):
    asset_dir = "with_dirname"
    version_file = "test_custom_version/version.py"


class TestPdmStyle(TestVersionDotPy):
    asset_dir = "pdm_style"
    version_file = "test_custom_version/version.py"


def test_custom_packages(tmp_path: Path) -> None:
    if os.getenv("PPV_HOME_TMP"):
        (tmp_path := Path.home() / "tmp2").mkdir()
    testing_dir = tmp_path / "testing_package"
    copy_assets("custom_packages", testing_dir)
    result = build_package(testing_dir=testing_dir)
    assert (
        "poetry-plugin-version: Using __init__.py file at custom_package/__init__.py "
        "for dynamic version" in result.stdout
    )
    assert (
        "poetry-plugin-version: Setting package dynamic version to __version__ "
        "variable from __init__.py: 0.0.2" in result.stdout
    )
    assert "Building test-custom-version (0.0.2)" in result.stdout
    wheel_path = testing_dir / "dist" / "test_custom_version-0.0.2-py3-none-any.whl"
    info = pkginfo.get_metadata(str(wheel_path))
    assert info and info.version == "0.0.2"


def test_variations(tmp_path: Path) -> None:
    testing_dir = tmp_path / "testing_package"
    copy_assets("variations", testing_dir)
    result = build_package(testing_dir=testing_dir)
    assert (
        "poetry-plugin-version: Using __init__.py file at "
        "test_custom_version/__init__.py for dynamic version" in result.stdout
    )
    assert (
        "poetry-plugin-version: Setting package dynamic version to __version__ "
        "variable from __init__.py: 0.0.3" in result.stdout
    )
    assert "Built test_custom_version-0.0.3-py3-none-any.whl" in result.stdout
    wheel_path = testing_dir / "dist" / "test_custom_version-0.0.3-py3-none-any.whl"
    info = pkginfo.get_metadata(str(wheel_path))
    assert info and info.version == "0.0.3"


def test_no_version_var(tmp_path: Path) -> None:
    testing_dir = tmp_path / "testing_package"
    copy_assets("no_version_var", testing_dir)
    result = build_package(testing_dir=testing_dir)
    assert (
        "poetry-plugin-version: No valid __version__ variable found in __init__.py, "
        "cannot extract dynamic version" in result.stderr
    )
    assert result.returncode != 0


def test_no_standard_dir(tmp_path: Path) -> None:
    testing_dir = tmp_path / "testing_package"
    copy_assets("no_standard_dir", testing_dir)
    result = build_package(testing_dir=testing_dir)
    assert "poetry-plugin-version: __init__.py file not found at" in result.stderr
    assert result.returncode != 0


def test_multiple_packages(tmp_path: Path) -> None:
    testing_dir = tmp_path / "testing_package"
    copy_assets("multiple_packages", testing_dir)
    result = build_package(testing_dir=testing_dir)
    assert (
        "poetry-plugin-version: More than one package set, cannot extract "
        "dynamic version" in result.stderr
    )
    assert result.returncode != 0


def test_no_config(tmp_path: Path) -> None:
    testing_dir = tmp_path / "testing_package"
    copy_assets("no_config", testing_dir)
    result = build_package(testing_dir=testing_dir)
    assert "Built test_custom_version-0-py3-none-any.whl" in result.stdout
    assert result.returncode == 0


def test_no_config_source(tmp_path: Path) -> None:
    testing_dir = tmp_path / "testing_package"
    copy_assets("no_config_source", testing_dir)
    result = build_package(testing_dir=testing_dir)
    assert (
        "poetry-plugin-version: No source configuration found in "
        "[tool.poetry-plugin-version] in pyproject.toml, not extracting dynamic version"
    ) in result.stderr
    assert result.returncode != 0


def test_build_system(tmp_path: Path) -> None:
    testing_dir = tmp_path / "testing_package"
    copy_assets("build_system", testing_dir)
    result = build_package(testing_dir=testing_dir)
    assert "Building test-custom-version (0.0.8)" in result.stdout
    assert result.returncode == 0


def test_poetry_v2(tmp_path: Path) -> None:
    testing_dir = tmp_path / "testing_package"
    copy_assets("poetry_v2", testing_dir)
    result = build_package(testing_dir=testing_dir)
    assert "Building test-custom-version (0.0.8)" in result.stdout
    assert result.returncode == 0


def test_poetry_v2_api(tmp_path: Path) -> None:
    testing_dir = tmp_path / "testing_package"
    copy_assets("poetry_v2_api", testing_dir)
    result = build_package(testing_dir, command="pip install -e .")
    assert "Successfully installed test-custom-version-0.0.8" in result.stdout
    assert result.returncode == 0


def test_git_tag(tmp_path: Path) -> None:
    testing_dir = tmp_path / "testing_package"
    copy_assets("git_tag", testing_dir)
    run_shell = functools.partial(run_by_subprocess, cwd=testing_dir)
    result = run_shell("git init")
    assert result.returncode == 0
    result = run_shell("git config user.email tester@example.com")
    assert result.returncode == 0
    result = run_shell("git config user.name Tester")
    assert result.returncode == 0
    result = run_shell("git add .")
    assert result.returncode == 0
    result = run_shell("git commit -m release")
    assert result.returncode == 0
    result = build_package(testing_dir=testing_dir)
    assert "No Git tag found, not extracting dynamic version" in result.stderr
    assert result.returncode != 0
    result = run_shell("git tag 0.0.9")
    assert result.returncode == 0
    result = build_package(testing_dir=testing_dir)
    assert (
        "poetry-plugin-version: Git tag found, setting dynamic version to: 0.0.9"
        in result.stdout
    )
    assert "Built test_custom_version-0.0.9-py3-none-any.whl" in result.stdout
    wheel_path = testing_dir / "dist" / "test_custom_version-0.0.9-py3-none-any.whl"
    info = pkginfo.get_metadata(str(wheel_path))
    assert info and info.version == "0.0.9"
