"""Typed container-slot conversions keep native types until LLVM lowering.

Run with python3 -m unittest discover -s tools -p test_typed_ir.py.
"""
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pystachy_compiler.gen import Gen
from src.pystachy_compiler.ir import FnInfo, IFn, Ins, Val
from src.pystachy_compiler.loader import Loader
from src.pystachy_compiler.syntax import Node


def slot_op(op, native_type="float"):
    i = Ins(op, "%slot" if op == "slot.pack" else native_type, "")
    i.a = [Val("%a0", native_type if op == "slot.pack" else "%slot")]
    i.r = [1]
    return i


def function_with(i):
    fn = IFn(FnInfo("slots", "@slots", Node("def", "slots", 1), ""))
    fn.n = 2
    fn.blocks[0].code = [i, Ins("ret.none", "", "")]
    return fn


class TypedSlotTests(unittest.TestCase):
    def assert_bad(self, i):
        error = StringIO()
        with redirect_stderr(error), self.assertRaises(SystemExit) as raised:
            Gen().verify(function_with(i), False)
        self.assertEqual(raised.exception.code, 1)
        self.assertIn("bad IR", error.getvalue())
        self.assertIn(i.op, error.getvalue())

    def test_valid_native_types_and_pure_effects(self):
        for t in ("int", "float", "bool", "None", "str", "bytes", "file",
                  "list[float]", "dict[str,bool]", "tuple[int,str]", "Box",
                  "opt[int]", "union[int,str]"):
            for op in ("slot.pack", "slot.unpack"):
                with self.subTest(type=t, op=op):
                    i = slot_op(op, t)
                    g = Gen()
                    g.verify(function_with(i), False)
                    self.assertEqual(g.nums(i), 1)
                    self.assertEqual(g.opfx(i, {}), 0)

    def test_requires_one_operand_and_one_result(self):
        for op in ("slot.pack", "slot.unpack"):
            for operands in ([], [Val("%a0", "float"), Val("%a1", "float")]):
                with self.subTest(op=op, operands=len(operands)):
                    i = slot_op(op)
                    i.a = operands
                    self.assert_bad(i)
            for results in ([], [1, 2]):
                with self.subTest(op=op, results=results):
                    i = slot_op(op)
                    i.r = results
                    self.assert_bad(i)

    def test_pack_result_and_unpack_operand_must_be_slots(self):
        for t in ("", "int", "float", "%double"):
            with self.subTest(type=t, op="slot.pack"):
                i = slot_op("slot.pack")
                i.t = t
                self.assert_bad(i)
            with self.subTest(type=t, op="slot.unpack"):
                i = slot_op("slot.unpack")
                i.a[0].t = t
                self.assert_bad(i)

    def test_rejects_empty_and_runtime_pseudo_types(self):
        for t in ("", "%slot", "%double", "#", "*T", "T", "K", "V", "S"):
            for op in ("slot.pack", "slot.unpack"):
                with self.subTest(type=t, op=op):
                    self.assert_bad(slot_op(op, t))

    def test_rejects_unused_metadata(self):
        for op in ("slot.pack", "slot.unpack"):
            for field, value in (("s", "LLVM text"), ("x", "float"), ("k", 1),
                                 ("b", ["entry"])):
                with self.subTest(op=op, field=field):
                    i = slot_op(op)
                    setattr(i, field, value)
                    self.assert_bad(i)

    def test_integer_slot_conversions_keep_the_same_value(self):
        g = Gen()
        original = Val("%a0", "int")
        self.assertEqual(g.to_slot(original), "%a0")
        unpacked = g.from_slot("%a0", "int")
        self.assertEqual((unpacked.v, unpacked.t), ("%a0", "int"))
        self.assertEqual(g.fn.blocks[0].code, [])

    def test_source_builds_typed_conversions_before_lowering(self):
        source = (Path(__file__).resolve().parent.parent / "tests" / "typed_ir_slots.py").read_text()
        captured = []
        lower = Gen.lower

        def capture(g, fn):
            g.verify(fn, False)
            captured.extend(i for b in fn.blocks for i in b.code
                            if i.op in ("slot.pack", "slot.unpack"))
            lower(g, fn)

        with patch.object(Gen, "lower", capture):
            Gen().program(Loader([]).program("typed_ir_slots.py", source))
        self.assertTrue(captured)
        for op in ("slot.pack", "slot.unpack"):
            types = {i.a[0].t if op == "slot.pack" else i.t
                     for i in captured if i.op == op}
            self.assertTrue({"float", "bool", "str", "None", "Box", "opt[float]",
                             "list[float]"}.issubset(types), (op, types))
            self.assertTrue(any("union[" in t for t in types), (op, types))
            self.assertNotIn("int", types)
        for i in captured:
            self.assertEqual((i.s, i.x, i.k, i.b), ("", "", 0, []))


if __name__ == "__main__":
    unittest.main()
