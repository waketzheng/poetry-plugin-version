import re
import subprocess
from pathlib import Path

import pytest


def build_version_0_whl() -> None:
    subprocess.check_call(["poetry", "build", "--clean", "--format", "wheel"])
    root_dir = Path(__file__).parent.resolve().parent
    dist_dir = root_dir / "dist"
    whl_file = list(dist_dir.glob("*.whl"))[0]
    new_name = re.sub(r"(.*)-\d+\.\d+\.\d+(.*)", r"\1-0\2", whl_file.name)
    whl_file.rename(whl_file.with_name(new_name))


@pytest.fixture(scope="session", autouse=True)
def prepare_wheel_file() -> None:
    # Build a whl file with version=0
    build_version_0_whl()
