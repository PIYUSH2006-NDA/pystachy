"""Check lib/_pystachy_itertools.py on CPython against CPython's C module itertools.

For random calls of each of the module's functions (small lists of ints and strs, empty ones,
and arguments at the edges of the C checks: negative, zero, None, floats and strs where an
integer goes), the port and the C module must raise the same error when called, or give an
iterator that yields the same items in the same order and reads its inputs in the same order:
each input is an iterator that logs its reads, and the items are taken one at a time, as many
as the case says, interleaving tee()'s iterators and groupby()'s groups with their groupby().
A case stops at the first error an item raises (a generator is finished after it, where the
C iterators can go on: lib/compatibility.md), and an input's reads after its end are left out
(first_ends()). The module's names and docstring must be the C module's.
Usage: python3 -I tools/itertools_check.py [--rounds N] [--seed S]
"""
import argparse
import importlib.util
import itertools
import operator
from pathlib import Path
import random
import sys

LIB = Path(__file__).resolve().parent.parent / "lib"
sys.dont_write_bytecode = True  # (no __pycache__ in lib/)
NAMES = ["accumulate", "batched", "chain", "combinations", "combinations_with_replacement", "compress", "count",
         "cycle", "dropwhile", "filterfalse", "groupby", "islice", "pairwise", "permutations", "product", "repeat",
         "starmap", "takewhile", "tee", "zip_longest"]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class Logged:
    """An iterator over items that logs each read, and the end, in a shared list."""

    def __init__(self, name, items, log):
        self.name = name
        self.items = list(items)
        self.log = log
        self.i = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.i >= len(self.items):
            self.log.append(self.name + ":end")
            raise StopIteration
        self.log.append(f"{self.name}:{self.i}")
        self.i += 1
        return self.items[self.i - 1]


def first_ends(log):
    """The log without the reads of an input after its end: the C iterators of accumulate(),
    compress(), dropwhile(), filterfalse(), groupby(), starmap() and takewhile() read their inputs
    again when called after their end, where a generator has finished
    (tests/deviations/lib_itertools_ended.py), and compress()'s, after its selectors' end, also
    reads an item of its data each time"""
    ended = set()
    out = []
    for entry in log:
        if entry.endswith(":end"):
            if entry in ended:
                continue
            ended.add(entry)
        out.append(entry)
        if entry == "sel:end":
            break
    return out


def err(e):
    return f"{type(e).__name__}: {e}"


def drive(mod, case, log):
    """What a case gives with module mod: the error of the call or the items taken, in order."""
    out = []
    try:
        it = case(mod, log)
    except Exception as e:
        return [err(e)]
    plan = case.plan
    try:
        if case.kind == "tee":
            its = list(it)
            out.append(f"n={len(its)}")
            for k in plan:
                if its:
                    out.append(repr(next(its[k % len(its)], "<end>")))
        elif case.kind == "groupby":
            groups = []
            for k in plan:
                if k % 3 == 0 or not groups:
                    nxt = next(it, None)
                    if nxt is None:
                        out.append("<end>")
                        break
                    groups.append(nxt[1])
                    out.append(f"key {nxt[0]!r}")
                else:
                    out.append(repr(next(groups[k % len(groups)], "<end>")))
        else:
            for _ in range(plan):
                out.append(repr(next(it, "<end>")))
    except Exception as e:
        out.append(err(e))
    return out


def gen_items(rng, kind=None):
    kind = kind or rng.choice(["int", "str", "bool"])
    n = rng.choice([0, 0, 1, 2, 3, 4, 5, 7, 9])
    if kind == "int":
        return [rng.randint(-3, 9) for _ in range(n)]
    if kind == "bool":
        return [rng.random() < 0.5 for _ in range(n)]
    return [rng.choice("aabbcz") for _ in range(n)]


def gen_int_arg(rng, low=-2, high=6):
    r = rng.random()
    if r < 0.06:
        return None
    if r < 0.1:
        return 1.5
    if r < 0.13:
        return "3"
    if r < 0.16:
        return True
    return rng.randint(low, high)


