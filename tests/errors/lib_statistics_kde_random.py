# error: name '_kernel_invcdfs' is not defined
# lib/statistics's kde_random() stays uncompiled (lib/README.md): it draws with random.Random, and
# its table of kernels is made where random imports (Pystachy has no random)
import statistics

print(statistics.kde_random([1.0, 2.0, 4.0], h=1.5, seed=8675309)())
