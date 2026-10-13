# error: unsupported call iter(list[float])
# lib/statistics's harmonic_mean() stays uncompiled (lib/README.md): it asks whether iter(data) is
# data (the subset has no iterators), and sums exactly with _sum(), as fractions.Fraction
import statistics

print(statistics.harmonic_mean([40.0, 60.0]))
