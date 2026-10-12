# error: **kwargs is not supported
class A:
    def m(self, **kw: int) -> int:
        return len(kw)


print(A().m(a=1))
