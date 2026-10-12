import sys, warnings, threading, io, contextlib
warnings.simplefilter("always")
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    import fastmath as m
print("loaded", m.__file__.rsplit(".", 2)[-2] if m.__file__.endswith(".so") else "source", [str(x.message)[:60] for x in w])
print("gil", getattr(sys, "_is_gil_enabled", lambda: "n/a")())
print(m.fib(90), m.check(4))
for f in [lambda: m.check(-5), lambda: m.check(2**64), lambda: m.fib("x"), lambda: m.lookup("zz"),
          lambda: m.bad2(7), lambda: m.bye(3), lambda: m.quit_msg("so long"), lambda: m.quit_none(0)]:
    try:
        f()
    except BaseException as e:
        print("caught", type(e).__name__, repr(e.args), getattr(e, "code", "-"))
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    m.hello("captured")
print("redirected:", repr(buf.getvalue()))
r = []
def other():
    try:
        m.ncalls()
    except RuntimeError as e:
        r.append(type(e).__name__)
t = threading.Thread(target=other); t.start(); t.join()
print("other thread:", r)
