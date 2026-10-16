"""Its own docstring, which it replaces, as datetime does with _pydatetime's."""
from __future__ import annotations

before = __doc__


def now() -> str:
    return __doc__


try:
    from ._nodocmod import x
except ImportError:
    from .docmod import __doc__
after = __doc__
__doc__ = __doc__[:10] + "..."
