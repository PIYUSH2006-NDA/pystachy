"""Generators component of the self-hosting Pystachy compiler.

A generator function compiles to an LLVM switched-resume coroutine (llvm.coro.*). The typed IR
marks where it starts (gen.start), suspends (gen.yield) and finishes (gen.ret); LLVM's coroutine
passes compute what lives across each yield, lay the frame out and outline the resume and
destroy functions (CoroSplit), and may put the frame of a generator a loop owns in the loop's
own frame (CoroElide). The frame comes from pys_alloc, which the collector scans; nothing frees
it (coro.free has nothing to do). A consumer resumes the handle (gen.resume) and reads the
promise (gen.promise): the value yielded, the state, the value returned. See
docs/internals.md#generators.
"""
from __future__ import annotations
from src.pystachy_compiler.analysis import closure_free
from src.pystachy_compiler.ir import Exit, FnInfo, Ins, IterArg, SeqStart, Try, Val
from src.pystachy_compiler.names import short
from src.pystachy_compiler.specs import (
    EXCBASES,
    GENCMD,
    GENDONE,
    GENNAME,
    GENRET,
    GENRUN,
    GENSTATE,
    exc_derives,
)
from src.pystachy_compiler.syntax import Node, has_kind, mk, names_in
from src.pystachy_compiler.utils import gelem, is_gen, typestr, unopt


def with_yield(body: list[Node]) -> bool:
    # does one of these statements yield inside a with block
    for st in body:
        if st.kind == "def" or st.kind == "class" or st.kind == "subclass" or st.kind == "lambda":
            continue
        if st.kind == "with" and has_kind(st.kids[-1], "yield"):
            return True
        for k in st.kids:
            if (k.kind == "block" and with_yield(k.kids)) or (k.kind == "except" and with_yield(k.kids[1].kids)):
                return True
    return False


def loop_yield(body: list[Node]) -> bool:
    # does one of these statements yield inside a for loop over a call (which may make a
    # generator the loop owns, closed where the loop is left)
    for st in body:
        if st.kind == "def" or st.kind == "class" or st.kind == "subclass" or st.kind == "lambda":
            continue
        if st.kind == "for" and has_kind(st.kids[2], "yield") and st.kids[1].kind != "list" and st.kids[1].kind != "tuple" and st.kids[1].kind != "str":
            return True
        for k in st.kids:
            if (k.kind == "block" and loop_yield(k.kids)) or (k.kind == "except" and loop_yield(k.kids[1].kids)):
                return True
    return False


def yields_from(n: Node) -> bool:
    # does n hold a yield from (outside the functions it defines)
    if n.kind == "yield" and n.s == "from":
        return True
    if n.kind == "def" or n.kind == "class" or n.kind == "subclass" or n.kind == "lambda":
        return False
    for k in n.kids:
        if yields_from(k):
            return True
    return False


def gen_gen_declare(self, f: FnInfo, d: Node) -> str:
    # generator function f (def d): its yield type (f.ret, gen[Y]) and return type (f.gret) from
    # its return annotation, or left for its calls to decide (a template); what closing it may
    # run (f.gclose, f.gwith). The error where Pystachy does not compile it, else ""
    f.gen = True
    body = d.kids[2].kids
    f.gwith = with_yield(body)
    f.gclose = f.gwith or yields_from(d.kids[2]) or loop_yield(body)
    for st in body:
        f.gtry = f.gtry or has_kind(st, "try")
    f.gclose = f.gclose or f.gtry
    if len(d.kids) > 3 and d.kids[3].s == "async":
        return "async generators are not supported"
    if d.kids[1].kind == "noann":
        f.generic = True  # (its first yield decides what it yields, for each call's argument types)
        f.ret = ""
        f.gret = ""
        return ""
    yr = self.gen_ann_ret(d.kids[1])
    if len(yr) == 1:
        return yr[0]
    f.ret = self.ctype("gen", [yr[0]])
    f.gret = yr[1]
    return ""


