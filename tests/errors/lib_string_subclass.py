# error: class inheritance is not supported (only an exception class may have a base)
# lib/string's Template with another delimiter, as a subclass of it (lib/README.md): Pystachy has
# no inheritance but an exception class's
from string import Template


class Percent(Template):
    delimiter = "%"


print(Percent("%who").substitute(who="tim"))
