# pylev 1.4.0, ported to Pystachy

[pylev](https://pypi.org/project/pylev/) computes the Levenshtein edit distance in pure Python,
in five variants: the classic recursive definition, a memoized recursion, the Wagner-Fischer
table, its two-row iterative form (`levenshtein` itself) and Damerau-Levenshtein, which also
counts a swap of two adjacent characters as one edit. It is rank 4,258 on PyPI in October 2026.
Its users include Poetry 1.1 and 1.2, through their command-line layers clikit 0.6 and
cleo 1.0.0a, which call `levenshtein` to suggest a command for a mistyped name (cleo 2 replaced
it with rapidfuzz). These are its five modules from the sdist `pylev-1.4.0.tar.gz` (SHA-256
`9e77e941042ad3a4cc305dcdf2b2dec1aec2fbe3dd9015d2698ad02b173006d1`), under the 3-clause BSD
license (`LICENSE`).

| file | upstream SHA-256 | edits |
|---|---|---|
| `__init__.py` | `abd7f780829ad3ef0dd4f4eeb01ccd048e4dead3bc73a646f0fa5a8461e12463` | none |
| `classic.py` | `b2205250a290e2cf7f125e127bec28c1ea0f7a7387ad3559a841fec40a25d248` | none |
| `recursive.py` | `759d2d7ccbf4205ff0c6e946296d8f8c2eb0a7db503ac3a666f36066087e9088` | 1 line |
| `wf.py` | `160773704d0cee4715faddacb57b35e25bd28a72bbbd4726e11a1eebbf0caef1` | 2 regions (the Python 2 shim) |
| `damerau.py` | `c7e613589dd646f9587fcdcc3301a656bb49db61ea719ddfb3e84a70aced72d9` | 2 regions (the Python 2 shim) |

The rest of the sdist is packaging (`setup.py`, `setup.cfg`, `pyproject.toml`, `bench.sh`, the
README). Every edit is marked `# Pystachy port:` in the source, and `diff -ru` against the
sdist's `pylev/` shows them all.

## The edits, and the feature each one stands in for

**M1, lenient annotations and cheap refinements ([#6](https://github.com/den-run-ai/pystachy/issues/6)).**
`wf.py` and `damerau.py` open with the same Python 2 shim:

```python
PY2 = sys.version_info[0] == 2

if PY2:
    range = xrange
```

- **1, 2.** `PY2 = sys.version_info[0] == 2` becomes `PY2 = False`, in both files. Pystachy
  rejects `sys.version_info` (`unsupported module attribute sys.version_info`). M1's item 3
  folds `sys.version_info` tests at load time, as `sys.platform` tests are folded now.
- **3, 4.** The `if PY2:` block is commented out, in both files. Pystachy compiles the branch
  of a module-level `if` on a flag (and even of `if False:`), and this branch reads `xrange`,
  which is not defined (`name 'xrange' is not defined`). M1's item 4, module-level bool flags
  as constants, drops the dead branch.

With these four edits, four of the five variants compile: `wf_levenshtein`, `wfi_levenshtein`
(and its aliases `levenshtein` and `levenschtein`), `damerau_levenshtein` and
`classic_levenshtein`.

**Templates and empty containers ([#17](https://github.com/den-run-ai/pystachy/issues/17)),
outside the milestones.**

- **5.** `recursive.py`: `memo = {}` becomes `memo: dict[str, int] = {}`, which makes
  `recursive_levenshtein` compile. Pystachy types an empty dict from the first statement that
  fills it, looking ahead past the reads before that statement, but the look-ahead does not
  type a stored value that is a local assigned after the read. `recursive_levenshtein` reads
  the memo (`memo.get(key)`, `memo[key]`) before `dist = min(...)`, and stores `dist`, so
  Pystachy asks for the annotation (`cannot infer the type of 'memo', an empty dict so far`).
  Seven lines show it, in a function with annotations or without:

  ```python
  def triple(n: int) -> int:
      memo = {}
      if n in memo:
          print("hit")
      v = n * 3
      memo[n] = v
      return v
  ```

  This is rejected with the same message, and it compiles when the fill is
  `memo[n] = n * 3`.

## What compiles as it is

Every function of pylev is unannotated, so each one is a template, compiled once for each set
of argument types a program calls it with: `str`, and also `list[str]` or `list[int]`, since the
code indexes and compares any sequence. As they are: the from-imports and aliases of
`__init__.py` (`levenshtein = wfi_levenshtein`, `classic_levenschtein = classic_levenshtein`),
`__all__`, the `__version__` tuple; `None` defaults that the body replaces with an `int` or a
dict (`if len_1 is None: len_1 = len(string_1)`), given by keyword too, and passed on by the
recursion; the swap of the two arguments by tuple assignment
(`string_2, string_1 = string_1, string_2`) and the three-way rotation of the rows
(`dprev, d0, d1 = d0, d1, dprev`); list comprehensions, `[0] * n`, `d0[:]`, `d[-1]`, `min()` of
three values, and string keys built by `",".join([str(...), ...])`.

## What the port leaves out

Nothing of the modules' code. Two kinds of argument that CPython accepts are rejected at
compile time:

- tuples: `levenshtein((1, 2, 3), (1, 2, 4))` fails with `tuple index must be an integer
  constant`. M1's item 8 (#6) indexes tuples of one item type by a variable.
- two sequences of different types in `levenshtein`, `wfi_levenshtein` and
  `damerau_levenshtein`: `levenshtein("ab", ["a", "b", "c"])` fails with
  `cannot compare str == list[str]` (CPython gives 1). Their first line compares the
  arguments, and the swap needs a variable that holds either type: dynamic values, M4
  ([#9](https://github.com/den-run-ai/pystachy/issues/9)). `wf_levenshtein`,
  `recursive_levenshtein` and `classic_levenshtein` take such pairs and agree with CPython.

## Deviations it hits

- **`str` is UTF-8 bytes** ([docs/language.md](../../docs/language.md#deviations-from-cpython)).
  pylev counts edits of what `len()` and indexing count, so on non-ASCII text its distances
  are byte edit distances: `levenshtein("café", "cafe")` is 2 (CPython: 1), and
  `levenshtein("中文", "中文字")` is 3 (CPython: 1). They agree where the edits touch only
  ASCII characters (`levenshtein("naïve", "naïf")` is 2 in both) or replace one character with
  another that differs from it in one byte (`levenshtein("é", "è")` is 1 in both). All five
  variants behave alike. ASCII text, and sequences of words or numbers, are not affected.
- **`int` is 64-bit.** pylev's own arithmetic is on lengths and distances, far inside 64 bits.
  Items of an `int` sequence are compared, never computed on; the tests use 2**63 - 1 and
  -(2**63 - 1) as items, and a program cannot make a bigger item (computing one raises
  `OverflowError`).

## Tests

`tests/port_pylev_strings.py` runs the cases of pylev's own test suite (`tests.py` in its
repository, at the tag of 1.4.0) as a program, every pair in both orders, then edge cases on
every variant and alias: empty strings, the longer string first, adjacent transpositions, NUL
and control characters, `classic_levenshtein` on the short pairs, and the two non-ASCII pairs
above where the byte and character distances agree. `tests/port_pylev_sequences.py` runs the
variants on lists of words and of 64-bit ints, and `recursive_levenshtein` with explicit
lengths and offsets (positional and keyword) and with a memo shared between calls, whose keys
do not name the strings (a second call with other strings reads the first one's results, as
upstream does). `tests/run.sh` compares what they print with CPython's, JIT and AOT. Run under
CPython against the unmodified upstream package, both print exactly what they print against
this port. Both are small: under `make verify`'s gc-stress stage (the compiler collecting
every 1,000 allocations, the program at every allocation), each takes about 0.9 s for the JIT
run and the AOT build and run together.

## Speed

The headline workload: `wfi_levenshtein` (the function behind `levenshtein`) and
`damerau_levenshtein` on 6 pairs of strings of 1,500 and 1,400 characters over `acgt`, made by
a linear congruential generator in the program (checksum 9093 in both). Wall clock with
process start-up, median of 3 runs, on a 4-core x86-64 VM that was running other jobs:

| | time |
|---|---:|
| Pystachy AOT executable, this port | 0.360 s |
| CPython 3.13.16, unmodified pylev 1.4.0 | 4.058 s |

That is 11.3 times faster; a second set of runs gave 0.375 s and 3.989 s (10.6 times). pylev has
no C extension, so CPython runs it in the interpreter; programs that need speed under CPython
use a C library such as rapidfuzz or Levenshtein instead, which this does not compare.
