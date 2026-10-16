"""Binds a name of the module that imports it (tests/mods/shim_c.py) before that module's try reads it."""
import mods.shim_c as shim_c

shim_c.unicode = str
