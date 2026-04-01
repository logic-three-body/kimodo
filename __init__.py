# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Development shim so repo-root imports resolve to the inner kimodo package."""

from pathlib import Path

_INNER_PACKAGE_ROOT = Path(__file__).resolve().parent / "kimodo"
_INNER_INIT = _INNER_PACKAGE_ROOT / "__init__.py"

__file__ = str(_INNER_INIT)
__path__ = [str(_INNER_PACKAGE_ROOT)]

if __spec__ is not None:
    __spec__.submodule_search_locations = __path__

with _INNER_INIT.open("rb") as _f:
    exec(compile(_f.read(), __file__, "exec"))
