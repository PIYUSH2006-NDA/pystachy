# error: quantiles() returns both list[int] and list[float]
# lib/statistics's quantiles() of ints (lib/README.md): CPython returns n - 1 copies of one data
# point, ints, and interpolates floats between two or more
import statistics

print(statistics.quantiles([1, 3, 2, 4], n=4))