def gen_gen_ann_ret(self, n: Node) -> list[str]:
    # [Y, R] of a generator's return annotation n: Iterator[Y] or Iterable[Y] (R None),
    # Generator[Y, None, R] or Generator[Y] (typing's or collections.abc's); [why] where it is
    # no such annotation, or Pystachy does not support its types
    if n.kind == "str":
        n = self.parse_expr(n.s)
    base = self.typing_ref(n.kids[0]) if n.kind == "index" else ""
    if base != "Iterator" and base != "Iterable" and base != "Generator":
        return ["a generator function's return annotation must be Iterator[T], Iterable[T] or Generator[Y, None, R]"]
    a = n.kids[1].kids if n.kids[1].kind == "tuple" else [n.kids[1]]
    if base != "Generator" and len(a) != 1:
        return [f"{base}[...] takes one type: {base}[T]"]
    if base == "Generator" and len(a) != 1 and len(a) != 3:
        return ["Generator[...] takes three types: Generator[Y, S, R]"]
    if len(a) == 3 and a[1].kind != "None":
        return ["a generator whose send type is not None (Generator[Y, S, R]) is not supported: generators have no send()"]
    why = self.ann_problem(a[0], False) if a[0].kind != "None" else ""
    if why != "":
        return [why]
    r = "None"
    if len(a) == 3 and a[2].kind != "None":
        why = self.ann_problem(a[2], False)
        if why != "":
            return [why]
        r = self.ann(a[2])
    return ["None" if a[0].kind == "None" else self.ann(a[0]), r]


def gen_gen_name(self, f: FnInfo) -> str:
    # what CPython shows of f's generator objects: its __qualname__
    q = self.qualname(f)
    return q[: q.find("@")] if "@" in q else q


def gen_gen_begin(self, f: FnInfo) -> None:
    # the start of generator function f's code, its parameters stored: gen.start makes the
    # generator object (its frame, from pys_alloc) and suspends it before the first statement
    # (a call runs none of the body). With exceptions on, a landing block covers the body: what
    # leaves the body finishes the generator (gen_end)
    fn = self.fn
    fn.coro = True
    i = Ins("gen.start", "", "")
    i.a = [Val(self.sconst(self.gen_name(f)), "str")]
    first = self.label()
    i.b = [first]
    self.runtime("pys_alloc")
    self.add(i)
    self.term = True
    if self.eh:
        fn.gbase = self.alloca("int", "")
        if f.gwith:
            fn.gsaved = self.alloca("%ptr", "")
        if f.gtry:
            fn.gouter = self.alloca("exc", "")
            fn.ghand = self.alloca("exc", "")
        fn.gpad = self.label()
        tr = Try(first)
        tr.landing = fn.gpad
        fn.tries.append(tr)
        self.handler = fn.gpad
    self.place(first)
    self.gen_enter()


def gen_gen_enter(self) -> None:
    # where a generator resumes: the depth of the unwind actions now (its try statements' marks
    # are relative to it), on which those it set aside go back (pys_gen_enter)
    fn = self.fn
    if fn.gbase == "":
        return
    if fn.gsaved != "":
        b = self.rt("pys_gen_enter", "i64", [f"ptr {self.mload('%ptr', fn.gsaved)}"])
    else:
        b = self.rt("pys_try_mark", "i64", [])
    self.mstore("int", b, fn.gbase)
    if fn.gouter != "":
        # (the exception its resumer handles, which it handles again at its next suspend; a
        # yield in an except clause or a finally block handles its own again)
        self.mstore("%ptr", self.rt("pys_exc_handled", "ptr", []), fn.gouter)
        if len(self.excs) > 0:
            self.rt("pys_exc_restore", "void", [f"ptr {self.mload('%ptr', fn.ghand)}"])


