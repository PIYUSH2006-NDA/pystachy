"""   A module's docstring: CPython 3.13 strips the first line's leading spaces,
	expands tabs (é counts one column)	and
    removes the indentation the other lines share.

      More.
    """


def doc_of() -> str:
    return __doc__


class Thing:
    def doc(self) -> str:
        return __doc__ + "!"
