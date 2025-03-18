import os
import subprocess
from collections.abc import Generator
from pathlib import Path

import pytest


def build_version_0_whl() -> Path:
    root_dir = Path(__file__).parent.resolve().parent
    pyproject = root_dir / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    dist_dir = root_dir.joinpath("dist")
    lines = text.splitlines()
    for index, line in enumerate(lines):
        line = line.split("#")[0].rstrip()
        if line.startswith('version = "') and line.endswith('"'):
            lines[index] = 'version = "0"'
            break
    pyproject.write_text(os.linesep.join(lines), encoding="utf-8")
    try:
        subprocess.run(["poetry", "build", "--clean", "--format", "wheel"])
    finally:
        pyproject.write_text(text, encoding="utf-8")
    return dist_dir


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
def prepare_wheel_file() -> Generator[Path]:
    # Build a whl file with version=0
    dist_dir = build_version_0_whl()
    yield dist_dir
