"""
pylev
=====

A pure Python Levenshtein implementation that's not freaking GPL'd.

Based off the Wikipedia code samples at
http://en.wikipedia.org/wiki/Levenshtein_distance.

Usage
-----

Usage is fairly straightforward.::

    import pylev
    distance = pylev.levenshtein('kitten', 'sitting')
    assert distance == 3

"""
from .classic import classic_levenshtein
from .recursive import recursive_levenshtein
from .wf import wf_levenshtein, wfi_levenshtein
from .damerau import damerau_levenshtein

__author__ = "Daniel Lindsley"
__version__ = (1, 4, 0)
__license__ = "New BSD"


# Pystachy port: the three aliases are from-imports of the same functions. Another module's
# from-import of an alias (name = f) of a from-imported function fails (`from pylev import
# levenshtein`: name 'levenshtein' is not defined), where `pylev.levenshtein` works
from .wf import wfi_levenshtein as levenshtein

# Backward-compatibilty because I misspelled.
from .classic import classic_levenshtein as classic_levenschtein  # Pystachy port: as above
from .wf import wfi_levenshtein as levenschtein  # Pystachy port: as above


__all__ = [
    "levenshtein",
    "classic_levenshtein",
    "recursive_levenshtein",
    "wf_levenshtein",
    "wfi_levenshtein",
    "damerau_levenshtein",
]
