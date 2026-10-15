# error: defaultdict() cannot bind its type variables from the argument for 'default_factory', a <built-in function int>
# A lambda's result takes no type from the Callable it becomes: def inner() -> defaultdict[str, int]
from collections import defaultdict

nested: defaultdict[str, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))
nested["a"]["b"] += 1
print(nested)
