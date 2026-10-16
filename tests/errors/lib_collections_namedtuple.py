# error: 'namedtuple' from 'collections' is not supported
# namedtuple() makes a class at run time, with untyped fields: a typing.NamedTuple class is supported
from collections import namedtuple

Point = namedtuple("Point", "x y")
print(Point(1, 2))
