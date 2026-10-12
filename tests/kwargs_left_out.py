# A function of an imported module whose **kwargs annotation Pystachy cannot compile (Any) is left
# out, an error only where the program calls it, as one with another such parameter is: the import
# and the module's other functions work (it was an error at the import). Its **kwargs: int sibling
# is compiled.
import mods.kwargs_any
from mods.kwargs_any import count, tally

print(count(), mods.kwargs_any.count(), tally(a=1, b=2))
