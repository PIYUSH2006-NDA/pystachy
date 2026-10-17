# singletons as enum makes them (class C: ... then C = C()), for class_singleton
class _auto_null:
    def __repr__(self) -> str:
        return '_auto_null'
_auto_null = _auto_null()


class MISSING:
    def __repr__(self) -> str:
        return 'MISSING'

    def __bool__(self) -> bool:
        return False
MISSING = MISSING()


class Plain:
    pass
Plain = Plain()


class auto:
    def __init__(self, value=_auto_null):
        self.value = value

    def given(self) -> bool:
        return self.value is not _auto_null


def is_missing(x: object) -> bool:
    return x is MISSING
