# Documented deviations of lib/random (CPython 3.13's random with marked edits, on lib/_pyrandom's
# Mersenne Twister) from CPython.
import math
from random import Random

# Pystachy's ints are 64-bit: getrandbits() takes up to 63 bits, and raises OverflowError past
# them before it draws: CPython prints 10499958131665514997, then 0.8474337369372327.
r = Random(1)
try:
    print(r.getrandbits(64))
except OverflowError as e:
    print("OverflowError:", e)
print(r.random())

# A range whose width leaves 64 bits raises OverflowError: CPython prints -2922244813938350433.
try:
    print(Random(2).randrange(-2**62, 2**62))
except OverflowError as e:
    print("OverflowError:", e)

# A NaN seeds as its hash, which is its object's address in CPython (so its draws differ from run
# to run there); a Pystachy float has none, and its hash is 0: CPython prints False.
print(Random(math.nan).random() == Random(0).random())

# The items of a str are its bytes past ASCII, as indexing gives them: CPython raises ValueError
# (Sample larger than population or is negative) for the two characters.
print(len(Random(3).sample("ñu", 3)))
