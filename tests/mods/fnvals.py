"""Functions passed as values across modules (fn_values_mod.py): names qualified by the loader."""


def inc(x):
    return x + 1


def apply_all(fs, x):
    for f in fs:
        x = f(x)
    return x


def apply(f, x, times=1):
    for _ in range(times):
        x = f(x)
    return x


def default_key(x, key=len):
    return key(x)


def chooser(name):
    return inc if name == "inc" else inc
