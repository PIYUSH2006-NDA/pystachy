# error: getattr() is supported with two arguments, the second a str literal (or, in operator's getters, a constant name)
# A method's name must be a literal: a getter specializes on literal arguments only
from operator import methodcaller

name = "upper"
print(methodcaller(name)("x"))
