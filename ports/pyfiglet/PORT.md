# pyfiglet 1.0.4, ported to Pystachy

[pyfiglet](https://pypi.org/project/pyfiglet/) is FIGlet in pure Python: it draws text as banners
of ASCII art in FIGlet's fonts, where each character is a glyph several lines high, and joins the
glyphs with FIGlet's kerning and smushing rules, wraps them at a width, justifies them and prints
them left to right or right to left. It is rank 1,594 on PyPI in October 2026 (5.9 million
downloads in the 30 days to 1 October). asciimatics (for its `FigletText` renderer) and
textual-pyfiglet (a Textual widget) depend on it. These are its module `pyfiglet/__init__.py` and
`version.py` from the sdist `pyfiglet-1.0.4.tar.gz` (SHA-256
`db9c9940ed1bf3048deff534ed52ff2dafbbc2cd7610b17bb5eca1df6d4278ef`), MIT licensed (`LICENSE`), and
three of the sdist's 550 FIGlet fonts, `standard` (pyfiglet's default), `slant` and `small`,
embedded as strings in `_fontdata.py`.

| file | upstream SHA-256 | edits |
|---|---|---|
| `__init__.py` | `bae593a5b013824c47412db63fb9b66c943b6b9cb0a940e0b785690ce3fb497f` | 58 regions |
| `version.py` | `b611991d8ea92cf84973a0b06018d4690ea91b12e1c0f329fe98e862c8b0bc8e` | none |
| `fonts/standard.flf` | `398a52d40da3ec217ce3673f532eb8e2303023369cfa0dc27b11ff43cc306a4f` | none: a string of `_fontdata.py` |
| `fonts/slant.flf` | `0a1f6ebfa9b0a1658107765d5273f537e2a626c79a6fb431e1ca1e5330a74f2a` | none: a string of `_fontdata.py` |
| `fonts/small.flf` | `6326d8a718cb57689d5eaa98d301b9297ef6f6300279635b901532a2f3d6aadf` | none: a string of `_fontdata.py` |

