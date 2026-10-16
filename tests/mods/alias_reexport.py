"""Re-exports type aliases and a TypeVar of mods.alias_types, and makes aliases of them."""
from mods.alias_types import Grid, Pair, Pos, Row, T

Rows = list[Row]
Coord = Pair[Pos]
Cells = Grid[T]
