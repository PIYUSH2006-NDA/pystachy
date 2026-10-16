# Documented deviations of lib/ modules' __doc__ from CPython's: the modules written for Pystachy
# have docstrings of their own (collections too: lib_collections.py), where CPython's begin
# "functools.py - Tools for working with functions", "The io module provides the Python
# interfaces to stream handling" and "curses"; and operator's is its Python module's, which
# CPython replaces with _operator's, "Operator interface.".
import curses
import functools
import io
import operator

print(functools.__doc__.splitlines()[0])
print(io.__doc__.splitlines()[0])
print(curses.__doc__.splitlines()[0])
print(operator.__doc__.strip().splitlines()[0])
