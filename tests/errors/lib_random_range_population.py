# error: range() is only supported in a for loop
# lib/random's sample() takes a sequence (lib/README.md); a range is not a value in Pystachy, and
# list(range(n)) is the population
import random

random.seed(1)
print(random.sample(range(100), 3))
