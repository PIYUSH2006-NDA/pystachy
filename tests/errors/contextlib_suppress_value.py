# error: the builtin 'KeyError' cannot be used as a value
from contextlib import suppress

quiet = suppress(KeyError)
with quiet:
    print({}["k"])
