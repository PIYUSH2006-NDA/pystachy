"""Class layout addresses remain typed until LLVM lowering."""
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pystachy_compiler.gen import Gen
from src.pystachy_compiler.ir import ClassInfo, FnInfo, IFn, Ins, Val, Values
from src.pystachy_compiler.loader import Loader
from src.pystachy_compiler.specs import FXBIT
from src.pystachy_compiler.syntax import Node


def fixture():
    g = Gen()
    ci = ClassInfo("Box", Node("class", "Box", 1))
    ci.fields = ["value", "text", " inherited.flag"]
    ci.ftypes = {"value": "int", "text": "str", " inherited.flag": "bool"}
    ci.fpos = {name: i for i, name in enumerate(ci.fields)}
    ci.fflag = {"text": 3}
    ci.nflag = 1
    g.classes["Box"] = ci
    return g


def address(index=0, t="*int"):
    i = Ins("field.addr", t, "")
    i.k = index
    i.a = [Val("%a0", "Box")]
    i.r = [1]
    return i


def function(i):
    fn = IFn(FnInfo("fields", "@fields", Node("def", "fields", 1), ""))
    fn.n = 2
    fn.blocks[0].code = [i, Ins("ret.none", "", "")]
    return fn


class TypedFieldTests(unittest.TestCase):
    def test_fields_flags_and_exact_lowering(self):
        for index, t in enumerate(("*int", "*str", "*bool", "*bool")):
            with self.subTest(index=index):
                g = fixture()
                i = address(index, t)
                g.verify(function(i), False)
                self.assertEqual(g.nums(i), 1)
                self.assertEqual(g.opfx(i, {}), 0)
                g.lower_ins(function(i), i)
                self.assertEqual(g.out, [f"  %t1 = getelementptr %C.Box, ptr %a0, i32 0, i32 {index}"])

    def test_invalid_layout_index_type_shape_and_metadata(self):
        cases = [("k", -1), ("k", 4), ("t", "int"), ("t", "*float"),
                 ("s", "value"), ("x", "int"), ("b", ["entry"]),
                 ("a", []), ("a", [Val("%a0", "opt[Box]")]),
                 ("a", [Val("%a0", "Missing")]),
                 ("a", [Val("%a0", "Box"), Val("%a1", "Box")]),
                 ("r", []), ("r", [1, 2])]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                i = address()
                setattr(i, field, value)
                error = StringIO()
                with redirect_stderr(error), self.assertRaises(SystemExit):
                    fixture().verify(function(i), False)
                self.assertIn("field.addr", error.getvalue())

    def test_repeated_field_addresses_are_canonical(self):
        g = fixture()
        a = address()
        b = address()
        b.r = [2]
        fn = function(a)
        fn.blocks[0].code.insert(1, b)
        vs = Values(fn, {"entry": []})
        self.assertEqual(g.canon(vs, "%t1"), g.canon(vs, "%t2"))

    def test_field_addresses_keep_memory_effects(self):
        g = fixture()
        p = g.fgep(Val("%a0", "Box"), 1)
        self.assertEqual(g.fn.blocks[0].code[-1].t, "*str")
        load = Ins("mach.load", "%ptr", "")
        load.a = [Val(p, "%ptr")]
        store = Ins("mach.store", "", "")
        store.a = [Val(p, "%ptr"), Val("%a1", "%ptr")]
        self.assertEqual(g.opfx(load, g.fn.fa), FXBIT["rO"])
        self.assertEqual(g.opfx(store, g.fn.fa), FXBIT["wO"])

    def test_source_uses_typed_declared_layouts(self):
        root = Path(__file__).resolve().parent.parent / "tests"
        captured = []
        lower = Gen.lower

        def capture(g, fn):
            g.verify(fn, False)
            for b in fn.blocks:
                for i in b.code:
                    self.assertFalse(i.op == "raw" and "getelementptr %C." in i.s)
                    if i.op == "field.addr":
                        captured.append(i)
                        self.assertTrue(i.t.startswith("*"))
                        self.assertIn(i.a[0].t, g.classes)
            lower(g, fn)

        with patch.object(Gen, "lower", capture):
            for name in ("reference_union_inheritance.py", "typed_ir_slots.py"):
                Gen().program(Loader([]).program(name, (root / name).read_text()))
        self.assertTrue(captured)


if __name__ == "__main__":
    unittest.main()