def gen_gen_end(self, f: FnInfo) -> None:
    # the end of generator function f's code: falling off its end finishes it. Its landing block
    # (exceptions on): an exception that leaves its body finishes it too. Closed by its loop (a
    # command, gen.drop), the GeneratorExit raised at its yield ends it, and anything else is
    # reported as CPython reports an exception it ignores; else the exception goes on, a
    # StopIteration as RuntimeError (PEP 479)
    fn = self.fn
    if not self.term:
        self.gen_none_end()
        self.gen_ret(Val("null", "None"))
    if f.ret == "":
        f.ret = "gen[None]"  # (no yield is reached: it yields nothing)
    if f.gret == "":
        f.gret = "None"
    elif fn.gnone and f.gret != "None" and f.node.kids[1].kind == "noann":
        f.gret = self.optional(f.gret)  # (it also ends without a value: R | None, the same pointer)
    if fn.gpad != "":
        self.handler = ""
        slot = self.alloca("exc", "")
        e = self.landing(fn.gpad, slot, Val("0", "int"))
        p = self.gen_promise(Val("", ""))
        self.mstore("int", str(GENDONE), self.maddr("int", p, str(GENSTATE)))
        cmd = self.mload("int", self.maddr("int", p, str(GENCMD)))
        lc = self.label()
        lp = self.label()
        self.cbr(self.num_cmp("!=", Val(cmd, "int"), Val("0", "int")).v, lc, lp)
        self.place(lc)
        lf = self.label()
        lr = self.label()
        self.cbr(self.exc_match(e, self.builtin_catch("GeneratorExit")), lf, lr)
        self.place(lr)
        name = self.mload("%ptr", self.maddr("int", p, str(GENNAME)))
        self.rt("pys_gen_unraisable", "void", [f"ptr {e.v}", f"ptr {name}", f"ptr {p}"])
        self.br(lf)
        self.place(lf)
        self.gen_ret(Val("null", "None"))
        self.place(lp)
        ls = self.label()
        lo = self.label()
        self.cbr(self.exc_match(e, self.builtin_catch("StopIteration")), ls, lo)
        self.place(ls)
        self.raise_("RuntimeError", self.sconst("generator raised StopIteration"))
        self.place(lo)
        self.throw(e)
    f.noret = False


def gen_builtin_catch(self, b: str) -> str:
    # the classes an except clause naming builtin exception class b catches (catch_set)
    out: list[str] = []
    for k in EXCBASES:
        if exc_derives(k, b):
            out.append(k)
    for k in self.classes:
        if self.classes[k].exc != "" and self.derives(k, b):
            out.append(k)
    return "\x01" + "\x01".join(out) + "\x01"


def gen_gen_promise(self, h: Val) -> str:
    # the address of the promise of generator h ("": the generator being compiled's own)
    i = Ins("gen.promise", "%ptr", "")
    if h.v != "":
        i.a = [h]
    self.put(i, 1)
    return f"%t{i.r[0]}"


def gen_gen_unhandle(self) -> None:
    # before the generator being compiled suspends: the exception being handled is its resumer's
    # again (in an except clause or a finally block, its own is kept for where it resumes)
    fn = self.fn
    if fn.gouter == "":
        return
    if len(self.excs) > 0:
        self.mstore("%ptr", self.rt("pys_exc_handled", "ptr", []), fn.ghand)
    self.rt("pys_exc_restore", "void", [f"ptr {self.mload('%ptr', fn.gouter)}"])


def gen_gen_ret(self, v: Val) -> None:
    # the generator being compiled finishes, returning v: its final suspend
    self.gen_unhandle()
    i = Ins("gen.ret", "", "")
    if v.t != "None":
        i.a = [Val(self.to_slot(v), "%slot")]
    self.put(i, 2)
    self.term = True


def gen_gen_none_end(self) -> None:
    # the generator ends without a value here (return, or the end of its code): the value of a
    # yield from that delegates to it is None, which its return type must hold. An unannotated
    # one returning a reference type R elsewhere returns R | None (the same null pointer); one
    # returning a number would need a box: an error
    f = self.curfn
    r = f.gret
    if r != "" and r != "None" and self.optional(r) != r and (f.node.kids[1].kind != "noann" or not self.none_null(r)):
        self.err(f"{short(f.name)}() returns {typestr(r)} and ends without a value elsewhere: annotate it Generator[Y, None, {typestr(r)} | None]" if f.node.kids[1].kind != "noann" else f"{short(f.name)}() returns {typestr(r)} and ends without a value elsewhere, which the value of yield from cannot hold: return a value on every path, or annotate it Generator[Y, None, {typestr(r)} | None]")
    self.fn.gnone = True


def gen_none_null(self, t: str) -> bool:
    # is t | None the same pointer as t, None being null (str, containers, tuples; not numbers)
    o = self.optional(t)
    return o != "" and (o == t or not self.isnum(t))