def make_case(rng, name):
    """A case: a function of (module, log) that calls name, with the plan of items to take."""
    a = gen_items(rng)
    b = gen_items(rng, "int")
    plan = rng.randint(0, 14)
    kind = "plain"

    def lg(nm, items, log):
        return Logged(nm, items, log)

    if name == "count":
        start = rng.choice([0, 3, -2, 2.5, True, "x", 9223372036854775806])
        step = rng.choice([1, 2, -1, 0.5, 0, True, "y"])
        form = rng.randint(0, 2)

        def case(m, log):
            return m.count() if form == 0 else m.count(start) if form == 1 else m.count(start, step)
    elif name == "cycle":
        def case(m, log):
            return m.cycle(lg("a", a, log))
        plan = rng.randint(0, 20)
    elif name == "repeat":
        times = gen_int_arg(rng)
        form = rng.randint(0, 2)

        def case(m, log):
            return m.repeat("r") if form == 0 else m.repeat("r", times) if form == 1 else m.repeat("r", times=times)
    elif name == "accumulate":
        func = rng.choice([None, operator.mul, max, min, operator.sub])
        initial = rng.choice([None, None, 100, 0])
        items = b if func is not None and rng.random() < 0.8 else a

        def case(m, log):
            return m.accumulate(lg("a", items, log), func, initial=initial)
    elif name == "batched":
        n = gen_int_arg(rng, -1, 4)
        strict = rng.random() < 0.3

        def case(m, log):
            return m.batched(lg("a", a, log), n, strict=strict)
    elif name == "chain":
        k = rng.randint(0, 3)
        lists = [gen_items(rng, "int") for _ in range(k)]
        if rng.random() < 0.5:
            def case(m, log):
                return m.chain(*[lg(f"i{j}", x, log) for j, x in enumerate(lists)])
        else:
            def case(m, log):
                return m.chain.from_iterable(lg("outer", [lg(f"i{j}", x, log) for j, x in enumerate(lists)], log))
    elif name == "compress":
        sel = [rng.random() < 0.5 for _ in range(rng.randint(0, 8))]

        def case(m, log):
            return m.compress(lg("data", a, log), lg("sel", sel, log))
    elif name in ("dropwhile", "takewhile", "filterfalse"):
        pivot = rng.randint(-1, 6)
        pred = None if name == "filterfalse" and rng.random() < 0.3 else (lambda x: x < pivot)

        def case(m, log):
            return getattr(m, name)(pred, lg("a", b, log))
    elif name == "groupby":
        kind = "groupby"
        plan = [rng.randint(0, 8) for _ in range(rng.randint(0, 16))]
        key = rng.choice([None, lambda x: x // 3, str])

        def case(m, log):
            return m.groupby(lg("a", b, log), key)
    elif name == "islice":
        nargs = rng.randint(0, 4)
        args = [gen_int_arg(rng, -1, 8) for _ in range(nargs)]

        def case(m, log):
            return m.islice(lg("a", b, log), *args)
    elif name == "pairwise":
        def case(m, log):
            return m.pairwise(lg("a", a, log))
    elif name == "starmap":
        pairs = [(rng.randint(-3, 5), rng.randint(1, 4)) for _ in range(rng.randint(0, 6))]

        def case(m, log):
            return m.starmap(operator.floordiv, lg("a", pairs, log))
    elif name == "tee":
        kind = "tee"
        plan = [rng.randint(0, 5) for _ in range(rng.randint(0, 70))]
        n = gen_int_arg(rng, -1, 4)
        items = list(range(rng.choice([0, 3, 60, 130])))
        form = rng.random() < 0.3

        def case(m, log):
            return m.tee(lg("a", items, log)) if form else m.tee(lg("a", items, log), n)
    elif name == "zip_longest":
        k = rng.randint(0, 3)
        lists = [gen_items(rng, "int") for _ in range(k)]
        fill = rng.choice([None, -1])

        def case(m, log):
            return m.zip_longest(*[lg(f"i{j}", x, log) for j, x in enumerate(lists)], fillvalue=fill)
    elif name == "product":
        k = rng.randint(0, 3)
        lists = [gen_items(rng, "int")[:4] for _ in range(k)]
        rep = gen_int_arg(rng, -1, 3)
        form = rng.random() < 0.5
        plan = rng.randint(0, 30)

        def case(m, log):
            its = [lg(f"i{j}", x, log) for j, x in enumerate(lists)]
            return m.product(*its) if form else m.product(*its, repeat=rep)
    else:  # permutations, combinations, combinations_with_replacement
        r = gen_int_arg(rng, -1, 6)
        plan = rng.randint(0, 40)
        form = name == "permutations" and rng.random() < 0.3

        def case(m, log):
            return getattr(m, name)(lg("a", a, log)) if form else getattr(m, name)(lg("a", a, log), r)
    case.plan = plan
    case.kind = kind
    return case


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()
    port = load("_pystachy_itertools", LIB / "_pystachy_itertools.py")
    bad = 0
    if port.__doc__ != itertools.__doc__:
        print("the module's docstring differs")
        bad += 1
    for name in NAMES:
        if not hasattr(port, name):
            print("missing:", name)
            bad += 1
    rng = random.Random(args.seed)
    cases = 0
    for name in NAMES:
        for _ in range(args.rounds):
            case = make_case(rng, name)
            log1, log2 = [], []
            want = drive(itertools, case, log1)
            got = drive(port, case, log2)
            cases += 1
            if want != got or first_ends(log1) != first_ends(log2):
                bad += 1
                if bad <= 10:
                    print(f"{name}: C {want} reads {log1}\n  port {got} reads {log2}")
    print(f"{cases} cases, {bad} differ")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