`_fontdata.py` is the port's own: a dict `FONTS` from the three names to the text of the three
font files, each written as a raw string literal `r"""..."""` that holds the file byte for byte
(the files are ASCII, hold no `"` and do not end in a backslash; under CPython,
`ast.literal_eval()` of each literal gives the file's text). Left out of the sdist's package:
`__main__.py` (the command line, which calls `main()`), `test.py` (see Tests), the empty
`fonts/__init__.py` and the other 572 files of `fonts/`. Every edit is marked `# Pystachy port:` in
the source, and `diff -u` against the sdist's `pyfiglet/__init__.py` shows them all. Code is
commented out rather than deleted, but for the closure `__char()`, which is a method now (below).

**The fonts' license.** The three fonts are FIGlet's, and their comment lines name their authors:
"Standard by Glenn Chappell & Ian Chai 3/93 -- based on Frank's .sig", "Slant by Glenn Chappell
3/93 -- based on Standard" and "Small by Glenn Chappell 4/93 -- based on Standard", modified by
John Cowan for FIGlet 2.2 (the standard font's Latin-2 to Latin-5 letters), by Paul Burton in
12/96 (all three) and by patorjk in 2012 (the standard font's U+0CA0). Each header grants:
"Permission is hereby given to modify this font, as long as the modifier's name is placed on a
comment line." FIGlet's repository (github.com/cmatsuoka/figlet) has them in its `fonts/`, under
its 3-clause BSD license ("Copyright (C) 1991, 1993, 1994 Glenn Chappell and Ian Chai", and later
holders), with the same glyphs as pyfiglet's copies, which differ in their first line and comment
lines. pyfiglet's repository keeps them among its `fonts-standard`, the fonts that its README says
"have a clear redistribution license", and its sdist ships them beside its MIT `LICENSE`. The port
embeds them unmodified, and `THIRD_PARTY_NOTICES` reproduces FIGlet's license.

## The edits, and the feature each one stands in for

**M2, full classes ([#7](https://github.com/den-run-ai/pystachy/issues/7)).**

- **Return annotations.** A missing return annotation means `-> None`, so the 20 functions and
  methods whose value is used are annotated: `figlet_format() -> str`, `FigletError.__str__()`,
  `FigletFont.preloadFont()`, `FigletRenderingEngine.render()`, `FigletProduct.getString()`, 13
  methods of `FigletBuilder` (among them `smushChars() -> Optional[str]` and
  `getCurWidth() -> Optional[int]`), and `Figlet`'s `direction()` and `justify()` (below).
- **Unannotated parameters**, which a method may not have: `addLeft` of `getLeftSmushedChar()`,
  `addLeft`, `idx` and `smushed` of `updateSmushedCharInLeftBuffer()` and `saved_buffer` of
  `cutBufferAtLastBlank()`.
- **Fields that `__init__` does not assign.** `FigletFont.loadFont()` assigns `height`,
  `hardBlank`, `printDirection` and `smushMode`, and `Figlet.setFont()` assigns `Font`
  (`'pyfiglet.Figlet' object has no attribute 'Font'`): the class bodies declare them.
  `FigletBuilder.__init__` assigns `text` and `buffer` from comprehensions, which do not type a
  field (`cannot infer the type of field 'buffer'; annotate it`): they are annotated.
- **Properties.** `Figlet.direction` and `Figlet.justify` are `@property`s (`unsupported decorator
  @property`): they are methods, called `direction()` and `justify()` at their three uses.
- **A subclass of `str`, and a class as a value.** `FigletString`, the type `renderText()` returns,
  subclasses `unicode_string`, a variable that upstream binds to
  `type(''.encode('ascii').decode('ascii'))`, which is `str` (`str.encode()` and `bytes` are M7;
  `unicode_string = str` would be `the builtin 'str' cannot be used as a value`). That line is
  commented out and the class names `str` as its base. Pystachy leaves the class uncompiled
  (inheritance), so `getString()` and `renderText()` return the `str` that upstream wraps in a
  `FigletString`.

**M3, functions as values ([#8](https://github.com/den-run-ai/pystachy/issues/8)).**

- **`**kwargs`.** `figlet_format(text, font, **kwargs)` passes its keywords on to `Figlet`; it
  takes `Figlet`'s three, `direction`, `justify` and `width`, with `Figlet`'s defaults.
  `Figlet.setFont(**kwargs)` reads only `font`; it takes `font: Optional[str] = None`.
- **`map()`.** `map(int, header[1:6])` and `list(map(ord, list(text)))` are comprehensions.
- **A closure.** `loadFont()` defines `__char()`, which reads `loadFont()`'s `height` and `self`;
  it is the method `_load_char(data, height)`, with the same body but for the regular expressions
  (below), at its three calls.

**M4, dynamic values ([#9](https://github.com/den-run-ai/pystachy/issues/9)).**

- **A variable rebound to another type** (a variable has one type for its lifetime). In
  `loadFont()`, `data` is the font's text and then its list of lines: the text is `text`;
  `header` is the first line and then the list of its fields: the line is `header_line`; and `i`
  is an `int` (in the loops over ranges, and as a glyph's code) and a `str` (the German letters,
  and the text of a code): the loop over the letters names its variable `ch`, and the text of a
  code is `code`.
- **A tuple of two types.** `getLastBlank()` returns `-1, -1`, or a list and an int; it returns
  `[], -1`. Its caller reads only the `-1`.
- **A tuple that grows.** `smushChars()` starts `smushes = ()` and adds pairs with `+=` (`expected
  tuple[], got tuple[tuple[str,str]]`): it is a `list[tuple[str, str]]`.
- **Optional values.** `getCurWidth()` is an `int | None`, which `addCharToProduct()` stores in
  the `int` field `curCharWidth` once it has tested `curChar`, which is `None` exactly when the
  width is: the width is a local, narrowed by `assert ... is not None`. `smushChars()` returns a
  `str | None`, which `updateSmushedCharInLeftBuffer()` stores in a list of `str` before
  `''.join()` joins it, where a `None` raises `TypeError: sequence item N: expected str instance,
  NoneType found`; the port raises that error before the store.
- **A function that falls off its end.** `Figlet.justify` returns `None` when `justify` is
  `'auto'` and the direction is neither left-to-right nor right-to-left, as with
  `Figlet(direction='sideways')`, and then nothing justifies the text. Declared `-> str`, it raised
  `RuntimeError: justify() ended without returning a value` (the documented deviation for a
  function that ends without a `return`; the first version of this port did, and its verifier
  caught it): it is `-> Optional[str]`, and so are the `justify` parameters of
  `FigletBuilder.__init__` and `justifyString()`.

**M7, the long tail ([#12](https://github.com/den-run-ai/pystachy/issues/12)).**

- `RESET_COLORS = b'\033[0m'` runs at import (`bytes literals are not supported`): it is the
  `str` `'\033[0m'`, which `print_figlet()` (left out) decoded.
- `unicode_string`, computed with `str.encode()` and `bytes.decode()` (above).
- `FigletString`'s `reverse()` and `flip()` use `str.translate()` and slice steps; they stay
  uncompiled with the class.

**Native stdlib hubs ([#11](https://github.com/den-run-ai/pystachy/issues/11)).**

- The imports of `itertools`, `importlib.resources`, `pathlib`, `re`, `shutil`, `zipfile` and
  `optparse` are commented out: Pystachy has none of these modules.
- **The fonts.** `preloadFont()` looks for `<font>.tlf` and then `<font>.flf` in the package's
  `fonts/` (`importlib.resources`), in the current directory and in `/usr/local/share/pyfiglet/`,
  and reads the first file of a font that is a zip archive (`zipfile`, `pathlib`). It returns
  `FONTS[font]` from `_fontdata.py`, or raises `FontNotFound(font)` as upstream does when it finds
  no file. Upstream's body is `preloadFont_upstream()`, which nothing calls.
- **Regular expressions.** The class attributes `reMagicNumber` (`^[tf]lf2.`) and `reEndMarker`
  (`(.)\s*$`), and the pattern `<end mark>{1,2}\s*$` that `__char()` compiled for each glyph, are
  three functions of string operations: `_magic()`; `_end_marker()`, the last character that is
  not whitespace, or the first of a line of whitespace, and for an empty line the
  `AttributeError` that `.group()` of no match raised, which `loadFont()` reports as a
  `FontError`; and `_strip_end()`, the line up to the first end mark that at most one more end
  mark and then only whitespace follow, which is the leftmost match that `sub()` removed.
  `re.sub(r"[\u0085\u2028\u2029]", " ", data)` is three `str.replace()`s,
  `reMagicNumber.sub('', header)` is `header_line[5:]` (the match is 5 characters long) and
  `re.search('^0x', i, re.IGNORECASE)` is `code[:2].lower() == '0x'`.

**Outside the roadmap: iterating a `str` gives bytes.** Pystachy's `str` holds UTF-8, and
iteration steps through its bytes ([docs/language.md](../../docs/language.md#deviations-from-cpython)).
`loadFont()` reads the glyphs of the German letters, which follow `~` in a font, by iterating
`'ÄÖÜäöüß'`, and `FigletBuilder` made the code points of its text with `list(map(ord,
list(text)))`. Iterating bytes, `loadFont()` read 14 glyphs for the 7 letters, keyed by the bytes
of their UTF-8 (0x84 to 0xC3), and every glyph after them from the wrong lines: the standard font
had 237 glyphs instead of 236 and none of the 7 letters, and `figlet_format("é")` drew the glyph
read for its first byte, 0xC3, whose last row was the font's line `165  YEN SIGN`, where CPython
draws nothing (the standard font has no `é`). `_chars()`, added, returns the characters
of a `str`, each as long as its UTF-8 lead byte says (`ord()` of a whole character is its code
point), and both loops iterate it. It tests `_UTF8_STR = len('\u00e9') == 2`, so under
CPython each item is one character and the edited module prints what upstream prints.

## What compiles as it is

The font parser but for the edits above: the header's optional fields (`printDirection` and
`fullLayout` start as `None` and may become `int`s), the conversion of an old layout with `&` and
`|`, the comment lines, `''.join(letter) != ''` and `int(code, 16)` of a `0x` code; its
`try`/`except Exception as e` that re-raises as `FontError` with `%` of the exception. The whole
rendering engine: `FigletBuilder`'s smushing (`smushAmount()` with `rstrip(' ')` and
`lstrip(' ')`, `smushChars()` with the hierarchy, pair and big-X rules over the `SM_*` constants,
which are fields), wrapping at the last blank or the last character (a `list[tuple[list[str],
int]]` of saved buffers, `pop()` and `IndexError`), justification (`' ' * int((width - n) / 2)`),
right-to-left printing, hard blanks, and `FigletRenderingEngine`, whose `base` is an
`Optional[Figlet]` from `from __future__ import annotations`. The exception classes (`FigletError`
with its own `__init__` and `__str__`, and `CharNotPrinted`, `FontNotFound`, `FontError` and
`InvalidColor`, which only have docstrings), the `COLOR_CODES` dict, the `sys.platform` branch, the
re-export of `__version__`, mutable default arguments (`buffer: list[str] = []`), and the
`if __name__ == '__main__':` block, which the loader drops. Functions that use what the port leaves
out stay in the source, unedited: Pystachy compiles a function only where a program calls it.

## What the port leaves out

- **The other fonts.** The sdist has 550 FIGlet fonts (`.flf`), 21 TOIlet fonts (`.tlf`, 12 of
  them zip archives) and 4 control files (`.flc`, which pyfiglet does not read). Another `.flf`
  font is one more literal in `_fontdata.py`, and 482 of the 550 are ASCII as these three are. The
  other 68 have glyphs drawn with other characters (box drawing, block elements), which Pystachy
  measures in bytes (see Deviations): they are not embedded.
- **Fonts from files**: the current directory, `/usr/local/share/pyfiglet/`, zip archives,
  `FigletFont.getFonts()`, `isValidFont()`, `infoFont()` and `installFonts()` (they need
  `importlib`, `pathlib`, `zipfile`, `shutil`, `re` and `itertools`: #11), and `Figlet.getFonts()`.
- **`FigletString`**: `renderText()` returns a `str`, and a program that calls `.reverse()`,
  `.flip()`, `.strip_surrounding_newlines()` or `.normalize_surrounding_newlines()` on it is
  rejected at compile time (M2, M7).
- **Colors and the command line**: `print_figlet()` (`**kwargs`), `color_to_ansi()` and
  `parse_color()` (a variable that is an `int` or a `str`, M4, and `str.format()`, M7), and
  `main()` (`optparse`, and `bytes` written to `sys.stdout.detach()`).
- Arguments that CPython takes and Pystachy rejects at compile time: `Figlet.direction` and
  `Figlet.justify` read as properties (they are methods), keywords of `figlet_format()` other
  than `direction`, `justify` and `width` (upstream passes them on to `Figlet`, which raises
  `TypeError`), and keywords of `setFont()` other than `font` (which upstream ignores).

## Deviations it hits

- **`str` is UTF-8 bytes** ([docs/language.md](../../docs/language.md#deviations-from-cpython)).
  With `_chars()`, text with any characters renders as in CPython (`figlet_format("ŁódźŻółć ĄĘ",
  width=200)` draws the standard font's Latin Extended-A glyphs, and characters no font has, such
  as `€`, `😀` and `日`, are skipped). What a program computes from a `str` itself counts bytes,
  and so would a font whose glyphs are drawn with characters outside ASCII: in `ansi_shadow`,
  whose glyphs are made of `█`, `╗` and the like (3 bytes each), each row of a glyph measures up
  to 3 times its width: embedded the same way, `figlet_format("wrap these words",
  font="ansi_shadow", width=40)` put each of the 14 letters on a row of glyphs of its own (98
  lines) where CPython puts up to four on a row (35 lines), and `justify="center"` indented the
  rows of `Hi` by 8 or 10 spaces where CPython indents them all by 19. The three embedded fonts
  are ASCII, and so is their output.
- **`int` is 64-bit.** The arithmetic is on widths and code points. A width of 2**63 - 1 renders
  as in CPython when the text is left-justified (the tests pass 9223372036854775807), but a
  program cannot make a bigger one: `figlet_format("Hi", width=2 ** 63)` renders in CPython, and
  Pystachy raises `OverflowError: integer result does not fit in 64 bits` computing `2 ** 63`.
  Centred or right-justified, such a width makes a string of about `width / 2` or `width` spaces:
  for `figlet_format("Hi", font="small", justify="center", width=9223372036854775807)`, CPython
  raises a `MemoryError` that `except MemoryError` catches, and a Pystachy program ends there with
  `MemoryError` and status 1, as the documented deviation for running out of memory says.

## Tests

`tests/port_pyfiglet_render.py` runs the cases of pyfiglet's own test, `pyfiglet/test.py` in the
sdist, which renders four texts in each font with one `Figlet` object whose `setFont()` changes
and compares each with what the C `figlet` prints: one word, a text cut at its spaces, a long word
cut at its last character, and an explicit new line, for the three embedded fonts, printed line by
line with `repr()` as `test.py`'s `dump()` does; then `test.py`'s four banners, in the default
font at the default width of 80. `tests/port_pyfiglet_edges.py` takes the edge cases the port and
its verifier met: what the parser reads from each font (header fields, comment, glyph counts and
widths, the 7 German letters and the Latin Extended-A glyphs, and the glyph of `@`, whose rows hold
`@`s besides their end marks); every justification, a justification and a direction pyfiglet does
not know (`'middle'`, `'sideways'`); right to left; wrapping at blanks and inside a word, at widths
around the glyph `M`'s 9 columns and at 9223372036854775807; `CharNotPrinted` at widths 8, 0 and
-5; new lines, tabs, carriage returns, blanks and empty text; Latin-1 and Latin Extended-A letters,
and `€`, an emoji and CJK characters, which no font has; every printable ASCII character in each
font; `setFont()`; `FontNotFound` for a missing name, a path and `''`; and a `FontNotFound` that
nothing catches, which ends the program as CPython reports it (`tests/port_pyfiglet_edges.err`).
Each of its parts is a function, so that the fonts it loads are garbage when it returns (below).

`tests/run.sh` compares what they print with CPython's, JIT and AOT. Run under CPython against the
unmodified upstream package, both print exactly what they print against this port. Both pass JIT
and AOT with `PYSTACHY_IRCHECK=1`, with the native compiler and the CPython-hosted one, with
`PYSTACHY_OPT=-all`, and `tests/run.sh` passes as a whole (1,935 passed, 0 failed). They stay
small in the gc-stress form of `make verify` (the compiler collecting every 1,000 allocations, the
program at every allocation), where the JIT run and the AOT build and run of `port_pyfiglet_render`
take 6.3 s of CPU together (2.6 s, 1.1 s and 2.6 s) and those of `port_pyfiglet_edges` 7.8 s
(2.5 s, 1.4 s and 3.9 s). Without gc-stress, each JIT run takes 0.2 s
of CPU, each AOT build 1.0 s and 1.3 s, and each AOT run 0.02 s. Under gc-stress, each collection
scans what is live, and a parsed standard font holds about 1,400 strings (236 glyphs of 6 rows):
in a probe, a standard font kept in a module-level variable doubled the cost of five renderings in
the small font after it (0.28 s to 0.59 s of CPU), and a `del` of the variable did not undo it
(0.63 s). The edges test took 11.7 s before its parts became functions.

## Speed

**Run time.** The headline workload: a `Figlet` made for each of the three fonts (which loads and
parses it) and a 220-character text rendered at width 200, 40 times each, every other time
centred; and the same text rendered 80 times in each font by three `Figlet`s made once. Median of
3 runs, wall clock with process start-up and CPU time, on a 4-core x86-64 VM that was running other
jobs (load 4):

| | load and render: wall | CPU | render only: wall | CPU |
|---|---:|---:|---:|---:|
| Pystachy AOT executable, this port | 0.377 s | 0.257 s | 0.547 s | 0.371 s |
| CPython 3.13.16, unmodified pyfiglet 1.0.4 | 0.894 s | 0.695 s | 1.296 s | 0.978 s |

That is 2.4 times faster in wall clock and 2.7 times in CPU time with the font loads, and 2.4 and
2.6 times rendering only. Two more sets of runs, at load 12, gave CPU ratios of 2.6 to 2.7 for
both, and wall-clock ratios of 2.2 to 2.7. pyfiglet has no C extension, so CPython runs the same
Python code; but where the port reads its fonts from strings in the executable, upstream reads
each font's file (28 KB for the standard font) and checks whether it is a zip archive every time a
`Figlet` is made. The rendering itself is string work: each glyph row joined to the line by
slicing and concatenation, and `getCharAt()` copying the text's list of code points (`len(list(
self.text))`) for each character.

**Build time and size.** `pystachy build` of a program that imports pyfiglet and prints
`figlet_format("Hi")` takes 1.0 s of CPU (1.3 s of wall clock on the loaded VM), against 0.15 s
for `print(1)`, and makes a 174 KB executable (28 KB for `print(1)`) that holds the three fonts
(56 KB of text) and needs no files at run time.
