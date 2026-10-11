# qrcode 8.2, ported to Pystachy

[qrcode](https://pypi.org/project/qrcode/) (python-qrcode, by Lincoln Loop) is a QR code
generator in pure Python: it splits the data into numeric, alphanumeric and byte segments, adds
Reed-Solomon error correction over GF(256), lays out the modules (finder, timing and alignment
patterns, format and version information), picks the best of the 8 masks by ISO/IEC 18004's
penalty rules, and then gives the matrix, prints it in a terminal, or draws it as an image
through its PIL, PyPNG and SVG factories. It is rank 593 on PyPI in October 2026 (30.2 million
downloads in 30 days), and deps.dev lists 1,310 packages on PyPI that depend on qrcode 8.2
directly (1,995 in all). Its best-known users show the QR code that enrolls an authenticator app
in two-factor login: django-allauth (its `mfa` extra requires `qrcode>=7.0.0,<9`),
django-two-factor-auth (`qrcode<9`) and Flask-Security (its `mfa` extra, `qrcode>=8.2`); pretix,
the ticket shop, pins `qrcode==8.2`. They draw the codes as SVG or PNG images, which this port
leaves out (below).

This port is the encoder and its text output: `QRCode(...)`, `add_data()`, `make()`,
`print_ascii()`, `get_matrix()` and the `modules` matrix, with the `util` and `base` functions
under them. These are seven of the modules of the sdist `qrcode-8.2.tar.gz` (SHA-256
`35c3f2a4172b33136ab9f6b3ef1c00260dd2f66f858f24d88418a015f446506c`), under the BSD 3-Clause
License; `LICENSE` is the sdist's, which also holds the MIT license of pyqrnative, the code
qrcode was forked from.

| file | upstream SHA-256 | edits |
|---|---|---|
| `__init__.py` | `d02f23c778031d2278cb27651cdd35cadca2a4d876a4c3b75584bd0e4fa6e285` | 1 line |
| `constants.py` | `d02b1af1861d790f0d685ad19ade3799a560d763bcf5dfa82a088a01520edace` | none |
| `exceptions.py` | `2f67d9b9838ab1cbdd9fbdab6bec05f06c2caf6641f5e4595aba757f4203c781` | none |
| `LUT.py` | `3635ca3df1d24c56282e51a45e11637f6394abf1060fa9ab772607206ddd35c9` | none |
| `base.py` | `f49ff52f29c5e5d5c92b5e00cecf17c87258eba15f4e5b9827ae85f198de4ad6` | 10 regions: 6 method annotations, a field's, an import, a slice, and the 160 rows of `RS_BLOCK_TABLE` in brackets |
| `util.py` | `54e1b846b27a4243ecd1f2da6647de330c70c5d2292ac4479ba757be3a3d625e` | 28 regions, 9 of them method annotations |
| `main.py` | `385eee1c3033d938a1a5ee857ed79fe9f8951f6b69a152797a42c2206e25c890` | 35 regions, 13 of them method annotations |

The rest of the sdist is left out: the image factories (`image/`, with its `styles/`), `compat/`
(the optional imports of pypng's writer and of lxml or `xml.etree`), `console_scripts.py` (the
`qr` command),
`release.py`, `tests/`, and the packaging and documentation. Every edit is marked
`# Pystachy port:` in the source, and `diff -ru` against the sdist's `qrcode/` shows them all.

## The edits, and the feature each one stands in for

**Full classes (M2, [#7](https://github.com/den-run-ai/pystachy/issues/7)).** About half of
the edits, and nearly all of them mechanical.

1. 28 methods get parameter and return annotations: 13 of `QRCode`, 4 of `QRData`, 5 of
   `BitBuffer` and 6 of `Polynomial` (`main.py` imports `TextIO`, `base.py` `Iterator`, for
   them). Pystachy compiles a class only if its methods' parameters are annotated (`class
   qrcode.util.BitBuffer is not supported: parameter 'num' of method put() has no type
   annotation`). With M2's classes as templates, the methods would be compiled for the types
   they are called with.
2. Five fields are declared: `modules_count`, `data_cache` and `data_list` in `QRCode`'s class
   body, as `clear()` assigns them and Pystachy takes fields from the class body and `__init__`
   (`'qrcode.main.QRCode' object has no attribute 'modules_count'`), and `Polynomial`'s
   `self.num` and `QRData`'s `self.mode` where they are assigned (`cannot infer the type of
   field 'num'; annotate it`).
3. `version` and `mask_pattern` are properties upstream (`unsupported decorator @property`);
   here they are plain `Optional[int]` fields. Their setters become the methods
   `_set_version()` and `_set_mask_pattern()`, with the setters' bodies, called where upstream
   assigns the properties (in `__init__` and in `best_fit()`), and called again at the start
   of `make()`, on what the fields hold then. So `qr.version = 41` followed by
   `qr.make(fit=False)` raises upstream's `ValueError: Invalid version (was 41, expected 1 to
   40)`, and `qr.mask_pattern = 9` followed by `qr.make()` raises `ValueError: Mask pattern
   should be in range(8) (got 9)`, as upstream does when the property is assigned (see *What
   the port leaves out*). The version getter, which fits the version when it is still `None`, is
   gone; `make()` fits it there too, and `makeImpl()` copies the field to a local narrowed to
   `int` for its cache's dict key (`a test does not narrow a global or a field`), where the
   getter would return an `int`.
4. `class QRCode(Generic[GenericImage])` is `class QRCode:` (`class inheritance is not
   supported`). The base only parameterizes the image factory.
5. `__init__` keeps `image_factory` as its fifth parameter, so that `mask_pattern` stays the
   sixth, as the verifier of the evaluation asked; but no factory exists here and a class is
   no value (`class 'qrcode.main.QRCode' cannot be used as a value`), so it is an
   `Optional[int]` that only its default `None` makes sense for. For an `int`, it raises the
   `TypeError: issubclass() arg 1 must be a class` that upstream's `assert
   issubclass(image_factory, BaseImage)` raises for one.
6. `Polynomial.__mod__` extends a list with `self.num[-difference:]` where upstream slices
   the object, `self[-difference:]`, through its `__getitem__` (`slicing an object is not
   supported: Polynomial.__getitem__ would take a slice object`).
7. `get_matrix()` is annotated `-> list[list[Optional[bool]]]`, and so are its locals `code`
   and `x_border`: a list holds items of one type, and the modules are `Optional[bool]`, which
   upstream's `cast(list[bool], module)` renames. This is the verifier's 3-line fix; without
   it, `get_matrix()` does not compile.

With classes as templates and properties, M2 would undo 1 to 4 and the annotation of 7; with
classes as values, 5.

**Lenient annotations and cheap refinements (M1,
[#6](https://github.com/den-run-ai/pystachy/issues/6)).**

8. The alias `ModulesType = list[list[Optional[bool]]]` stays as a comment and is spelled out
   where it is used, in `precomputed_qr_blanks`'s annotation and `QRCode.modules`'s (`the
   builtin 'list' cannot be used as a value`).
9. The `TypeVar`s' bounds are the string `"BaseImage"` (`a TypeVar's constraints, and a bound
   other than a string, are not supported`); `BaseImage` is left out with the image factories.
10. `cast(int, self.modules[x][y])` is written `1 if self.modules[x][y] else 0` (`the builtin
    'int' cannot be used as a value`), and get_matrix's `cast(list[bool], ...)` is dropped (7).
11. `create_bytes()` gets `-> list[int]`: Pystachy reads a def with annotated parameters and no
    return annotation as returning `None` (`returning a value from a function without a return
    annotation`).
12. `PATTERN_POSITION_TABLE` is annotated `list[list[int]]`: Pystachy types a list display by
    its first item, here `[]` (`cannot infer the type of an empty list`).
13. `RS_BLOCK_TABLE`, a tuple of 160 tuples of 3 or 6 ints, is a list of lists: `rs_blocks()`
    indexes it by a variable (`tuple index must be an integer constant`) and slices a row, and
    a list of the tuples would hold two tuple types (`expected tuple[int,int,int], got
    tuple[int,int,int,int,int,int]`). Tuples of one item type indexed by a variable are M1's
    item 8; rows of two lengths in one table also need M4's mixed containers. An AST
    comparison shows that the values are the same. `base.rs_blocks()` called with a version
    past 40 raises `IndexError: list index out of range`, where upstream's says `tuple`.

**Functions as values (M3, [#8](https://github.com/den-run-ai/pystachy/issues/8)).**

14. `util.mask_func(pattern)` returns one of 8 lambdas, which `map_data()` calls for every
    module (`only functions, classes and methods can be called`). The new
    `util.mask_bit(pattern, i, j)` holds the same 8 expressions, and `map_data()` calls it.
    `mask_func` stays, and compiles where it is not called. Under CPython, the two agree on all
    8 patterns at every position of a 177 × 177 matrix and around it.
15. `print_ascii()`'s nested `get_module(x, y)` (`nested functions and classes are not
    supported`) is the method `_get_module(x, y, invert, modcount)`, given as arguments the
    names it read from `print_ascii()`'s scope.
16. `sum(map(_data_count, ...))` is `sum(_data_count(b) for b in ...)`, and
    `sum(map(sum, modules))`, the count of dark modules, is
    `sum(row.count(True) for row in modules)` (`map() is not supported`; `sum()` of
    `bool | None` items is rejected too): every module is `True` or `False` by then.
17. `make_image()` and its two `@overload` stubs are left out with the image factories: a
    method with `**kwargs` keeps the whole class from compiling (`**kwargs is not supported`).

**Dynamic values (M4, [#9](https://github.com/den-run-ai/pystachy/issues/9)).**

18. `print_ascii(out=None, ...)` is `print_ascii(out: TextIO = sys.stdout, ...)`: an `Optional`
    file is not supported (`None/Optional is only supported for class types, str, int, float,
    bool, list, dict and tuple, not file`). Upstream's `if out is None: out = sys.stdout` stays.
    `print_tty(out: Optional[TextIO] = None)` keeps the `None`, and is rejected where a
    program calls it.

**The long tail (M7, [#12](https://github.com/den-run-ai/pystachy/issues/12)).**

19. `c in {0, 6}` is `c in (0, 6)`, twice (`set literals are not supported`).
20. In the penalty rules, `range(n)` stored in a variable is `list(range(n))` (`range() is only
    supported in a for loop, ...`), and the `for col in it:` loops that skip an item with
    `next(it, None)` are `while` loops that step `col` (or `row`) once more instead, in levels
    2 and 3. Under CPython, `lost_point()` gives what upstream's gives for 3,000 random and
    patterned matrices.
21. `optimal_data_chunks()` and `_optimal_split()` are generators (`'yield' is not supported`);
    here they return the list of what they yield. `QRCode.add_data()` extends a list with it,
    as upstream.
22. `bytes` (`bytes literals are not supported`): `ALPHA_NUM` is a `str`; `to_bytestring()`
    returns the `str` where upstream encodes it to UTF-8; `QRData.write()` puts `ord(c)` of each
    byte, where iterating `bytes` gives ints; and `print_ascii()`'s four characters,
    `bytes((code,)).decode("cp437")` of 255, 223, 220 and 219, are written decoded (no `bytes`,
    no codecs). A Pystachy `str` holds UTF-8 bytes, which iteration, indexing, slicing and
    `len()` see one by one, so the data is exactly the bytes upstream encodes (below).
    `to_bytestring()` also has a branch for a `str` of code points, where `len("é") == 1`: it
    makes the `str` of `chr()` of each of the UTF-8 bytes, with the new helper
    `_utf8_bytes()`. That branch never runs under Pystachy; it makes the port give upstream's
    codes under CPython too (it agrees with `str.encode("utf-8")` on all 1,112,064 Unicode
    scalar values), which is how `tests/record.sh` records the test's expected output.

M7's generators and iterators, sets and `bytes` would undo 19 to 22.

**Native standard-library hubs ([#11](https://github.com/den-run-ai/pystachy/issues/11), M6).**

23. `import re` is dropped (`module 're' is not supported: ...`), the first error the
    unmodified package gives. `RE_ALPHA_NUM.match(data)`, `rb"^[ALPHA_NUM]*\Z"`, is
    `all(c in ALPHA_NUM for c in data)` in `optimal_mode()`. The chunk optimizer compiles
    `rb"\d{minimum,}"` and `b"[ALPHA_NUM]{minimum,}"`, or for data of at most `minimum` bytes
    `rb"^\d+$"` and `b"^[ALPHA_NUM]+$"`, and `re.search()`es them; here a pattern is the string
    of the characters it matches, `minimum` and whether it is anchored, and the new `_search()`
    finds what `re.search()` found: the first run of at least `minimum` of the characters,
    which the regex takes whole, or, anchored, the run at the start if it reaches the end or a
    final `"\n"`, before which `$` matches too. A negative `minimum` (`add_data(data,
    optimize=-1)`) makes upstream's regex end in the literal text `{-1,}`, not a repeat, and
    `_search()` then finds one of the characters followed by that text, as the regex does.
    Under CPython, the chunker gives upstream's chunks for 245,128 cases: every string of up
    to 4 bytes over `1`, `9`, `A`, `$`, space, `a`, `"\n"` and the bytes `0xC3` and `0xA9`,
    every string of 5 of the first 7 of them, each with `minimum` 1 to 6, and 20,000 random
    strings of runs of up to 80 bytes with `minimum` 1, 3, 8, 20 and 50; and for 48,086 more
    with `minimum` -2 and -1 among them: every string of up to 4 of `1`, `A`, `a`, `"\n"`,
    `{`, `-`, `,` and `}`, and 20,000 random strings with the texts `{-1,}`, `{-2,}` and
    `{1,}` among their runs.
24. The cp437 decoding of 22 needs `_codecs`; and the image factories need PIL, or pypng (whose
    PNG writer needs `zlib` and `struct`), or `decimal` and `xml.etree` for SVG, besides M2's
    inheritance (`class PilImage(qrcode.image.base.BaseImage)`) and `abc`: `__init__.py` and
    `main.py` no longer import `qrcode.image`.

A native `re` would undo most of 23; the chunker is the largest rewrite of the port (about 50
lines).

**Files.**

25. `print_ascii(tty=True)` tests `out.isatty()` (`'file' has no method 'isatty'`): here it
    always raises `OSError("Not a tty")`, as upstream does where `out` is not a terminal.

## What compiles as it is

`constants.py`, `exceptions.py` (`DataOverflowError`, an exception class with `pass`) and
`LUT.py` (`rsPoly_LUT`, a dict of 13 generator polynomials, lists of up to 31 ints)
compile unmodified, and so does most of the rest: the GF(256) tables `EXP_TABLE` and `LOG_TABLE`,
filled by module-level loops; `glog()` and `gexp()`, with `raise ValueError(f"glog({n})")`;
`Polynomial`'s `__mul__` and the recursive `__mod__` (`Polynomial(num, 0) % other`), which
iterate the object through `__iter__` (`enumerate(self)`, `zip(self, other)`); the `RSBlock`
`NamedTuple` and `rs_blocks()`'s `count, total_count, data_count = rs_block[i : i + 3]`;
`BIT_LIMIT_TABLE`, a nested list comprehension run at import; the BCH codes of the format and
version information (`BCH_type_info()`, `BCH_type_number()`, shifts and `^=` in `while` loops);
`mode_sizes_for_version()`, whose dict results `best_fit()` compares by identity
(`mode_sizes is not ...`); the bit buffer and the numeric and alphanumeric writers
(`int(chars)`, `ALPHA_NUM.find(chars[0]) * 45 + ...`); `create_bytes()`'s Reed-Solomon blocks and
their interleaving, and `create_data()`'s padding; the penalty rules' run lengths and 1:1:3:1:1
patterns; `QRCode`'s module layout (finder, alignment and timing patterns, format and version
information, the zigzag of `map_data()`), with `0 <= r <= 6` chained comparisons and the
module-level cache `precomputed_qr_blanks`; `bisect_left(..., lo)` from `lib/bisect.py`, the
unmodified CPython module, in `best_fit()`; `_check_mask_pattern()`'s `isinstance()`, decided at
compile time; `copy_2d_array()`; the `ActiveWithNeighbors` `NamedTuple` with `__bool__`;
`is_constrained()`; and `print_ascii()`'s loops and `out.write()` and `out.flush()` on
`sys.stdout`.

## What the port leaves out

- The images: `qrcode.image` and `compat/` (PIL, PyPNG and SVG output, styled images,
  embedded logos), `QRCode.make_image()` (`'qrcode.main.QRCode' object has no method
  'make_image'`), and `qrcode.make()` and `qrcode.run_example()`, which stay but take
  `**kwargs` (`**kwargs is not supported` where a program calls them). The `qr` command
  (`console_scripts.py`).
- `print_tty()` (18, 25) and `active_with_neighbors()`, which calls
  `ActiveWithNeighbors(*context)` (`star arguments are not supported`); both stay, and are
  rejected where a program calls them.
- Data other than `str`: `add_data()` takes a `str` (`add_data(12345)`: `expected str, got
  int`; `add_data(util.QRData("x"))`: `expected str, got QRData`), where upstream also takes
  `bytes`, other values (through `str()`) and `QRData` objects, and `util.QRData()` takes a
  `str`. A `bool` where an `int` goes is rejected too (`QRCode(mask_pattern=True)`: `expected
  int | None, got bool`; `add_data(s, optimize=True)`: `expected int, got bool`), where
  upstream takes it as 1.
- The setters' timing (3): upstream raises as the bad value is assigned, the port when
  `make()` runs next. A program that assigns a bad value and calls no `make()` (or calls
  `print_ascii()` or `get_matrix()` on a code already made, which do not make it again) gets
  no error, and reads back the value it assigned. And reading `qr.version` before `make()`
  gives `None`, where upstream's getter fits a version and gives it (1 for a `QRCode()`
  without data).
- `print_ascii(tty=True)` on a terminal (25), and `out` defaults to the `sys.stdout` of when
  the module was imported, where upstream reads `sys.stdout` at each call. `out` is
  `sys.stdout`, `sys.stderr` or a file from `open()`: Pystachy has no `io.StringIO`, which
  upstream's own tests print to.
- `repr()` of a `QRData` shows a `str`, `'HELLO'`, where upstream's shows `b'HELLO'` (so
  does the `ValueError` of `int()` on a numeric chunk that is not digits, which only a
  negative `optimize` makes: `'5{-'` for `b'5{-'`); and
  `util.optimal_data_chunks()` returns a list, where upstream returns a generator (both
  iterate the same; `len()` works on the port's, `next()` on upstream's).
- `util.mask_func()` (14), which compiles where it is not called.

## Deviations it hits

- **`str` is UTF-8 bytes** ([docs/language.md](../../docs/language.md#deviations-from-cpython)),
  and that is what makes the byte mode exact. Upstream encodes the text to UTF-8 and writes
  each byte; here the `str` holds those bytes already, and `len()`, iteration, indexing and
  slicing in the chunker and in `QRData.write()` see them one by one. So
  `add_data("https://example.com/путь?q=€")` makes one byte-mode chunk of 34 bytes and the
  same version-4 code in both (the test prints it), and every non-ASCII input the evaluation
  and its verifier tried (Cyrillic, `€`, `é`, CJK, emoji, combining marks) gave upstream's
  modules. The `isdigit()` of `optimal_mode()` knows only ASCII here, as `bytes.isdigit()` does
  upstream. Four things differ:
  - A program's own `len()` of the text: `len("https://example.com/путь?q=€")` is 28 in
    CPython and 34 here; `sum(len(c) for c in qr.data_list)`, the bytes the library counts, is
    34 in both, and the test prints that.
  - `util.optimal_mode()` called with a `str` that is not ASCII, rather than with what
    `to_bytestring()` returns: `optimal_mode("٣")` (ARABIC-INDIC DIGIT THREE) is 1 (numeric) in
    CPython, whose `str.isdigit()` is true for it, and 4 (bytes) here. Through `add_data()` and
    `QRData()` it is 4 in both.
  - Text a program builds with `chr()` of 128 to 255, which is that one byte here (UTF-8 above
    255): `add_data(chr(233))` writes the byte `0xE9`, where upstream encodes `"é"` as the two
    bytes `0xC3 0xA9`. The literal `"é"` or `"\u00e9"`, and `chr()` of a larger code point,
    give upstream's code.
  - A lone surrogate: `qr.add_data(chr(0xD800))` makes a version-1 code of its three-byte
    form here (and under CPython from the port, whose `_utf8_bytes()` encodes it), where
    upstream's `make()` raises `UnicodeEncodeError: 'utf-8' codec can't encode character
    '\ud800' in position 0: surrogates not allowed`.
- **`int` is 64-bit.** The encoder's own ints are small (bit buffers of bytes, 15- and 18-bit
  BCH codes, at most 23,648 data bits). Arguments are checked as upstream checks them, also at
  the extremes: `QRCode(version=2**63 - 1)` and `version=-2**63` raise `ValueError: Invalid
  version (was 9223372036854775807, expected 1 to 40)` and its negative twin, and
  `box_size=-(2**63 - 1)` `Invalid box size`, in both (the test runs them). A bigger int cannot
  be made: `QRCode(version=int("100000000000000000000"))` raises `OverflowError: int() result
  does not fit in 64 bits` in `int()`, where CPython raises `ValueError: Invalid version (was
  100000000000000000000, expected 1 to 40)`.

## Tests

`tests/port_qrcode_encode.py` prints three codes with `print_ascii()`: alphanumeric
(`HELLO WORLD`, level Q, border 1), numeric (20 digits, level L, inverted, no border) and
UTF-8 bytes (`https://example.com/путь?q=€`, level H, version 4). Then it prints checksums of
the modules of codes of no data, of mixed data that the optimizer splits into four chunks, of
CJK and emoji text, of a version-7 code (with its version information), of each of the 8 masks
given, and of a code given its version and mask by position (with `image_factory`'s `None`
fifth). Then the errors: `QRCode()`'s checks of `version` (41, 0, -1, 2**63 - 1, -2**63),
`mask_pattern`, `box_size` and `border`; an `int` `image_factory`; the setters' checks of 3
(`mask_pattern = 9`, `version` = 41, 0 and -1), and assignments that pass them; data too long
for version 1-H (`DataOverflowError`) and for any version (2,953 bytes fit 40-L, 2,954 raise the
version setter's `ValueError`); `error_correction=5` (`IndexError`); and `print_ascii(tty=True)`.
Then `best_fit()` across the three sizes of the length fields (versions 9/10 and 26/27, where it
tries again); `get_matrix()` with and without a border, and the aliasing of its border rows; two
`add_data()` calls and a second `make()`; `make(fit=False)` without a version; and the chunk
optimizer on 16 edge cases (each class of character, `$` before a final `"\n"` in the anchored
form, non-ASCII bytes between runs, NUL, combining marks) with `minimum` 1, 4 and 20, a
negative `minimum` (with and without the literal text `{-1,}` in the data, and a code made
with `optimize=-1`), and 60 pseudo-random strings, and `optimal_mode()`. `tests/run.sh`
compares what it prints with CPython's, JIT and AOT. Run under CPython against the unmodified
upstream package, it prints exactly what it prints against this port.

It leaves out what the port leaves out, and the deviations above. The evaluation's and its
verifier's longer drivers print the same under CPython against the unmodified upstream, under
CPython against the port, and JIT and AOT: a 183-line demo, 310 strings through the chunker
(3,168 chunks) and 250 longer ones (11,586), the verifier's harder inputs (CJK, emoji,
combining marks, NUL, the 40-L capacity edges of 2,953 bytes and 7,089 digits, 64-bit
extremes, two `add_data()` calls) and `get_matrix()`.

The test is one program, not two, because its AOT build is slow, and `make verify` builds
every test in several stages: most of the build's time is LLVM's on the module code that makes
`RS_BLOCK_TABLE`'s 160 lists (a module of that table alone takes 2.2 s of CPU to build, where
hello world takes 0.14 s). On a 4-core VM that other jobs kept busy (load average 5 to 6), the
test runs in 0.4 s JIT, its AOT build takes 4.8 s (4.5 s of CPU) and the executable runs in
0.01 s. Under `make verify`'s gc-stress stage (the compiler collecting every 1,000
allocations, the program at every allocation), the JIT run takes 2.1 s, the AOT build 5.7 s
and the AOT run 1.7 s: 9.5 s in all, 8.1 s of CPU. Choosing a mask makes a code 9 times, so the
version-7 code, and the codes of `get_matrix()`, of the second `make()` and of
`make(fit=False)`, are given their mask.

## Speed

The evaluation's headline workload: 400 codes of all four error correction levels and versions
3 to 16 (URLs with letters and digits, so that the optimizer splits them), each fitted, masked
by the best of 8 and laid out, with a checksum of the versions and the dark modules (`codes 400
versions 3473 dark 570996` in all three). Median of 3 runs, with process start-up, on a 4-core
x86-64 VM:

| | wall clock | CPU time |
|---|---:|---:|
| Pystachy AOT executable, this port | 0.535 s | 0.533 s |
| CPython 3.13.16, unmodified qrcode 8.2 | 4.571 s | 4.510 s |
| CPython 3.13.16, this port | 5.779 s | 5.337 s |

That is 8.5 times faster; a second set of runs gave 0.541 s and 4.629 s (8.6 times). JIT, with
the compilation, takes 0.948 s, and the executable is 402 KB. The VM's load average was 5 on
its 4 cores. qrcode has no C extension, but CPython runs its chunk optimizer in the C regex
engine; under CPython the port, whose optimizer and UTF-8 encoding are Python loops, is slower
than upstream, so the executable runs the code of this port 10 times faster (in CPU time) than
CPython does.
