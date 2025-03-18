from __future__ import annotations

import ast
import contextlib
from pathlib import Path
from typing import cast

with contextlib.suppress(ImportError):
    from poetry.console.commands.build import BuildHandler

    _origin_requires_isolated_build = BuildHandler._requires_isolated_build

    def _requires_isolated_build(self: BuildHandler) -> bool:
        if not _origin_requires_isolated_build(self):
            return False
        # patch poetry to avoid using isolated_builder for this plugin
        return not any(
            dep.name.replace("_", "-") == "poetry-plugin-version"
            for dep in self.poetry.build_system_dependencies
        )

    BuildHandler._requires_isolated_build = _requires_isolated_build  # type:ignore


def get_version_from_file(init_path: Path) -> str | None:
    tree = ast.parse(init_path.read_text(encoding="utf-8"))
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
                return cast(str, version)
    return None
