import ast
import subprocess
from pathlib import Path
from typing import Any, Dict, NoReturn, Optional

from cleo.io.io import IO
from poetry.core.utils.helpers import module_name
from poetry.plugins.plugin import Plugin
from poetry.poetry import Poetry


class VersionPlugin(Plugin):
    def abort(self, message: str) -> NoReturn:
        self.__io.write_error_line(message)
        raise RuntimeError(message)

    def activate(self, poetry: Poetry, io: IO) -> None:
        name = "poetry-plugin-version"
        poetry_version_config: Optional[Dict[str, Any]] = poetry.pyproject.data.get(
            "tool", {}
        ).get(name)
        if poetry_version_config is None:
            return
        self.__io = io
        if not (version_source := poetry_version_config.get("source")):
            self.abort(
                f"<b>{name}</b>: No <b>source</b> configuration found in "
                f"[tool.{name}] in pyproject.toml, not extracting dynamic version"
            )
        if version_source == "init":
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
                f"<b>{name}</b>: Using __init__.py file at "
                f"{init_path} for dynamic version"
            )
            tree = ast.parse(init_path.read_text())
            for el in tree.body:
                if isinstance(el, ast.Assign) and len(el.targets) == 1:
                    target = el.targets[0]
                    if isinstance(target, ast.Name) and target.id == "__version__":
                        if isinstance(value_node := el.value, ast.Constant):
                            version = value_node.value
                        elif isinstance(value_node, ast.Str):
                            version = value_node.s
                        else:  # pragma: nocover
                            # This is actually covered by tests, but can't be
                            # reported by Coverage
                            # Ref: https://github.com/nedbat/coveragepy/issues/198
                            continue
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
        elif version_source == "git-tag":
            self.set_version_from_git_tag(poetry, io, name)

    def set_version_from_git_tag(self, poetry: Poetry, io: IO, name: str) -> None:
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
