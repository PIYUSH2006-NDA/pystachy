"""Typed operations keep native types until LLVM lowering.

Run with python3 -m unittest discover -s tools -p test_typed_ir.py.
"""
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pystachy_compiler import diagnostics
from src.pystachy_compiler.gen import Gen
from src.pystachy_compiler.ir import FnInfo, IFn, Ins, Val
from src.pystachy_compiler.loader import Loader
from src.pystachy_compiler.specs import FXBIT
from src.pystachy_compiler.syntax import Node
from src.pystachy_compiler.utils import targs, typestr, umembers


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


def union_op(op, union_type="union[int,str]"):
    i = Ins(op, "int" if op == "union.tag" else "%slot",
            "" if op == "union.tag" else "str")
    i.a = [Val("%a0", union_type)]
    i.r = [1] if op == "union.tag" else [1, 2]
    return i


def cast_op(source="bool", target="float"):
    i = Ins("num.cast", target, "")
    i.a = [Val("%a0", source)]
    i.r = [1]
    return i


def compare_op(t="int", predicate="=="):
    i = Ins("num.cmp", "bool", predicate)
    i.a = [Val("%a0", t), Val("%a1", t)]
    i.r = [1]
    return i


class ClosurePathTests(unittest.TestCase):
    def test_paths_do_not_change_tuple_layouts_or_closure_types(self):
        fixture = Path(__file__).resolve().parent.parent / "tests/paths]/closure_path_fixture.py"
        source = fixture.read_text() + "\nprint(checks(1))\n"
        expected_ir = None
        for directory in ("ordinary", "x]y", "c[d", "a],b[c", "[id]", "a,b",
                          "a%5Bb", "a?b", "a|b", "é[%,]"):
            path = directory + "/closures.py"
            with self.subTest(path=path), patch.object(diagnostics, "SRC", path), \
                    patch.object(diagnostics, "FILES", []):
                g = Gen()
                ir = g.program(Loader([]).program(path, source))
                if expected_ir is None:
                    expected_ir = ir
                self.assertEqual(ir, expected_ir)
                for closure in g.closures:
                    self.assertNotIn(directory, closure.t)
                    self.assertTrue(closure.t.rsplit("@", 1)[1][:-1].isdigit())
                    self.assertIn(path + ":", typestr(closure.t))
                    self.assertEqual(targs(g.ctype("tuple", [closure.t, "int"])),
                                     [closure.t, "int"])

    def test_imported_closure_diagnostic_resolves_original_path(self):
        path = "a],b[c/é%module.py"
        with patch.object(diagnostics, "FILES", ["main.py", path]):
            self.assertEqual(typestr("fn[c:0:outer.<locals>.g@10000002]"),
                             "<function outer.<locals>.g (" + path + ":2)>")

    def test_tuple_round_trip_check_is_always_on(self):
        error = StringIO()
        g = Gen()
        g.line = 12
        with patch.object(diagnostics, "SRC", "guard.py"), redirect_stderr(error), \
                self.assertRaises(SystemExit) as raised:
            g.ctype("tuple", ["fn[c:0:g@bad]path:2]", "int"])
        self.assertEqual(raised.exception.code, 1)
        self.assertEqual(error.getvalue(),
                         "guard.py:12: error: internal error: tuple item types do not round-trip\n")


