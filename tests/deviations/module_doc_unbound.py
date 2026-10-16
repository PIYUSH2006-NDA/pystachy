# A module without a docstring that binds __doc__ itself, where the first statement that names
# __doc__ is a def, has no __doc__ until its code binds it: the function's earlier read raises
# NameError, where CPython's reads None (with module-level code first, it reads None).
def title() -> str:
    return __doc__


try:
    print(title())
except NameError as e:
    print(e)
__doc__ = "set"
print(title())
