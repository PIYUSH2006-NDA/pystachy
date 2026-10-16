# A module-level iter is what the module's code reads, also in its functions: no read of the
# builtin iter, so no exception handling (eh_global.calls pins @main without pys_eh_on; see
# eh_names.py).
iter = 3


def get() -> int:
    return iter + 1


print(iter + 1, get())