class TypedIRTests(unittest.TestCase):
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

    def test_empty_result_layout_keeps_heap_write_effect(self):
        for t in ("dict[str,int]", "set[tuple[str,int]]"):
            i = Ins("empty.kind", "", "")
            i.a = [Val("%a0", t)]
            i.r = [1]
            g = Gen()
            g.verify(function_with(i), False)
            self.assertEqual(g.opfx(i, {}), FXBIT["wD"])
            g.holes.append(t)
            i.k = 1
            i.a[0].t = "dict[?,?]" if t.startswith("dict[") else "set[?]"
            g.verify(function_with(i), False)

    def test_empty_result_layout_rejects_bad_operands_and_holes(self):
        for t in ("list[int]", "int", "opt[dict[str,int]]", "dict[?,?]"):
            i = Ins("empty.kind", "", "")
            i.a = [Val("%a0", t)]
            i.r = [1]
            self.assert_bad(i)
        for field, value in (("a", []), ("a", [Val("%a0", "dict[str,int]")] * 2),
                             ("r", []), ("r", [1, 2]), ("k", -1), ("k", 1),
                             ("t", "dict[str,int]"), ("s", "raw"), ("x", "str"),
                             ("b", ["entry"])):
            i = Ins("empty.kind", "", "")
            i.a = [Val("%a0", "dict[str,int]")]
            i.r = [1]
            setattr(i, field, value)
            self.assert_bad(i)

    def test_empty_result_layout_rejects_invalid_resolved_holes(self):
        for t in ("int", "list[int]", "set[str]", "dict[?,int]"):
            i = Ins("empty.kind", "", "")
            i.a = [Val("%a0", "dict[?,?]")]
            i.r = [1]
            i.k = 1
            g = Gen()
            g.holes.append(t)
            error = StringIO()
            with redirect_stderr(error), self.assertRaises(SystemExit):
                g.verify(function_with(i), False)
            self.assertIn("concrete hole", error.getvalue())

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

    def test_union_reads_keep_conservative_load_effects(self):
        for t in ("union[int,str]", "union[bool,float,int,str]"):
            for op in ("union.tag", "union.payload"):
                with self.subTest(type=t, op=op):
                    i = union_op(op, t)
                    g = Gen()
                    g.verify(function_with(i), False)
                    self.assertEqual(g.nums(i), 1 if op == "union.tag" else 2)
                    self.assertEqual(g.opfx(i, {}), FXBIT["rL"] | FXBIT["rD"] | FXBIT["rO"])

    def test_union_reads_require_closed_nonoptional_operands(self):
        for t in ("", "int", "%slot", "opt[union[int,str]]", "union[]", "union[int]",
                  "union[int,str", "union[int,str]]", "union[int,]", "union[,str]",
                  "union[int,int]", "union[int,None]", "union[int,opt[str]]",
                  "union[int,union[bool,str]]", "union[int,%slot]", "union[int,*T]"):
            for op in ("union.tag", "union.payload"):
                with self.subTest(type=t, op=op):
                    self.assert_bad(union_op(op, t))

    def test_union_read_shapes_and_metadata(self):
        for op in ("union.tag", "union.payload"):
            for operands in ([], [Val("%a0", "union[int,str]")] * 2):
                with self.subTest(op=op, operands=len(operands)):
                    i = union_op(op)
                    i.a = operands
                    self.assert_bad(i)
            for results in ([], [1, 2] if op == "union.tag" else [1]):
                with self.subTest(op=op, results=results):
                    i = union_op(op)
                    i.r = results
                    self.assert_bad(i)
            for field, value in (("x", "int"), ("k", 1), ("b", ["entry"]),
                                 ("t", "%slot" if op == "union.tag" else "int")):
                with self.subTest(op=op, field=field):
                    i = union_op(op)
                    setattr(i, field, value)
                    self.assert_bad(i)
        for member in ("", "float", "opt[str]", "%slot"):
            with self.subTest(member=member):
                i = union_op("union.payload")
                i.s = member
                self.assert_bad(i)
        i = union_op("union.tag")
        i.s = "str"
        self.assert_bad(i)

    def test_optional_union_tag_stays_after_its_null_guard(self):
        g = Gen()
        g.utest(Val("%a0", "opt[union[int,str]]"), ["str"], True)
        tags = [(b, i) for b in g.fn.blocks for i in b.code if i.op == "union.tag"]
        self.assertEqual(len(tags), 1)
        block, i = tags[0]
        self.assertEqual(i.a[0].t, "union[int,str]")
        guard = g.fn.blocks[0].code[-1]
        self.assertEqual(guard.op, "cbr")
        self.assertEqual(guard.b[1], block.label)
        self.assertNotEqual(guard.b[0], block.label)
        self.assertIn("icmp eq ptr %a0, null", g.fn.blocks[0].code[-2].s)

    def test_merged_union_operations_keep_typed_payload_operands(self):
        root = Path(__file__).resolve().parent.parent / "tests"
        lower = Gen.lower
        for name in ("mixed_union_format.py", "scalar_union_arithmetic.py",
                     "reference_union_calls.py", "reference_union_inheritance.py"):
            captured = []

            def capture(g, fn, captured=captured):
                g.verify(fn, False)
                captured.extend(i for b in fn.blocks for i in b.code
                                if i.op == "union.payload")
                lower(g, fn)

            with self.subTest(source=name), patch.object(Gen, "lower", capture):
                Gen().program(Loader([]).program(name, (root / name).read_text()))
                self.assertTrue(captured)
                for i in captured:
                    self.assertIsInstance(i.a[0], Val)
                    self.assertTrue(i.a[0].t.startswith("union["))
                    self.assertIn(i.s, umembers(i.a[0].t))

    def test_source_builds_declared_union_reads(self):
        source = (Path(__file__).resolve().parent.parent / "tests" /
                  "scalar_union_optional_narrowing.py").read_text()
        captured = []
        lower = Gen.lower

        def capture(g, fn):
            g.verify(fn, False)
            captured.extend(i for b in fn.blocks for i in b.code
                            if i.op in ("union.tag", "union.payload"))
            lower(g, fn)

        with patch.object(Gen, "lower", capture):
            Gen().program(Loader([]).program("scalar_union_optional_narrowing.py", source))
        self.assertEqual({i.op for i in captured}, {"union.tag", "union.payload"})
        for i in captured:
            self.assertTrue(i.a[0].t.startswith("union["))
            if i.op == "union.payload":
                self.assertIn(i.s, umembers(i.a[0].t))

    def test_numeric_operations_are_typed_and_pure(self):
        ops = [cast_op("bool", "int"), cast_op("bool", "float"), cast_op("int", "float")]
        ops.extend(compare_op(t, p) for t in ("int", "float")
                   for p in ("==", "!=", "<", "<=", ">", ">="))
        for i in ops:
            with self.subTest(op=i.op, type=i.t, predicate=i.s):
                g = Gen()
                g.verify(function_with(i), False)
                self.assertEqual(g.nums(i), 1)
                self.assertEqual(g.opfx(i, {}), 0)

    def test_numeric_casts_reject_other_type_pairs(self):
        for source, target in (("bool", "bool"), ("int", "int"), ("float", "float"),
                               ("int", "bool"), ("float", "int"), ("str", "float"),
                               ("", "float"), ("bool", ""), ("%slot", "int"),
                               ("opt[int]", "float"), ("bool", "%double")):
            with self.subTest(source=source, target=target):
                self.assert_bad(cast_op(source, target))

    def test_numeric_comparisons_reject_wrong_types_and_predicates(self):
        for t in ("", "bool", "str", "%slot", "opt[float]", "union[int,float]"):
            with self.subTest(type=t):
                self.assert_bad(compare_op(t))
        for second in ("float", "bool", "", "%slot"):
            with self.subTest(second=second):
                i = compare_op()
                i.a[1].t = second
                self.assert_bad(i)
        for predicate in ("", "is", "===", "olt"):
            with self.subTest(predicate=predicate):
                self.assert_bad(compare_op(predicate=predicate))
        i = compare_op()
        i.t = "int"
        self.assert_bad(i)

    def test_numeric_operation_shapes_and_metadata(self):
        for make in (cast_op, compare_op):
            for field, value in (("x", "int"), ("k", 1), ("b", ["entry"]),
                                 ("r", []), ("r", [1, 2]), ("a", [])):
                i = make()
                with self.subTest(op=i.op, field=field, value=value):
                    setattr(i, field, value)
                    self.assert_bad(i)
            i = make()
            i.a = i.a + [Val("%extra", i.a[0].t)]
            self.assert_bad(i)
        i = cast_op()
        i.s = "sitofp"
        self.assert_bad(i)
        i = compare_op()
        i.a = i.a[:1]
        self.assert_bad(i)

    def test_source_builds_numeric_ops_and_retains_exact_mixed_comparison(self):
        source = (Path(__file__).resolve().parent.parent / "tests" / "typed_ir_numeric.py").read_text()
        captured = []
        lower = Gen.lower

        def capture(g, fn):
            g.verify(fn, False)
            captured.extend(i for b in fn.blocks for i in b.code
                            if i.op in ("num.cast", "num.cmp", "rt"))
            lower(g, fn)

        with patch.object(Gen, "lower", capture):
            g = Gen()
            g.program(Loader([]).program("typed_ir_numeric.py", source))
        casts = {(i.a[0].t, i.t) for i in captured if i.op == "num.cast"}
        self.assertEqual(casts, {("bool", "int"), ("bool", "float"), ("int", "float")})
        comparisons = {(i.a[0].t, i.s) for i in captured if i.op == "num.cmp"}
        self.assertTrue({(t, p) for t in ("int", "float")
                         for p in ("==", "!=", "<", "<=", ">", ">=")}.issubset(comparisons))
        self.assertTrue(any(i.op == "rt" and i.s == "cmp_if" for i in captured))
        self.assertTrue({"bool", "int"}.issubset(g.funcs["real"].insts))


if __name__ == "__main__":
    unittest.main()
