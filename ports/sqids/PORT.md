# sqids 0.5.2, ported to Pystachy

[sqids](https://pypi.org/project/sqids/) makes short, unique, URL-safe ids from lists of
non-negative integers and decodes them back: `Sqids().encode([1, 2, 3])` is `"86Rf07"`, and
`decode("86Rf07")` is `[1, 2, 3]`. Programs use it for link shorteners and for public ids of
database rows. It is the Python package of Sqids, the successor of Hashids, and is written in
pure Python with no dependencies. It is rank 5,271 on PyPI in October 2026, and deps.dev lists 17
packages on PyPI that depend on sqids 0.5.2 directly (38 in all). Among them are the Masonite
web framework, django-sqids and netbox-sqids (sqids ids for Django models, and for every model
of NetBox as a plugin), the DKIST solar telescope data center's `dkist-inventory`, and the UK
National Archives' API client for Find Case Law (`ds-caselaw-marklogic-api-client`).

These are the package's three modules from the sdist `sqids-0.5.2.tar.gz` (SHA-256
`5ac08f0c5c9b6814bc2e7c79ee5931e0849d25d95c50e415771b022a44f58af9`), MIT licensed (`LICENSE`).

| file | upstream SHA-256 | edits |
|---|---|---|
| `__init__.py` | `dec511d0fd42c1fb20907eba8161abdadf6278c31d1d0b341038e242a204eaa1` | none |
| `constants.py` | `9b0e801cfcd48c0d028669d84a73a174a99f51da57ecc250e464a92eaf8ac1ae` | 2 set displays made lists (4 lines) |
| `sqids.py` | `7e9765b179f1b25e4b9fdf71d606d2048b2a037ed089933d8a2243e67ffb761e` | 12 regions |

`py.typed`, the package's empty PEP 561 marker, is left out. So is the rest of the sdist:
`tests/`, whose cases the tests below run as programs; `assets/filter_blocklist.py`, which
derives `constants.py`'s three filtered blocklists from `DEFAULT_BLOCKLIST`; and
`assets/performance.py`. Every edit is marked `# Pystachy port:` in the source, and `diff -ru`
against the sdist's `sqids/` shows them all, with an "Only in" line for `py.typed`.

The API is upstream's: `Sqids(alphabet, min_length, blocklist)`, `encode(numbers)` and
`decode(id)`, with the same defaults, errors and messages, and the same ids.

## The edits, and the feature each one stands in for

