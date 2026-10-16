"""Binds a type statement's alias only after importing a module that imports it back (tests/errors/type_statement_import_cycle.py)."""
from emods.ts_cyc_b import height

type Grid = list[list[int]]
