# error: a generator expression is only supported as the argument of
# lib/statistics's covariance() stays uncompiled (lib/README.md): it passes generator expressions to
# sumprod(), and the subset has them only as the arguments of some builtins
import statistics

print(statistics.covariance([1.0, 2.0, 3.0], [1.0, 3.0, 2.0]))