**Sets (M7, [#12](https://github.com/den-run-ai/pystachy/issues/12)).** sqids keeps its
blocklists in sets and compares characters with set operations. Pystachy has no sets yet.

1. In `constants.py`, `_exact_match` and `_match_anywhere` are list displays instead of set
   displays, 7 and 195 words (2 regions each, the `{` and the `}`). Upstream's line is rejected
   with `constants.py:575: error: set literals are not supported`. They are two of the three
   blocklists that `assets/filter_blocklist.py` derives from `DEFAULT_BLOCKLIST` for the default
   alphabet. The first holds the words of three characters, which block a whole id. The second
   holds longer words without a digit, which block an id that contains one. The third, the tuple
   `_match_at_ends`, holds words with a digit, which block an id that starts or ends with one.
   sqids only tests `id_ in self.__blocklist_exact_match` and loops over
   `self.__blocklist_match_anywhere`, and a list answers both as the set does. Each word is
   written once.
2. In `sqids.py`, `DIGITS = set("0123456789")` is the string `"0123456789"`. Upstream's line is
   rejected with `unsupported call set(str)`. Edit 5 tests a word's characters against it one at
   a time.
3. `__init__` checks that the alphabet's characters are unique with
   `len(set(alphabet)) != len(alphabet)`. In the port this is
   `any(alphabet.count(c) > 1 for c in alphabet)`, which is true for the same alphabets.
   Upstream's line is rejected with `unsupported call set(str)`. The check runs once per
   `Sqids()`, after the one that rejects alphabets with characters above 127, so it stops within
   the alphabet's first 129 characters, with one pass over the alphabet for each.
4. The three blocklist fields are annotated `List[str]` instead of `Set[str]` and
   `Tuple[str, ...]`, and the default branch stores the tuple as a list, `list(_match_at_ends)`
   (1 region). Upstream's annotations are rejected with
   `class sqids.sqids.Sqids is not supported: unsupported type annotation`. The 358-word tuple
   stays a tuple in `constants.py`: Pystachy compiles a tuple of one item type with a fixed
   length and can loop over it. But this field holds either the default's 358 words or a custom
   blocklist's words, and a tuple of any length (`Tuple[str, ...]`) is not a Pystachy type. Each
   `Sqids()` with the default blocklist and alphabet makes the copy once.
5. The branch that filters a custom blocklist changes in 5 regions:
   - `set(alphabet.lower())` is `alphabet.lower()`;
   - the three `set()`s are `[]`;
   - `word_lower_set & alphabet_lower != word_lower_set` (the word has a character outside the
     alphabet) is `not all(c in alphabet_lower for c in word_lower)`;
   - `word_lower_set & DIGITS` (the word has a digit) is `any(c in DIGITS for c in word_lower)`;
   - `add()` is `append()`, and `tuple(match_at_ends)` is the list itself.

   The filter keeps the same words as upstream's sets and puts each in the same blocklist. A
   word that the blocklist gives twice (`"ABCD"` and `"abcd"`) is in a list twice, where a set
   holds it once. That changes no id, because the lists are only searched.

**Slice steps (M7, [#12](https://github.com/den-run-ai/pystachy/issues/12), whose syntax item
lists them).**

6. `alphabet[::-1]` in `__encode_numbers` and in `decode` is `"".join(reversed(alphabet))`.
   `enumerate(id_[::-1])` in `__to_number` is `enumerate(list(reversed(id_)))` (3 regions).
   Upstream's code is rejected with `slice steps are not supported`. Without the `list()`, the
   last one is rejected with `reversed() cannot be nested in enumerate() here; make it a list
   first, list(reversed(...))`.

**`str.startswith()` and `endswith()` with a tuple (M1,
[#6](https://github.com/den-run-ai/pystachy/issues/6), item 7 of its runtime gaps).**

7. `__is_blocked_id` loops over the words of `_match_at_ends` and returns `True` as soon as
   `id_.startswith(word) or id_.endswith(word)` (1 region). Upstream calls
   `id_.startswith(words)` and `id_.endswith(words)` once each with the tuple. With the list of
   edit 4, that is rejected with `expected str, got list[str]`. The answer is the same: upstream
   tries every prefix in C and then every suffix, and the loop tries both for each word.

Sets would undo edits 1, 2, 3 and 5. A tuple of any length, together with M1's `startswith()`
of a tuple, would undo edits 4 and 7, and slice steps would undo edit 6.

## What compiles as it is

These parts of the package compile without edits:

- `Sqids.__init__`'s defaults, read from the imported `constants` module
  (`alphabet: str = DEFAULT_ALPHABET`, `blocklist: List[str] = DEFAULT_BLOCKLIST`).
- The identity test `blocklist is DEFAULT_BLOCKLIST and alphabet is DEFAULT_ALPHABET`, which
  picks the filtered blocklists.
- `encode(self, numbers: Sequence[int])`, where a `Sequence[int]` is a `list[int]`.
- The name-mangled private methods and fields (`self.__shuffle()`, `self.__alphabet`).
- `__encode_numbers`, which calls itself with `increment + 1` while an id is blocked, up to its
  `Reached max attempts` error.
- `sum()`, `any()` and `all()` of generator expressions, `enumerate()`, `ord()`, the swap
  `chars[i], chars[r] = chars[r], chars[i]`, `list.insert(0, ...)`, and `split()`, `join()` and
  slices without a step.
- `isinstance(min_length, int) or isinstance(min_length, bool)`, which is decided at compile
  time.
- The f-string error messages with `sys.maxsize`.
- `constants.py`'s 560-word `DEFAULT_BLOCKLIST` and its 358-word tuple.

sqids imports only `typing` and `sys`, so it needs none of the native stdlib hubs
([#11](https://github.com/den-run-ai/pystachy/issues/11)). It has no inheritance, callbacks or
unions, so it needs nothing from M2 ([#7](https://github.com/den-run-ai/pystachy/issues/7)), M3
([#8](https://github.com/den-run-ai/pystachy/issues/8)) or M4
([#9](https://github.com/den-run-ai/pystachy/issues/9)).

## What the port leaves out

- `py.typed`, and the sdist's `assets/` and `tests/` (above).
- A `blocklist` that is a set or a tuple. Upstream annotates the parameter `List[str]` but takes
  any iterable of strings, and its own tests pass sets (`Sqids(blocklist={"ArUO"})`). In the
  port it is a `list[str]`, and any other type is a compile-time error.
- A `min_length` that is not an `int`. For `"bogus"`, `{}` or `True`, CPython raises
  `TypeError: Minimum length must be an int` at run time, and Pystachy rejects the call at
  compile time (`expected int, got bool`).
- Reading the private fields from outside the class, as upstream's
  `test_alphabet_is_not_superset_of_blocklist_word_characters` does
  (`sqids._Sqids__blocklist_exact_match`). Pystachy does not mangle private names, so it
  rejects that read (`'sqids.sqids.Sqids' object has no attribute
  '_Sqids__blocklist_exact_match'`). The test checks the filter through the ids it gives
  instead.

## Deviations it hits

- **`int` is 64-bit** ([docs/language.md](../../docs/language.md#deviations-from-cpython)).
  `encode` takes numbers from 0 to `sys.maxsize` (2**63 - 1) as upstream does, and every id that
  `encode` makes decodes back. Two of upstream's cases go further:
  - Upstream's test of out-of-range numbers computes `sys.maxsize + 1`. Here that raises
    `OverflowError: integer result does not fit in 64 bits` before `encode` is called. In
    CPython, `encode` raises `ValueError: Encoding supports numbers between 0 and
    9223372036854775807`.
  - `decode` of a string that `encode` did not make can hold a chunk worth 2**63 or more. That
    raises the same `OverflowError` here: `Sqids().decode("Abcdefghijklmnopqrs")` is
    `[318301136152884387737588878647]` in CPython.

  The tests keep to 64-bit numbers, with `-sys.maxsize - 1` as the negative edge.
- **`str` is UTF-8 bytes.** sqids rejects an alphabet with a character above 127
  (`ValueError: Alphabet cannot contain multibyte characters`). The port rejects the same
  alphabets, because each byte of such a character is above 127 too. A non-ASCII id decodes to
  `[]` in both (`decode("été")`). The difference shows in blocklist words. The filter lowers
  them with `str.lower()`, whose case mapping knows only ASCII here, and counts their length in
  bytes. So CPython keeps a word with a non-ASCII letter whose lower case is ASCII, and the port
  drops it. Take `Sqids(blocklist=["uk\u212a"])`, where U+212A is KELVIN SIGN, which lowers to
  `k`. In CPython it blocks the three-letter id `ukk`, and `encode([63])` gives `Gpk`. Here it
  gives `UkK`, the default blocklist's id. Both drop other non-ASCII words, such as `ñañ` and
  `éé1` in the test, because no alphabet holds their letters.

## Tests

`tests/port_sqids_encode.py` runs the cases of sqids's own `tests/test_encoding.py`,
`test_minlength.py` and `test_alphabet.py` as a program:

- the 29 distinct incremental vectors, and `86Rf07` for `[1, 2, 3]`;
- round trips of 11 numbers up to `sys.maxsize`, of `range(100)`, and of numbers at 2**62 and
  2**63 - 1;
- the empty list, and strings that are not ids: `""`, `"*"`, a separator alone or first,
  characters outside the alphabet, and a trailing newline;
- the out-of-range errors;
- minimum lengths 6 to 13 and 62 to 65, four of the 62-character vectors, five lists at each of
  six minimum lengths up to 255, and the errors for -1 and 256;
- custom alphabets: hexadecimal; `abc`, also with a minimum length of 255; upstream's
  92-character alphabet of letters, digits, punctuation and quotes; and one of control
  characters. Five alphabets raise errors.

`tests/port_sqids_blocklist.py` runs `tests/test_blocklist.py`, with lists where it passes sets:

- the default, empty and custom blocklists;
- words that block a whole id, part of an id, or either end of one;
- decoding blocked ids, a word of three letters, and `Reached max attempts`;
- the filter, on a lowercase word in an uppercase alphabet, on words with characters outside
  the alphabet, and on words shorter than three characters;
- the verifier's words: upper case, with digits, and non-ASCII;
- five ids that the default blocklist blocks, by a word at an end and by a word anywhere. Each
  is encoded with both ways of filtering the default blocklist: the filtered lists of edits 1
  and 4, and edit 5's filter on a copy of `DEFAULT_BLOCKLIST`. They agree.
- the property of `tests/test_round_trip.py`, which hypothesis checks on random inputs, on 40
  fixed ones: an id decodes to its numbers, and when an id of three characters or more is
  blocked, sqids makes another id that also decodes to them.

`tests/run.sh` compares what both programs print with CPython's output, JIT and AOT. Run under
CPython against the unmodified upstream package, both print exactly what they print against this
port. They pass JIT and AOT with `PYSTACHY_IRCHECK=1`, and also with the CPython-hosted
compiler, with `PYSTACHY_OPT=-all`, and in the gc-stress form. The evaluation's and the
verifier's drivers, run against the port, print what CPython prints against upstream, except
for the two cases of the deviations above. The evaluation's driver prints 83 lines of vectors
and edge cases. The verifier's two cover numbers at 2**63, blocklist words, and the default
blocklist filtered both ways over 28,572 numbers.

Each test takes about 0.19 s to run JIT. Its AOT build takes 3.2 s, and the executable then
runs in under 0.01 s. In the gc-stress form, the compiler collects every 1,000 allocations
(`PYSTACHY_GC_STRESS=1000`) and the program collects at every allocation
(`PYSTACHY_GC_STRESS_PROGRAM=1`). There the JIT runs take 0.31 s and 0.32 s, and the AOT builds
and runs take 3.4 s and 3.3 s: 3.7 s and 3.6 s per test in all. These are wall-clock medians of
3, at a load average near 5 on this 4-core VM.

## Speed

The evaluation's workload makes `Sqids(min_length=8)` with the default blocklist. It then
encodes and decodes 100,000 lists of three numbers (`[i, i * 7919 % 1000003, 42]`) and checks
each decode. It prints `100000 1073142 100000`, here and in CPython. Medians of 3, with process
start-up, on a 4-core x86-64 VM:

| | wall clock | CPU time |
|---|---:|---:|
| Pystachy AOT executable, this port | 1.166 s | 1.062 s |
| CPython 3.13.16, unmodified sqids 0.5.2 | 5.062 s | 4.828 s |
| CPython 3.13.16, this port | 5.895 s | 5.875 s |

That makes the executable 4.5 times faster than CPython on upstream in CPU time, and 4.3 times
in wall-clock time. The load average was near 5 during these runs. An earlier set, at a load
near 13, gave 1.064 s against 4.899 s of CPU time (4.6 times). The evaluation measured 1.036 s
against 4.791 s of wall-clock time on a quieter VM. sqids has no C extension, so CPython runs it
as Python everywhere. The executable's peak RSS is 36 MB, and CPython's is 12 MB.

Under CPython the port is 22% slower than upstream. Most of that, 0.9 s, is edit 7's loop: it
calls `startswith()` and `endswith()` once per word in Python, where upstream makes two calls
with the tuple and C loops over it. With edit 7 undone, and the field a tuple again, CPython
takes 4.970 s. Each id of 8 or more characters is tested against 358 words at each end and 195
words anywhere. With an empty blocklist, the executable takes 0.769 s of CPU time, so the
default blocklist's check costs it 0.29 s.
