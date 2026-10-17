"""The types module's TracebackType, which is all of it the subset has (Pystachy's own module).

CPython's types module names the interpreter's own types. A with statement's context manager
takes one of them, TracebackType, as the annotation of its __exit__() traceback parameter
(``tb: TracebackType | None``), and ``from types import TracebackType`` imports this module's
class (Loader.parse); an import of the types module, or of another of its names, finds no
module, as before. Pystachy keeps no tracebacks: a with statement whose exception reaches
__exit__() passes an object of this class, which has none of a traceback's attributes
(tb_frame, tb_lineno, tb_next), and None otherwise, as CPython does.
"""


class TracebackType:
    """The type of the traceback a with statement passes to __exit__(), which holds nothing."""