def gen_gen_return(self, n: Node) -> None:
    # return [v] in a generator: it finishes, with v the value of the yield from that delegates to it
    f = self.curfn
    v = Val("null", "None")
    if len(n.kids) > 0 and n.kids[0].kind != "None":
        r = f.gret
        if r == "None":
            self.err(f"{short(f.name)}() is annotated to return no value (Iterator[T], Iterable[T] or Generator[Y, None, None]): annotate it Generator[Y, None, R] to return one")
        v = self.expr(n.kids[0], r)
        if r == "":
            if v.t == "None" or "?" in v.t:
                self.err(f"cannot infer what {short(f.name)}() returns from {typestr(v.t)}; annotate it Generator[Y, None, R]")
            if self.fn.gnone and self.optional(v.t) != v.t and not self.none_null(v.t):
                self.err(f"{short(f.name)}() returns {typestr(v.t)} and ends without a value elsewhere, which the value of yield from cannot hold: return a value on every path, or annotate it Generator[Y, None, {typestr(v.t)} | None]")
            f.gret = v.t
        else:
            v = self.coerce(v, r)
    else:
        self.gen_none_end()
    self.carried = v  # (the value first: a finally block runs after it is computed)
    ended = self.leave(0)
    v = self.carried
    self.carried = Val("", "")
    if not ended:
        self.gen_ret(v)
    self.term = True


def gen_gen_cleanup(self) -> int:
    # 1 where closing the generator being compiled runs code of its (GeneratorExit raised here
    # reaches a try statement, a with block or a loop that owns a generator), else 0: with
    # exceptions off, nothing can
    if not self.eh:
        return 0
    if self.handler != self.fn.gpad:
        return 1
    for x in self.exits:
        if x.kind == "with":
            return 1
    return 0


def gen_gen_suspend(self, slot: str, k: int, sub: Val) -> None:
    # the generator being compiled yields the value in slot, then goes on where it is resumed.
    # k: closing it here runs code of its (gen_cleanup), so a close raises GeneratorExit here,
    # having closed sub first, the generator a yield from delegates to (or none: Val("", ""))
    fn = self.fn
    if fn.gsaved != "":
        sv = self.rt("pys_gen_leave", "ptr", [f"i64 {self.mload('int', fn.gbase)}"])
        self.mstore("%ptr", sv, fn.gsaved)
    self.gen_unhandle()
    res = self.label()
    i = Ins("gen.yield", "", "")
    i.a = [Val(slot, "%slot")]
    i.k = k
    i.b = [res]
    self.put(i, 2)
    self.term = True
    self.place(res)
    self.gen_enter()
    if k == 1:
        p = self.gen_promise(Val("", ""))
        cmd = self.mload("int", self.maddr("int", p, str(GENCMD)))
        lx = self.label()
        lgo = self.label()
        self.cbr(self.num_cmp("!=", Val(cmd, "int"), Val("0", "int")).v, lx, lgo)
        self.place(lx)
        if sub.v != "":
            self.gen_drop(sub)
        self.raise_("GeneratorExit", self.sconst(""))
        self.place(lgo)


def gen_yield_stmt(self, n: Node) -> None:
    # yield v as a statement (its value, None as next() resumes it, is dropped), or yield from x
    f = self.curfn
    if not f.gen:
        self.err("'yield' outside function")
    if n.s == "from":
        self.yield_from(n.kids[0])
        return
    y = gelem(f.ret) if f.ret != "" else ""
    v = self.expr(n.kids[0], y) if len(n.kids) > 0 else Val("null", "None")
    if y == "":
        if "?" in v.t:
            self.err(f"cannot infer what {short(f.name)}() yields from an empty {typestr(v.t)}; annotate it -> Iterator[T]")
        y = v.t
        f.ret = self.ctype("gen", [y])
    elif v.t != y:
        v = self.coerce(v, y)
    self.gen_suspend("0" if y == "None" else self.to_slot(v), self.gen_cleanup(), Val("", ""))


