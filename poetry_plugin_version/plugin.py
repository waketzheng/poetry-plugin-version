from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any, NoReturn

from poetry.core.utils.helpers import module_name
from poetry.plugins.plugin import Plugin

from .utils import get_version_from_file

if TYPE_CHECKING:  # pragma: no cover
    from cleo.io.io import IO
    from poetry.poetry import Poetry


class VersionPlugin(Plugin):
    def abort(self, message: str) -> NoReturn:
        self.__io.write_error_line(message)
        raise RuntimeError(message)

    def activate(self, poetry: "Poetry", io: "IO") -> None:
        name = "poetry-plugin-version"
        pyproject_data = poetry.pyproject.data
        tool_item = pyproject_data.get("tool", {})
        poetry_version_config: dict[str, Any] | None = tool_item.get(name)
        not_in_build_system = name not in str(pyproject_data.get("build-system"))
        if poetry_version_config is None and not_in_build_system:
            return
        self.__io = io
        if not (version_source := (poetry_version_config or {}).get("source")):
            if tool_item.get("poetry", {}).get("version") in ("0", "0.0.0"):
                if not_in_build_system:
                    self.abort(
                        f"<b>{name}</b>: No <b>source</b> configuration found in "
                        f"[tool.{name}] in pyproject.toml, not extracting dynamic version"
                    )
                self.set_version_from_file(poetry, io, name)
            return
        if version_source == "git-tag":
            self.set_version_from_git_tag(poetry, io, name)
        else:
            self.set_version_from_file(poetry, io, name)

    def set_version_from_file(self, poetry: "Poetry", io: "IO", name: str) -> None:
        if packages := poetry.local_config.get("packages"):
            if len(packages) != 1:
                self.abort(
                    f"<b>{name}</b>: More than one package set, "
                    "cannot extract dynamic version"
                )

            package_name = packages[0]["include"]
        else:
            package_name = module_name(poetry.package.name)
        if not (init_path := Path(package_name) / "__init__.py").is_file() and (
            not (init_path := poetry.file.path.parent / init_path).is_file()
        ):
            self.abort(
                f"<b>{name}</b>: __init__.py file not found at "
                f"{init_path} cannot extract dynamic version"
            )
        io.write_line(
            f"<b>{name}</b>: Using __init__.py file at {init_path} for dynamic version"
        )
        if version := get_version_from_file(init_path):
            io.write_line(
                f"<b>{name}</b>: Setting package "
                "dynamic version to __version__ "
                f"variable from __init__.py: <b>{version}</b>"
            )
            poetry.package._set_version(version)
            return
        self.abort(
            f"<b>{name}</b>: No valid __version__ variable found "
            "in __init__.py, cannot extract dynamic version"
        )

    def set_version_from_git_tag(self, poetry: "Poetry", io: "IO", name: str) -> None:
        result = subprocess.run(
            ["git", "describe", "--exact-match", "--tags", "HEAD"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )
        if result.returncode != 0:
            self.abort(
                f"<b>{name}</b>: No Git tag found, not extracting dynamic version"
            )
        tag = result.stdout.strip()
        io.write_line(
            f"<b>{name}</b>: Git tag found, setting dynamic version to: {tag}"
        )
        poetry.package._set_version(tag)
