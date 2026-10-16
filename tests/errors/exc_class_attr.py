# error: the attributes of the class of an exception (type[BaseException]) other than __name__ are not supported (.__qualname__)
from types import TracebackType


class Show:
    def __enter__(self) -> None:
        pass

    def __exit__(self, et: type[BaseException] | None, ev: BaseException | None, tb: TracebackType | None) -> None:
        if et is not None:
            print(et.__qualname__)


with Show():
    raise KeyError("k")
