from __future__ import annotations

__all__ = []  # type: ignore

import os
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from poetry.core.pyproject.toml import PyProjectTOML

from .utils import get_version_from_file

if TYPE_CHECKING:
    from collections.abc import MutableMapping


class _Mode(Enum):
    Classic = "classic"
    Pep621 = "pep621"


class _ProjectState:
    def __init__(
        self,
        path: Path,
        original_version: str | None,
        version: str | None,
        mode: _Mode,
        dynamic_array: Any | None,
        substitutions: "MutableMapping[Path, str] | None" = None,
    ) -> None:
        self.path = path
        self.original_version = original_version
        self.version = version
        self.mode = mode
        self.dynamic_array = dynamic_array
        self.substitutions = {} if substitutions is None else substitutions  # type: MutableMapping[Path, str]


class _State:
    def __init__(self) -> None:
        self.patched_core_poetry_create = False
        self.cli_mode = False
        self.projects = {}  # type: MutableMapping[str, _ProjectState]


_state = _State()


def _find_higher_file(*names: str, start: Path | None = None) -> Path | None:
    # Note: We need to make sure we get a pathlib object. Many tox poetry
    # helpers will pass us a string and not a pathlib object.
    if start is None:
        start = Path.cwd()
    elif not isinstance(start, Path):
        start = Path(start)
    for level in [start, *start.parents]:
        for name in names:
            if (f := level / name).is_file():
                return f
    return None


def _get_pyproject_path(start: Path | None = None) -> Path | None:
    return _find_higher_file("pyproject.toml", start=start)


def _get_pyproject_path_from_poetry(pyproject: "PyProjectTOML") -> Path:
    if not (recommended := getattr(pyproject, "path", None)):
        raise RuntimeError(
            "Unable to determine pyproject.toml path from Poetry instance"
        )
    return cast(Path, recommended)


def _get_version(pyproject_path: Path, name: str) -> str | None:
    init_path = pyproject_path.parent / name / "__init__.py"
    return get_version_from_file(init_path)


def _get_and_apply_version(pyproject_path: Path | None = None) -> str | None:
    if pyproject_path is None:
        pyproject_path = _get_pyproject_path()
        if pyproject_path is None:
            raise RuntimeError("Unable to find pyproject.toml")

    pyproject = PyProjectTOML(pyproject_path).data
    poetry_config = cast(dict[str, Any], pyproject.get("tool", {}).get("poetry", {}))
    if not poetry_config:
        return None
    classic = "name" in poetry_config
    project_item: dict[str, Any] = pyproject.get("project", {})
    pep621 = (
        project_item
        and "name" in project_item
        and "dynamic" in project_item
        and "version" in project_item.get("dynamic", {})
        and "version" not in project_item
        and "version" in poetry_config
    )

    if classic:
        name = cast(str, poetry_config["name"])
        dynamic_array = None
    elif pep621:
        name = cast(str, project_item["name"])
        dynamic_array = project_item["dynamic"]
    else:
        return None
    if name in _state.projects:
        return name

    original = poetry_config["version"]
    if (version := original) in ("0", "0.0.0"):
        initial_dir = Path.cwd()
        target_dir = pyproject_path.parent
        os.chdir(str(target_dir))
        try:
            version = _get_version(pyproject_path, name)
        finally:
            os.chdir(str(initial_dir))
    if name is not None:
        if classic and original is not None:
            mode = _Mode.Classic
            _state.projects[name] = _ProjectState(
                pyproject_path, original, version, mode, dynamic_array
            )
        elif pep621:
            mode = _Mode.Pep621
            _state.projects[name] = _ProjectState(
                pyproject_path, original, version, mode, dynamic_array
            )

    return name
