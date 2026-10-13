# error: median() returns both int and float
# lib/statistics's median() of ints (lib/README.md): CPython returns the middle int of an odd
# number of them, and the mean of the two middle ones, a float, of an even number; a function of
# Pystachy has one return type (median_low() and median_high() return an item)
import statistics

print(statistics.median([1, 3, 2]))
