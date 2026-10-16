# error: expected int, got float (compiling statistics._rank(
# lib/statistics's correlation() stays uncompiled (lib/README.md): its ranks, for method='ranked',
# take itertools' count() and groupby(), which compile, but _rank() puts the float ranks in a list
# of ints ([0] * len(val_pos)); the method is a str, so the ranks are compiled for 'linear' too
import statistics

print(statistics.correlation([1.0, 2.0, 3.0], [1.0, 3.0, 2.0]))
