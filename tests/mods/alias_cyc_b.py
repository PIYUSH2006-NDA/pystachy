"""From-imports an alias of mods.alias_cyc_a while that module's code is still running."""
from mods.alias_cyc_a import first

print("alias_cyc_b:", first(41))
