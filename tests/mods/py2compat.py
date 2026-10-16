"""Python 2 compatibility shims, as hashids, _compat_pickle and locale write them."""
NAMES = ("ValueError",)

try:
    WindowsError  # noqa: F821
except NameError:
    pass
else:
    NAMES += ("WindowsError",)

try:
    CODESET  # noqa: F821
except NameError:
    def encoding(do_setlocale: bool = True) -> str:
        return "utf-8" if do_setlocale else "ascii"
else:
    def encoding(do_setlocale: bool = True) -> str:
        return "?"

try:
    StrType = basestring  # noqa: F821
except NameError:
    StrType = str
