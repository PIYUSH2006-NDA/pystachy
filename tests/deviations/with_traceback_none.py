# Documented deviation (#490 stage 4): an __exit__ whose traceback parameter is not annotated
# TracebackType | None (from types) is given None for it, where CPython passes the exception's
# traceback object: tb is None is True here, and False in CPython. Annotated so, the parameter
# takes an object of TracebackType, which is not None (and has none of a traceback's
# attributes), as tests/with_cm.py shows.
class CM:
    def __enter__(self) -> None:
        pass

    def __exit__(self, et, ev, tb) -> bool:
        print(et.__name__ if et is not None else None, tb is None)
        return True


with CM():
    raise KeyError("k")
with CM():
    pass