def gen_yield_from(self, x: Node) -> Val:
    # yield from x: x a generator, delegated to until it finishes (its return value is the
    # result), else any iterable, each item of which is yielded (the result is None)
    f = self.curfn
    if not f.gen:
        self.err("'yield' outside function")
    y = gelem(f.ret) if f.ret != "" else ""
    if x.kind == "listcomp" and x.s == "gen":
        # yield from (e for t in it if c): each e, as the loop the generator expression is would
        # make it (its first iterable at once, the rest as it goes on; t its own variable)
        names: list[str] = []
        names_in(x.kids[1], names)
        body = [mk("expr", "", x.line, [mk("yield", "", x.line, [x.kids[0]])])]
        if len(x.kids) == 4:
            body = [mk("if", "", x.line, [x.kids[3], mk("block", "", x.line, body), mk("block", "", x.line, [])])]
        self.hidden_loop(mk("for", "", x.line, [x.kids[1], x.kids[2], mk("block", "", x.line, body)]), names)
        return Val("null", "None")
    self.gencall = ""
    v = self.expr(x, "")
    callee = self.gencallf if v.v == self.gencall and self.gencall != "" else None
    if not is_gen(v.t):
        it = mk("name", "__yf", x.line, [])
        self.hidden_loop(mk("for", "", x.line, [it, self.vnode(v), mk("block", "", x.line, [mk("expr", "", x.line, [mk("yield", "", x.line, [mk("name", "__yf", x.line, [])])])])]), ["__yf"])
        return Val("null", "None")
    t = gelem(v.t)
    if y == "":
        y = t
        f.ret = self.ctype("gen", [y])
    if t != y and not self.widens(t, y):
        self.err(f"{short(f.name)}() yields {typestr(y)}, but yield from delegates to a generator that yields {typestr(t)}")
    head = self.label()
    done = self.label()
    self.br(head)
    self.place(head)
    p = self.gen_next(v, done)
    s = self.mload("int", p)
    if t != y:
        s = self.to_slot(self.coerce(self.from_slot(s, t), y))
    self.gen_suspend(s, 1 if self.eh else 0, v if self.eh else Val("", ""))
    self.br(head)
    self.place(done)
    r = callee.gret if callee is not None else ""
    res = Val("null", "None") if r == "None" else Val("", "")
    if r != "" and r != "None":
        pr = self.gen_promise(v)
        res = self.from_slot(self.mload("int", self.maddr("int", pr, str(GENRET))), r)
    if callee is not None:
        self.gen_drop(v)  # (it has finished: destroyed, LLVM may put its frame in this one's)
    return res


def gen_hidden_loop(self, loop: Node, names: list[str]) -> None:
    # for loop loop, whose variables names are its own, as a comprehension's are (listcomp)
    saved: list[str] = []
    for nm in names:
        saved.append(self.ltype.get(nm, "") + " " + self.lreg.get(nm, ""))
    pre = self.narrowed
    self.for_(loop, names)
    self.narrowed = pre
    for i in range(len(names)):
        nm = names[i]
        sp = saved[i].find(" ")
        if sp == 0:
            if nm in self.ltype:
                del self.ltype[nm]
        else:
            self.ltype[nm] = saved[i][:sp]
            self.lreg[nm] = saved[i][sp + 1 :]
        self.compvars[nm] -= 1
        if self.compvars[nm] == 0:
            del self.compvars[nm]


def gen_gen_next(self, h: Val, done: str) -> str:
    # the next step of generator h: done if it has finished (so a finished generator is never
    # resumed), else it is resumed (a ValueError if it is running: it resumed itself), and done
    # if it finishes then. The address of its promise, where the value it yielded is
    p = self.gen_promise(h)
    st = self.maddr("int", p, str(GENSTATE))
    s0 = self.mload("int", st)
    go = self.label()
    self.cbr(self.num_cmp("==", Val(s0, "int"), Val(str(GENDONE), "int")).v, done, go)
    self.place(go)
    self.guard(self.num_cmp("==", Val(s0, "int"), Val(str(GENRUN), "int")).v, "ValueError: generator already executing")
    self.mstore("int", str(GENRUN), st)
    i = Ins("gen.resume", "", "")
    i.a = [h]
    self.add(i)
    s1 = self.mload("int", st)
    got = self.label()
    self.cbr(self.num_cmp("==", Val(s1, "int"), Val(str(GENDONE), "int")).v, done, got)
    self.place(got)
    return p


