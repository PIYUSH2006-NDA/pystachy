"""The main program's docstring, with non-ASCII text: café."""
# A module's __doc__ (#252): its docstring as CPython 3.13 cleans it, or None (an f-string is no
# docstring), read as __doc__ in its code and functions, as m.__doc__, and by from m import
# __doc__ (also with as, in a function, and in an optional import's handler, as datetime.py
# takes _pydatetime's); a module that binds __doc__ itself reads its docstring before that;
# a package's and a namespace package's __doc__
from mods.docmod import __doc__ as d
from mods import docmod, nodoc, redoc
import mods
import mods.ns.leaf


def local_import() -> str | None:
    from mods.nodoc import __doc__
    return __doc__


def local_var() -> str:
    __doc__ = "a local"
    return __doc__


def main_doc() -> str:
    return __doc__


print(__doc__, __doc__.endswith("café."), main_doc() == __doc__)
print(repr(d))
print(d == docmod.__doc__, docmod.doc_of() == d, docmod.Thing().doc() == d + "!")
print(nodoc.__doc__, nodoc.has_doc(), local_import(), local_var())
print(repr(redoc.before), repr(redoc.now()))
print(redoc.after == d, repr(redoc.__doc__))
print(mods.__doc__, mods.ns.__doc__)
print((lambda: __doc__)()[:8], [__doc__[:3] for _ in range(2)])
