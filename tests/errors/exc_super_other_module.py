# error: super_other.py:11: error: super() is only supported without arguments, in the methods of exception classes (super(C, self) in a method of C is super())
from emods.super_other import B

print(B("x"))
