from __future__ import annotations

import subprocess
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any

from poetry.core.utils.helpers import module_name
from poetry.plugins.plugin import Plugin

from .utils import get_version_from_file

if TYPE_CHECKING:  # pragma: no cover
    from typing import NoReturn

    from cleo.io.io import IO
    from poetry.poetry import Poetry


class VersionPlugin(Plugin):
    @staticmethod
    def abort(message: str, io: IO) -> NoReturn:
        io.write_error_line(message)
        raise RuntimeError(message)

    def activate(self, poetry: Poetry, io: IO) -> None:
        name = "poetry-plugin-version"
        pyproject_data = poetry.pyproject.data
        tool_item = pyproject_data.get("tool", {})
        poetry_version_config: dict[str, Any] | None = tool_item.get(name)
        not_in_build_system = name not in str(
            pyproject_data.get("build-system")
        ).lower().replace("_", "-")
        if poetry_version_config is None and not_in_build_system:
            return
        abort = partial(self.abort, io=io)
        if not (version_source := (poetry_version_config or {}).get("source")) and not (
            # Accept `path = package_dir/version.py` format to compare with pdm.
            version_source := (poetry_version_config or {}).get("path")
        ):
            if tool_item.get("poetry", {}).get("version") in ("0", "0.0.0"):
                if not_in_build_system:
                    abort(
                        f"<b>{name}</b>: No <b>source</b> configuration found in "
                        f"[tool.{name}] in pyproject.toml, not extracting dynamic version"
                    )
                self.set_version_from_file(poetry, io, name)
            return
        if version_source == "git-tag":
            self.set_version_from_git_tag(poetry, io, name)
        elif version_source.endswith(".py"):
            self.set_version_from_file(poetry, io, name, filename=version_source)
        else:
            self.set_version_from_file(poetry, io, name)

    def set_version_from_file(
        self, poetry: Poetry, io: IO, name: str, filename: str = "__init__.py"
    ) -> None:
        init_path = Path(filename)
        if Path(init_path.name) == init_path or not init_path.is_file():
            if packages := poetry.local_config.get("packages"):
                if len(packages) != 1:
                    self.abort(
                        f"<b>{name}</b>: More than one package set, "
                        "cannot extract dynamic version",
                        io=io,
                    )

                package_name = packages[0]["include"]
            else:
                package_name = module_name(poetry.package.name)
            init_path = Path(package_name) / filename
            if not init_path.is_file():
                root_dir = poetry.file.path.parent
                if (init_ := root_dir / init_path).is_file():
                    init_path = init_
                elif (src_init := Path("src") / init_path).is_file():
                    init_path = src_init
                elif (abs_src_init := root_dir / "src" / init_path).is_file():
                    init_path = abs_src_init
                else:
                    self.abort(
                        f"<b>{name}</b>: {filename} file not found at "
                        f"{init_path} cannot extract dynamic version",
                        io=io,
                    )
        io.write_line(
            f"<b>{name}</b>: Using {filename} file at {init_path} for dynamic version"
        )
        if version := get_version_from_file(init_path):
            io.write_line(
                f"<b>{name}</b>: Setting package "
                "dynamic version to __version__ "
                f"variable from {filename}: <b>{version}</b>"
            )
            poetry.package._set_version(version)
            return
        self.abort(
            f"<b>{name}</b>: No valid __version__ variable found "
            f"in {filename}, cannot extract dynamic version",
            io=io,
        )

    def set_version_from_git_tag(self, poetry: Poetry, io: IO, name: str) -> None:
        result = subprocess.run(
            ["git", "describe", "--exact-match", "--tags", "HEAD"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            self.abort(
                f"<b>{name}</b>: No Git tag found, not extracting dynamic version",
                io=io,
            )
        tag = result.stdout.strip()
        io.write_line(
            f"<b>{name}</b>: Git tag found, setting dynamic version to: {tag}"
        )
        poetry.package._set_version(tag)
