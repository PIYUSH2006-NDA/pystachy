# Pystachy's float text in an extension module whose host calls setlocale
from ffi import export


@export
def show(x: float) -> str:
    return str(x) + " " + str(float("2.5") * 2) + " " + repr(0.1) + " " + f"{x:.3f}"
