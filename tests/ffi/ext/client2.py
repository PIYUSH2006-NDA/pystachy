import fastmath as m


class S(str):
    pass


cases = [("fib(n=3)", lambda: m.fib(n=3)), ("fib()", lambda: m.fib()), ("fib(1, 2)", lambda: m.fib(1, 2)),
         ("fib(True)", lambda: m.fib(True)), ("fib(2**63)", lambda: m.fib(2**63)), ("fib(93)", lambda: m.fib(93)),
         ("scale(2, True)", lambda: m.scale(2, True)), ("scale(1.5, 1)", lambda: m.scale(1.5, 1)),
         ("scale('a', True)", lambda: m.scale("a", True)), ("shout(S('ab'))", lambda: m.shout(S("ab"))),
         ("shout(3)", lambda: m.shout(3)), ("check(-2**63)", lambda: m.check(-2**63)),
         ("big(91)", lambda: m.big(91))]
for label, f in cases:
    try:
        r = f()
        print(label, "->", type(r).__name__, r)
    except BaseException as e:
        print(label, "raises", type(e).__name__, e)
