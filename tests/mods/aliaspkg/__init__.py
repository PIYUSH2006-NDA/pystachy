"""A package that aliases a function of its submodule, as pylev's levenshtein = wfi_levenshtein."""
from .impl import twice

double = twice

__all__ = ["double", "twice"]
