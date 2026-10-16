# error: triangular() returns both int and float
# lib/random's triangular() returns its low bound unchanged where the mode's fraction of the range
# divides by zero, and a float otherwise (lib/README.md): int bounds would give both types
import random

random.seed(1)
print(random.triangular(1, 3))