def gen_gen_drop(self, h: Val) -> None:
    # generator h, which a loop owns, is left: closed (where it is suspended in a try statement,
    # a with block or a loop of its own: GeneratorExit is raised there), and destroyed
    i = Ins("gen.drop", "", "")
    i.a = [h]
    self.runtime("pys_exc_handled")
    self.runtime("pys_exc_restore")
    self.runtime("pys_gen_ignored")
    self.add(i)


def gen_owned_gen(self, v: Val, it: Node) -> int:
    # does a loop over v, the value of node it, own it: a generator that a call of a generator
    # function (or an __iter__ that is one) has just made (or a val node of one, gen_owned_node).
    # 0: no; 1: yes; 2: yes, and closing it may run code of its (with exceptions on)
    if not is_gen(v.t):
        return 0
    f = self.gencallf if self.gencall != "" and v.v == self.gencall else self.vowned[it.s] if it.kind == "val" and it.s in self.vowned else None
    if it.kind == "name" and it.s == ".0" and self.curfn.gfirst is not None:
        f = self.curfn.gfirst  # (a generator expression's first iterable, a generator it alone holds)
    if f is None:
        return 0
    return 2 if self.eh and f.gclose else 1


def gen_owned_node(self, v: Val) -> Node:
    # a val node of v, a value just computed: if it is a generator that a loop over it owns
    # (owned_gen), so does the loop over this node
    own = self.gencallf if is_gen(v.t) and self.gencall != "" and v.v == self.gencall else None
    n = self.vnode(v)
    if own is not None:
        self.vowned[n.s] = own
    return n


def gen_owned_loop(self, owned: list[Val], close: bool, tgt: Node, seqs: list[Val], mode: str, body: list[Node], start: str, hide: list[str], arg: IterArg | None, made: SeqStart | None) -> None:
    # a for loop over generators it owns (owned, made just now by calls), which are dropped
    # (gen.drop: closed, the last first, then destroyed) where the loop is left: at its end, at
    # break and at return, before the code after it, as CPython closes them once the loop drops
    # them; with close (one may run code as it closes, gen_cleanup), also where an exception
    # leaves the body: the loop is the body of a try statement whose finally block drops them.
    # (Destroyed on every way out, LLVM's CoroElide may put their frames in this function's.)
    drops = [mk("gendrop", "", self.line, [self.vnode(owned[j])]) for j in range(len(owned) - 1, -1, -1)]
    mark = Val("", "")
    slot = ""
    outer = self.handler
    hf = ""
    if close:
        mark = Val(self.rt("pys_try_mark", "i64", []), "int")
        if self.fn.gbase != "":
            mark = Val(self.scalar("sub", [mark, Val(self.mload("int", self.fn.gbase), "int")]), "int")
        slot = self.alloca("exc", "")
        hf = self.label()
    fx = Exit("finally", "", outer)
    fx.body = drops
    fx.nloops = len(self.loops)
    fx.nexcs = len(self.excs)
    self.exits.append(fx)
    tr = Try(self.label())
    if close:
        tr.final = hf
        self.fn.tries.append(tr)
        self.handler = hf
    ek = self.elsekids
    eb = self.elsebrk
    brk = ""
    if body is self.elsekids:
        # (for ... else: break skips the else block, which runs after the loop's end: it drops them first)
        brk = self.label()
        self.elsebrk = brk
    self.place(tr.body)
    self.for_seq(tgt, seqs, mode, body, start, hide, arg, made)
    self.elsekids = ek
    self.elsebrk = eb
    self.exits.pop()
    self.handler = outer
    tr.exit = self.label()
    if not self.term:
        self.stmts(drops)
    self.br(tr.exit)
    if brk != "":
        self.place(brk)
        self.stmts(drops)
        self.br(eb)
    if close:
        e = self.landing(hf, slot, mark)
        self.stmts(drops)
        self.throw(e)
    self.place(tr.exit)


def gen_gen_list(self, v: Val, want: str) -> Val:
    # the items of generator v, as a fresh list (list(g), sorted(g), "".join(g), ...)
    it = mk("name", "__item", self.line, [])
    return self.listcomp(mk("listcomp", "", self.line, [it, mk("name", "__item", self.line, []), self.vnode(v)]), want if want != "" else self.ctype("list", [gelem(v.t)]))


