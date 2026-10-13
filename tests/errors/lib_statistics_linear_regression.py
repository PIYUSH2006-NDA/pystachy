# error: a generator expression is only supported as the argument of
# lib/statistics's linear_regression() stays uncompiled (lib/README.md): it passes a generator
# expression to sumprod(), and its result is a collections.namedtuple (Pystachy has no collections)
import statistics

print(statistics.linear_regression([1.0, 2.0, 3.0], [1.0, 3.0, 2.0]))
