# error: 'int' has no method 'to_bytes'
# lib/random's randbytes() stays uncompiled (lib/README.md): Pystachy has no bytes
import random

random.seed(1)
print(random.randbytes(4))
