# tomli-w 1.2.0, ported to Pystachy

[tomli-w](https://pypi.org/project/tomli-w/) writes [TOML](https://toml.io): `tomli_w.dumps(doc)`
turns a dict with `str` keys into TOML text, and `tomli_w.dump(doc, fp)` writes that text to a
binary file. It is the write-only counterpart of tomli, the TOML parser that became the standard
library's `tomllib` in Python 3.11, without a writer. It is rank 342 on PyPI in October 2026. pip
vendors it (`pip lock` writes `pylock.toml` with `tomli_w.dumps()`), and Hatch and Flit depend on
it. These are its two modules from the sdist `tomli_w-1.2.0.tar.gz` (SHA-256
`2dd14fac5a47c27be9cd4c976af5a12d87fb1f0b4512f81d69cce3b35ae25021`), MIT licensed (`LICENSE`).

| file | upstream SHA-256 | edits |
|---|---|---|
| `__init__.py` | `b85ea5a4b65f3f974a6a0327ece2d7d5702256eff8847315b8fba162afa3f410` | none |
| `_writer.py` | `76c89f152db161fd62efa9a64727f3f72d76e710bb67f1d0f38e592a126c617b` | 14 edits in 27 regions |

`py.typed`, a marker for type checkers, is left out. Every edit is marked `# Pystachy port:` in
the source, and `diff -ru` against the sdist's `src/tomli_w` shows them all.

`dumps()` compiles for documents whose containers each hold values of one type:
`dict[str, str]`, `dict[str, dict[str, list[int]]]`, `dict[str, list[dict[str, str]]]` and so
on. Without their annotations, the writer's functions are templates, and each call of `dumps()`
compiles them for the type of its document.

## The edits, and the feature each one stands in for

**M1, lenient annotations and cheap refinements ([#6](https://github.com/den-run-ai/pystachy/issues/6)).**

- **Annotations Pystachy cannot represent** (item 1). Seven functions take the document or a
  value of it annotated `Mapping[str, Any]`, a bare `Mapping`, `object`, `Any` or
  `tuple | list`: `dumps()`, `gen_table_chunks()`, `format_literal()`, `format_inline_table()`,
  `format_inline_array()`, `is_aot()` and `is_suitable_inline_table()`. A call is rejected
  (`tomli_w._writer.dumps() is not supported: parameter 'obj': unsupported type annotation`), as
  is the local `tables: list[tuple[str, Any, bool]]` of `gen_table_chunks()` (`unsupported type
  annotation`). The port removes the parameters' annotations, which makes the functions
  templates (item 1 would treat them as absent), and `tables` is a `list[str]` (M4, below).
- **A flag of the module** (items 2 and 4). `TYPE_CHECKING = False` guards the imports that only
  the annotations use: `typing.IO`, `typing.Any`, `typing.Final`, `collections.abc.Generator` and
  `decimal.Decimal`. Pystachy does not fold the module's own flag, so it compiles the imports, and
  there is no `decimal` (`module 'decimal' is not supported`). It folds `typing.TYPE_CHECKING`,
  which the port imports instead; under CPython both are `False`.
- **`hex()`** (item 7). `format_string()` writes the control characters that have no short escape
  as `\uXXXX`, with `hex(ord(char))[2:]` (`unsupported call hex(int)`). The port writes
  `format(ord(char), "x")`, which gives the same digits.

**M2, full classes ([#7](https://github.com/den-run-ai/pystachy/issues/7)).** `ARRAY_TYPES =
(list, tuple)` holds two classes, for `isinstance(obj, ARRAY_TYPES)` (`the builtin 'list' cannot
be used as a value`). The port leaves the constant out, and its two uses, in `format_literal()`
and `is_aot()`, write `(list, tuple)`.

**M4, dynamic values ([#9](https://github.com/den-run-ai/pystachy/issues/9)).** Upstream walks
values of any type. Pystachy compiles each function for the types of one document, so the code
for every other type has to compile too, or be left out where the types tell at compile time that
it cannot run. Three edits do that, and a fourth leaves out `id()`, which M4 also lists:

- **`gen_table_chunks()` keeps keys.** It sorted the values of a table into `literals`,
  `(key, value)` pairs, and `tables`, `(key, table, inside_aot)` triples, which it then wrote in
  that order. Where all the values of a type of document are tables, or none are, one of the two
  lists is never filled, and Pystachy cannot type it (`cannot unpack int into 3 targets`); a list
  of pairs of a key and a value of any type would need M4. The lists hold the keys
  (`list[str]`), and the loops look the values up: a value that is a table is written as one, and
  each table of an array of tables as a `[[...]]` table (`inside_aot`), in upstream's order.
- **Tests of the types on names.** `elif is_aot(v) and not all(is_suitable_inline_table(t, ctx)
  for t in v)` is compiled for every type of value of a table: with `str` or `list[int]` values,
  `is_suitable_inline_table()` of a `str` or an `int` does not compile (`'int' has no method
  'items'`), and with `int` values neither does iterating `v` (`cannot iterate over int`). The
  condition also tests `isinstance(v, (list, tuple))` and, for each `t`, `isinstance(t, Mapping)`:
  Pystachy decides an `isinstance()` of a name at compile time, and compiles the rest of the
  condition for arrays of tables only. Where `is_aot(v)` is true, both tests are, so the condition
  has upstream's value. The loop over `tables` tests the types of the value the same way.
- **One type for the operands of `and`.** `is_aot()` returns `bool(isinstance(obj, ARRAY_TYPES)
  and obj and all(...))`, where `obj` is a list and the other operands `bool`s; Pystachy gives an
  `and` one type (`expected list[int], got bool`). The port writes `bool(obj)` for `obj`.
- **No `id()`.** `format_inline_table()` cached each table it rendered in
  `ctx.inline_table_cache`, keyed by `id(obj)` (`unsupported call id(dict[str,str])`), so that a
  table that `is_suitable_inline_table()` rendered to measure it is not rendered again when it is
  written. The cache is left out, so each table of an array of tables that stays inline is
  rendered twice (see Speed). `Context` still makes the empty dict.

**M7, the long tail ([#12](https://github.com/den-run-ai/pystachy/issues/12)).**

- **Sets.** `ASCII_CTRL`, `ILLEGAL_BASIC_STR_CHARS` and `BARE_KEY_CHARS` are frozensets of
  characters, made with a generator expression, `|` and `-` (`a generator expression is only
  supported as the argument of sum(), ...`). The port makes them `str`s of the same characters, and
  `char in ...` of one character tests them the same way. `format_key_part()` tested
  `BARE_KEY_CHARS.issuperset(part)` (`'str' has no method 'issuperset'`); it tests
  `all(c in BARE_KEY_CHARS for c in part)`. The `try`/`except TypeError` around that test, which
  turned a key of another type than `str` into a `TypeError` naming `type(part).__qualname__`
  (`unsupported call type(str)`, M2), is left out: `part` is a `str`, and Pystachy rejects a key
  of another type at compile time.
- **Generators.** `gen_table_chunks()` yielded the chunks of a table's text and, with
  `yield from`, those of the tables in it (`'yield' is not supported (there are no generator
  functions)`). It returns a list of them: `chunks.append()` for `yield` and `chunks.extend()`
  for `yield from`. `dumps()`'s `"".join()` and `dump()`'s `for` take the list as they took the
  generator, so neither is edited.

**Native stdlib hubs ([#11](https://github.com/den-run-ai/pystachy/issues/11)).** The modules
`datetime` (`module 'datetime' is not supported`) and `types` are not imported. `format_literal()`
loses its branches for `date`, `datetime` and `time` values (and the `ValueError` for a `time`
with a time zone), and `COMPACT_ESCAPES` is the dict that upstream wraps in a read-only
`types.MappingProxyType`.

## What compiles as it is

`format_string()`, the escaping loop: indexing until `IndexError`, slices, the lookups in
`COMPACT_ESCAPES`, and multiline strings with `replace("\r\n", "\n")`; `format_inline_array()` and
`format_inline_table()`, `str.join()` of generator expressions over a list or a tuple and over
`dict.items()`; `format_literal()`'s chain of `isinstance()` tests, with
`collections.abc.Mapping` for a dict and `bool` before `int`, and `str()` of an `int` or a
`float` (`inf`, `nan`, `-0.0`, `1e+16` as CPython writes them); `is_suitable_inline_table()`'s
f-string and its limit of 100 characters; the `Context` class, with attributes annotated `Final`
and the `ValueError` for a negative indent; `dumps()`'s positional-only and keyword-only
parameters; `from __future__ import annotations`; and `__init__.py`, with `__all__`,
`__version__` and the import of `dump` and `dumps`. `dump()`, `format_decimal()` and the end of
`format_literal()` (the lazy `from decimal import Decimal` and the `TypeError` for a value TOML
cannot hold) stay in the source, unedited: Pystachy compiles a function only where a program calls
it, and the end of `format_literal()` only for a type of value that none of its branches takes.

## What the port leaves out

- **`dump()`**, which writes bytes to a binary file (`fp: IO[bytes]`, `chunk.encode()`): a call
  is rejected (`tomli_w._writer.dump() is not supported: parameter 'fp': unsupported type
  annotation`). Bytes and binary files are M7. A program writes the text of `dumps()` to a file
  opened with `open(path, "w", encoding="utf-8")`.
- **Documents that mix types in a dict or a list** (M4), such as upstream's README example
  `{"table": {"nested": {}, "val3": 3}, "val2": 2, "val1": 1}`: Pystachy rejects the display
  (`expected str, got int` for `{"name": "demo", "version": 1}`). The same goes for a tuple of
  items of different types (`cannot iterate over tuple[int,str,float]: its items have different
  types`) and for optional values: in a `dict[str, int | None]`, a value takes none of
  `format_literal()`'s branches, and the end of the function is rejected (`importing module
  'decimal' in a function of module 'tomli_w._writer' is not supported`).
- **`date`, `datetime`, `time` and `decimal.Decimal` values** (#11): a Pystachy program cannot
  make them.
- **The `TypeError`s for a key that is not a `str` and for a value TOML cannot hold**, which
  CPython raises at run time: Pystachy rejects such a document at compile time
  (`tomli_w.dumps({1: "x"})`: `expected str, got int`).
- **The cache of rendered tables** (above), which only saves time.

## Deviations it hits

- **`str` is UTF-8 bytes** ([docs/language.md](../../docs/language.md#deviations-from-cpython)).
  `format_string()` indexes the text, and `format_key_part()` iterates the key, by bytes. That
  writes what CPython writes: the characters they look for are all ASCII, and the bytes
  0x80-0xFF of a non-ASCII character are in none of the sets, so they are copied as they are and
  make a key quoted, as the character does in CPython. But `is_suitable_inline_table()` keeps an
  array of tables inline when each table, written as `{ k = v },` after the indent, takes at most
  100 characters (`len(rendered_inline) <= MAX_LINE_LENGTH`), and Pystachy's `len()` counts bytes.
  A table of non-ASCII text that takes at most 100 characters but more than 100 bytes is written
  as `[[...]]` tables instead. `tomli_w.dumps({"rows": [{"name": "é" * 60}]})` (78 characters,
  138 bytes) gives

  ```toml
  rows = [
      { name = "éééééééééééééééééééééééééééééééééééééééééééééééééééééééééééé" },
  ]
  ```

  in CPython, and in Pystachy

  ```toml
  [[rows]]
  name = "éééééééééééééééééééééééééééééééééééééééééééééééééééééééééééé"
  ```

  and so does `"中" * 30` (48 characters, 108 bytes). Both are valid TOML for the same document:
  tomli 2.5.0 reads both back to it. Text that is all ASCII is not affected, and neither is any
  other output.
- **`int` is 64-bit.** TOML's integers are 64-bit, but `format_literal()` writes `str()` of an
  `int` of any size: for `{"big": 2**64}` CPython writes `big = 18446744073709551616`, and
  Pystachy raises `OverflowError: integer result does not fit in 64 bits` computing `2**64`. So
  does `2**63 - 1`, whose `2**63` does not fit; the tests write `9223372036854775807` and
  `-9223372036854775807 - 1`. Every `int` a Pystachy program holds is written as in CPython.

## Tests

`tests/port_tomli_w_values.py` writes values: `str`s with quotes, backslashes, tabs, the short
escapes `\b`, `\f`, `\n`, `\r`, the other C0 controls and DEL as `\uXXXX`, and the C1 controls, the
byte order mark, U+10FFFF and an emoji as they are; bare keys and quoted ones (empty, with a
space, a tab, a control character or a non-ASCII character); multiline strings (with CRLF, quotes,
backslashes and escapes, and strings that stay single-line) and the same text without the option;
`int`s at both 64-bit limits; `float`s (`inf`, `-inf`, `nan`, `-0.0`, `5e-324`, the largest, and
exponents); `bool`s; empty and nested arrays, and tuples; `indent=` 0, 1, 2 and the
`ValueError` for -1. `tests/port_tomli_w_tables.py` writes tables: an empty document, empty and
nested tables (with no header where they hold only tables), quoted keys in headers, and
arrays of tables, inline (each table at most 100 characters, the limit exactly, the same table
twice, nested inline tables, empty tables, a tuple of tables, an array of arrays of tables) or as
`[[...]]` tables (a table of 101 characters, a long value, a multiline string, arrays of tables in
tables and in arrays of tables). Many cases are those of tomli-w's own tests
(`tests/test_style.py` and `tests/test_types.py` of its repository at tag 1.2.0; the sdist has
none), with one type of value in each container. `tests/port_tomli_w_ini2toml.py` is a program
of two ports, ini2toml: it reads INI text with `ports/iniconfig` and writes it as TOML with
`tomli_w`, a section as a table and a value continued on more lines as a multiline string, for a
`setup.cfg` and for a text with a byte order mark, comments, an empty section, a dotted section
name, non-ASCII text, quotes and backslashes in a continued value, an empty value, a `:` separator
and a tab. Its AOT build is a 121 KB executable, linked with libc, libm and libgcc_s only.

`tests/run.sh` compares what they print with CPython's, JIT and AOT. Run under CPython against the
unmodified upstream package (and the unmodified iniconfig 2.3.1), all three print exactly what they
print against this port. They pass JIT and AOT with `PYSTACHY_IRCHECK=1`, with the native compiler
and the CPython-hosted one, with `PYSTACHY_OPT=-all`, and in `make verify`'s gc-stress form (the
compiler collecting every 1,000 allocations, the program at every allocation), where the JIT run
and the AOT build and run of `port_tomli_w_values`, `port_tomli_w_tables` and
`port_tomli_w_ini2toml` take 1.6 s, 2.2 s and 1.1 s of CPU together (2.0 s, 2.7 s and 1.3 s of wall
clock), almost all of it the AOT build. Without gc-stress, each JIT run takes 0.1 to 0.2 s of CPU.
`tests/run.sh` passes as a whole (1,937 passed, 0 failed).
Under CPython, the port's `_writer.py` also writes what upstream's writes for 40,000 random
documents, mixed types included, which checks the edits of `gen_table_chunks()`.

## Speed

**Run time.** The headline workload: a document of 20,000 tables of 10 `str` values (a third of
the keys need quotes, and each value has quotes, a tab and a newline to escape), written with
`dumps()` 5 times (31.8 MB of TOML), then an array of 20,000 small tables, which stays inline
(0.75 MB). The program builds the document first, in both runs. Median of 3 runs, with process
start-up, on a 4-core x86-64 VM that was running other jobs (load 11 to 16):

| | CPU | wall clock |
|---|---:|---:|
| Pystachy AOT executable, this port | 1.60 s | 1.88 s |
| CPython 3.13.16, unmodified tomli-w 1.2.0 | 2.34 s | 2.51 s |

That is 1.47 times faster in CPU time (1.34 times in wall clock; an earlier set of runs, with
CPU times within 2% of these, gave 1.87 times). Timed inside the program with
`time.process_time()`, the 5 `dumps()` take 1.47 s against 2.16 s (1.48 times), and the inline
array of tables 0.064 s against 0.060 s: slower, as the port renders each of its tables twice,
where upstream's cache renders it once. tomli-w is pure Python: there is no C extension that
CPython would run instead.

**Build time.** `pystachy build` of a program that imports `tomli_w` and writes one document
takes 0.6 s of CPU (0.14 s for `print(1)`) and makes an 85 KB executable; each other type of
document compiles the writer's functions again. The tests' builds take 1.4 s, 1.8 s and 1.0 s of
CPU.
