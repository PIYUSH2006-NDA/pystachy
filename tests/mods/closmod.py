"""Closures in an imported module (closures_mod.py): the loader qualifies the module's own names in
their bodies, and leaves alone their parameters and the variables of the functions around them."""

SCALE = 3
noop = lambda x: x
twice = lambda f, x: f(f(x))


def scaled(k):
    return lambda x: x * k * SCALE


def tally(words):
    counts: dict[str, int] = {}
    seen = 0

    def note(w):
        nonlocal seen
        seen += 1
        counts[w] = counts.get(w, 0) + 1

    for w in words:
        note(w)
    return (seen, sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def pipeline(*steps):
    def run(x):
        for s in steps:
            x = s(x)
        return x
    return run


def keyed(xs, key=lambda v: -v):
    return sorted(xs, key=key)
