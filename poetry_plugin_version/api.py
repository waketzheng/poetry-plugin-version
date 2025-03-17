from __future__ import annotations

import contextlib

from poetry.core.masonry.api import (
    build_sdist,
    build_wheel,
    get_requires_for_build_sdist,
    get_requires_for_build_wheel,
    prepare_metadata_for_build_wheel,
)

from . import patch

with contextlib.suppress(ImportError):
    from poetry.console.commands.build import BuildHandler

    # to be optimize
    BuildHandler._requires_isolated_build = lambda *args, **kw: False  # type:ignore

patch.activate()

__all__ = (
    "build_sdist",
    "build_wheel",
    "get_requires_for_build_sdist",
    "get_requires_for_build_wheel",
    "prepare_metadata_for_build_wheel",
)
