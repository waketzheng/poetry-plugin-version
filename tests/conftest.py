import os
import subprocess
import sys
import threading
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest
import uvicorn

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


class UvicornServer(uvicorn.Server):
    def __init__(self, app: str = "tests.api:app", **kw: Any) -> None:
        port = self.load_port()
        super().__init__(config=uvicorn.Config(app, port=port, **kw))

    @staticmethod
    def load_port() -> int:
        file = Path(__file__).parent / "assets" / "poetry_v2_api" / "pyproject.toml"
        pyproject = tomllib.loads(file.read_text("utf-8"))
        for package in pyproject["build-system"]["requires"]:
            if "poetry-plugin-version" not in package:
                continue
            port = package.split("://", 1)[-1].split("/", 1)[0].split(":")[-1]
            return int(port)
        return 8000

    def install_signal_handlers(self) -> None:
        pass

    @contextmanager
    def run_in_thread(self) -> Generator[None]:
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()
        try:
            while not self.started:
                time.sleep(1e-3)
            yield
        finally:
            self.should_exit = True
            thread.join()


def build_version_0_whl() -> Path:
    root_dir = Path(__file__).parent.resolve().parent
    pyproject = root_dir / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    dist_dir = root_dir.joinpath("dist")
    for whl in dist_dir.glob("*"):
        whl.unlink()
    lines = text.splitlines()
    for index, line in enumerate(lines):
        line = line.split("#")[0].rstrip()
        if line.startswith('version = "') and line.endswith('"'):
            lines[index] = 'version = "0"'
            break
    pyproject.write_text(os.linesep.join(lines), encoding="utf-8")
    try:
        subprocess.run(["poetry", "build"])
    finally:
        pyproject.write_text(text, encoding="utf-8")
    return dist_dir


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def media_server() -> Generator[Path]:
    # Build a whl file with version=0
    dist_dir = build_version_0_whl()
    # Start a media server at http://localhost:8000 to download /dist/poetry_plugin_version-0-xxx.whl
    with UvicornServer().run_in_thread():
        yield dist_dir
