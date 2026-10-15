# error: module '_weakref' is not supported: it is built into CPython, which imports it rather than the _weakref module on the module path, and Pystachy does not have it
# (#254) The program's directory holds a package _weakref (tests/errors/_weakref/), which
# CPython never imports in place of its builtin module, so neither does Pystachy
import _weakref

print(_weakref.ref)
