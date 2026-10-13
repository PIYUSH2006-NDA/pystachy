# error: name 'count' is not defined
# lib/statistics's correlation() stays uncompiled (lib/README.md): its ranks, for method='ranked',
# take itertools' count() and groupby(), whose import is optional (Pystachy has no itertools)
import statistics

print(statistics.correlation([1.0, 2.0, 3.0], [1.0, 3.0, 2.0]))
