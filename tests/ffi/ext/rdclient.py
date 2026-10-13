import io, sys
import rd

sys.stdin = io.StringIO("one\ntwo\nthree\nfour\n")
print("host:", input())
print("module:", rd.ask("name? "))
print("module line:", repr(rd.line()))
print("host line:", repr(sys.stdin.readline()))
print("module rest:", repr(rd.rest()))
try:
    rd.ask("")
except EOFError as e:
    print("caught EOFError", e)
old = sys.stdout
sys.stdout = None
rd.shout("not printed")
sys.stdout = old
rd.shout("printed")


# an exception sys.stdout raises outside Exception stays outside it, and a SystemExit keeps its code
class Exits:
    def __init__(self, code: object) -> None:
        self.code = code

    def write(self, s: str) -> int:
        raise SystemExit(self.code)

    def flush(self) -> None:
        pass


for code in (7, None, "bye", True):
    sys.stdout = Exits(code)
    try:
        rd.shout("exit")
    except Exception:
        sys.stdout = old
        print("caught as an Exception")
    except SystemExit as e:
        sys.stdout = old
        print("SystemExit", repr(e.code), e.args)


class Stop(BaseException):
    pass


class Halts:
    def __init__(self, e: BaseException) -> None:
        self.e = e

    def write(self, s: str) -> int:
        raise self.e

    def flush(self) -> None:
        pass


for e in (Stop("halt"), GeneratorExit("gen")):
    sys.stdout = Halts(e)
    try:
        rd.shout("halt")
    except Exception:
        sys.stdout = old
        print("caught as an Exception")
    except BaseException as x:
        sys.stdout = old
        print("BaseException", isinstance(x, Exception), isinstance(x, GeneratorExit), x)
