# Class templates of an imported module: specialized for the arguments of each call that makes an
# object; Never, whose field cannot be typed, is an error only where the program makes one
from mods.ctmpl import Cell, make
import mods.ctmpl

a = Cell(1)
b = mods.ctmpl.Cell("s", "x")
print(a, b, a.get() + 1, b.get().upper(), make(2.5), a.relabel(3), make([1]).relabel("z"))
print(isinstance(a, Cell), isinstance(b, mods.ctmpl.Cell), isinstance(make(1), Cell))