def gen_gen_stream(self, name: str, v: Val, args: list[Node], want: str, resultsoft: bool) -> Val:
    # sum(g), min(g), max(g), any(g), all(g), ... of generator v: of the generator expression
    # (x for x in g), whose items they take as they come (any() and all() stop at the deciding one)
    it = mk("name", "__item", self.line, [])
    g = mk("listcomp", "gen", self.line, [it, mk("name", "__item", self.line, []), self.owned_node(v)])
    return self.builtin(name, [g] + args, want, resultsoft)


def gen_gen_contains(self, x: Val, g: Val) -> Val:
    # x in g of generator g: it is iterated until an item equals x (CPython's == of the item and x)
    gn = self.owned_node(g)
    item = mk("name", "__item", self.line, [])
    test = mk("cmp", "==", self.line, [mk("name", "__item", self.line, []), self.vnode(x)])
    return self.builtin("any", [mk("listcomp", "gen", self.line, [test, item, gn])], "bool")


def gen_gen_method(self, o: Val, m: str, args: list[Node]) -> Val:
    # o.m(args) of generator o: __next__() is next(o), __iter__() o itself
    if m == "send" or m == "throw" or m == "close":
        self.err(f"generator.{m}() is not supported: generators have no send(), throw() or close() (for loops, yield from, next() and the functions that take an iterable run them)")
    if m == "__next__" and len(args) == 0:
        return self.gen_next_value(o, Val("", ""))
    if m == "__iter__" and len(args) == 0:
        return o
    self.err(f"'generator' object has no attribute '{m}'")
    return o


def gen_gen_next_value(self, g: Val, dflt: Val) -> Val:
    # next(g) of generator g: the value it yields next; where it has finished, dflt (next(g, d))
    # if given (Val("", "") if not), else StopIteration (in a generator with exceptions off,
    # which nothing in it can catch, PEP 479's RuntimeError at once)
    y = gelem(g.t)
    done = self.label()
    p = self.gen_next(g, done)
    v = self.from_slot(self.mload("int", p), y)
    t = y if dflt.v == "" else self.join(y, dflt.t)
    if t == "":
        self.err(f"next() of a generator of {typestr(y)} with a default of {typestr(dflt.t)}: they need one type")
    if dflt.v != "":
        v = self.coerce(v, t)
    got = self.cur
    end = self.label()
    self.br(end)
    self.place(done)
    if dflt.v == "":
        if self.curfn.gen and not self.eh:
            self.raise_("RuntimeError", self.sconst("generator raised StopIteration"))
        else:
            self.raise_("StopIteration", self.sconst(""))
        self.place(end)
        return v
    d = self.coerce(dflt, t)
    dl = self.cur
    self.br(end)
    self.place(end)
    if t == "None":
        return Val("null", "None")
    ph = Ins("phi", t, "")
    self.incoming(ph, v.v, got)
    self.incoming(ph, d.v, dl)
    return Val(self.phi(ph), t)


def binds(n: Node, x: str, loop: bool) -> int:
    # how often code n binds name x as a local of its function: 2 where it may bind it again (in a
    # loop, a for loop's target, a global or nonlocal declaration), not counting the functions,
    # lambdas, classes and comprehensions it defines (but a def's or class's own name)
    k = n.kind
    if k == "def" or k == "class" or k == "subclass":
        return (2 if loop else 1) if n.s == x else 0
    if k == "lambda" or k == "listcomp" or k == "setcomp" or k == "dictcomp" or k == "nestedcomp":
        return 0
    if (k == "global" or k == "nonlocal") and len([g for g in n.kids if g.s == x]) > 0:
        return 2
    tg: list[Node] = []
    if k == "assign":
        tg = n.kids[:-1]
    elif k == "annassign" or k == "augassign" or k == "for" or k == "walrus":
        tg = [n.kids[0]]
    elif k == "with":
        tg = [it.kids[1] for it in n.kids[:-1] if len(it.kids) == 2]
    elif k == "del":
        tg = n.kids
    names: list[str] = []
    for t in tg:
        names_in(t, names)
    c = len([nm for nm in names if nm == x])
    if (k == "except" and n.s == x) or (k == "import" and len([a for a in n.kids if a.s == x]) > 0):
        c += 1
    if c > 0 and (loop or k == "for"):
        return 2
    for kid in n.kids:
        c += binds(kid, x, loop or k == "for" or k == "while")
        if c > 1:
            return 2
    return c


