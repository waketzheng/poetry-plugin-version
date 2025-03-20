#!/usr/bin/env python
import re
import subprocess
from pathlib import Path


def build_version_0_whl() -> None:
    # Build a whl file with version=0
    subprocess.check_call(["poetry", "build", "--clean", "--format", "wheel"])
    root_dir = Path(__file__).parent.resolve().parent
    dist_dir = root_dir / "dist"
    whl_file = list(dist_dir.glob("*.whl"))[0]
    new_name = re.sub(r"(.*)-\d+\.\d+\.\d+(.*)", r"\1-0\2", whl_file.name)
    whl_file.rename(whl_file.with_name(new_name))


try:
    import pytest
except ImportError:
    if __name__ != "__main__":
        raise
else:

    @pytest.fixture(scope="session", autouse=True)
    def prepare_wheel_file() -> None:
        build_version_0_whl()


if __name__ == "__main__":
    build_version_0_whl()