def maybe_unbound(n: Node, x: str) -> bool:
    # does code n read x where Flow found it may be unassigned (Node.chk)
    if n.kind == "name" and n.s == x and n.chk:
        return True
    for k in n.kids:
        if maybe_unbound(k, x):
            return True
    return False


def gen_genexp_value(self, n: Node) -> Val:
    # a generator expression (e for t in it if c) as a value: an anonymous generator function, as
    # CPython's (never a list): it is evaluated here, the rest where the generator runs. The
    # variables of this function it reads are passed to it as they are now, which is what they
    # hold when it runs: each is a parameter never bound again or a local bound once (outside any
    # loop), surely assigned here; another (a comprehension's, one bound again) is an error
    line = n.line
    noann = mk("noann", "", line, [])
    yld = mk("expr", "", line, [mk("yield", "", line, [n.kids[0]])])
    body = [yld]
    if len(n.kids) == 4:
        body = [mk("if", "", line, [n.kids[3], mk("block", "", line, body), mk("block", "", line, [])])]
    # its first iterable: a value made here, or range(), enumerate(), zip() or reversed() of
    # arguments evaluated here (those are no values: the generator's loop makes them)
    first = n.kids[2]
    ps: list[Node] = [mk("param", ".0", line, [noann, noann])]
    itn = mk("name", ".0", line, [])
    if self.iterator_call(first):
        ps = []
        cargs: list[Node] = []
        for j in range(len(first.kids) - 1):
            a = first.kids[j + 1]
            ps.append(mk("param", f".{j}", line, [noann, noann]))
            cargs.append(mk("kw", a.s, line, [mk("name", f".{j}", line, [])]) if a.kind == "kw" else mk("name", f".{j}", line, []))
        itn = mk("call", "", line, [first.kids[0]] + cargs)
    loop = mk("for", "", line, [n.kids[1], itn, mk("block", "", line, body)])
    d = mk("def", "<genexpr>", line, [mk("params", "0,-1", line, ps), noann, mk("block", "", line, [loop])])
    free: dict[str, bool] = {}
    closure_free(d, free)
    f = self.curfn
    fbody = f.node.kids[2].kids if f.node.kind == "def" else f.node.kids
    caps: list[str] = []
    for x in free:
        if x in self.compvars:
            self.err(f"a generator expression that reads '{x}', a variable of a comprehension around it, is not supported (it would read the variable's last value when it runs)")
        if not self.modlevel and x in self.ltype and not (x in self.assigned or x in f.params):
            self.err(f"a generator expression that reads '{x}', a variable of a function around {short(f.name)}(), is not supported")
        if self.modlevel or not (x in self.assigned or x in f.params):
            continue  # (a global, read where the generator runs)
        nb = 0
        for st in fbody:
            nb += binds(st, x, False)
        if nb > (0 if x in f.params and x not in self.assigned else 1) or x in self.nlw or maybe_unbound(n, x):
            self.err(f"a generator expression that reads '{x}' is not supported where {short(f.name)}() may bind it again, or it may be unbound, before the generator runs (a generator expression reads it then)")
        caps.append(x)
    caps.sort()
    for x in caps:
        d.kids[0].kids.append(mk("param", x, line, [noann, noann]))
    firsts: list[Node] = []
    own: FnInfo | None = None
    if self.iterator_call(first):
        for a in first.kids[1:]:
            firsts.append(self.vnode(self.expr(a.kids[0] if a.kind == "kw" else a, "")))
    else:
        self.gencall = ""
        it = self.iterable(self.expr(first, ""))  # (made here)
        if self.owned_gen(it, first) > 0:
            own = self.gencallf  # (a generator it alone holds: its loop owns it)
        firsts.append(self.vnode(it))
    g = self.declare_fn(d, "")
    self.ngenexp += 1
    g.ll = f"@f.genexpr.{self.ngenexp}"
    g.mod = f.mod
    g.gfirst = own
    return self.call_fn(g, [], firsts + [mk("name", x, line, []) for x in caps])
