# pyaes 1.6.1, ported to Pystachy

[pyaes](https://pypi.org/project/pyaes/) is Richard Moore's AES in pure Python: the block cipher
of FIPS-197 for 128-, 192- and 256-bit keys, the five common modes of operation on top of it
(ECB, CBC, CFB, OFB and CTR), and a stream API (`Encrypter`, `Decrypter`) that feeds data through
a mode with PKCS#7 padding. It has no dependencies, and 1.6.1, from 2017, is its last release.
It is rank 2,018 on PyPI in October 2026, and deps.dev lists 260 packages on PyPI that depend on
pyaes 1.6.1 directly (901 in all). Its users take it as the AES that works where nothing faster
is installed: Telethon, the Telegram client library, requires it, and builds Telegram's AES-IGE
mode from `pyaes.AES`'s `encrypt` and `decrypt` of one block, a list of ints, when neither
`cryptg` nor OpenSSL's libssl is available (`telethon/crypto/aes.py`, in 1.45.0 too). Electrum,
the Bitcoin wallet, keeps it as the last of its three AES backends (`AESModeOfOperationCBC` and
the stream API), after pycryptodomex and `cryptography`, one of which it now requires.

This port is the block cipher, `pyaes.AES`, the part Telethon calls: the key expansion for the
three key sizes, and `encrypt` and `decrypt` of one block of 16 ints. Keys and blocks are lists
of ints, as Pystachy has no `bytes` yet. These are two of the modules of the sdist
`pyaes-1.6.1.tar.gz` (SHA-256
`02c1b1405c38d3c370b085fb952dd8bea3fadcee6411ad99f312cc129c536d8f`), MIT licensed (`LICENSE`,
the sdist's `LICENSE.txt`).

| file | upstream SHA-256 | edits |
|---|---|---|
| `__init__.py` | `e20e2b5dedefe93c7259df8f59f017de1fad737b45f48074a36b09d6010226e7` | 2 regions |
| `aes.py` | `5dc0ff7ad948704ae9814fc2720f9b479599092a7a46e1fd9d55b78953a1a43f` | 12 regions, and `xrange(` written `range(` on 21 lines |

`blockfeeder.py` (the stream API) and `util.py` (its padding) are left out, and so is the rest of
the sdist: `setup.py`, the README and `tests/`, whose programs compare pyaes with PyCrypto on
random keys and data. Every edit is marked `# Pystachy port:` in the source, each of the 21
renamed lines with `# Pystachy port: xrange` at its end, and `diff -u` against the sdist's
`pyaes/` shows them all.

## The edits, and the feature each one stands in for

**Full classes (M2, [#7](https://github.com/den-run-ai/pystachy/issues/7)).**

1. `AES.__init__(self, key: list[int])`, `encrypt(self, plaintext: list[int]) -> list[int]` and
   `decrypt(self, ciphertext: list[int]) -> list[int]` are annotated (3 regions). Pystachy
   compiles a class only if its methods' parameters are annotated (`class pyaes.aes.AES is not
   supported: parameter 'key' of method __init__() has no type annotation`), and a method that
   returns a value needs a return annotation. With M2's classes as templates, the methods would
   be compiled for the types they are called with; with `bytes` (M7), for a `bytes` key too.
2. The fields `self._Ke` and `self._Kd`, the round keys, are annotated `list[list[int]]` (2
   regions): Pystachy does not type a field by a list comprehension (`cannot infer the type of
   field '_Ke'; annotate it`).
3. `AESModesOfOperation = dict(ctr=AESModeOfOperationCTR, ...)`, a table of the mode classes, is
   left out, and its name with it from `aes.py`'s `__all__` and the package's `from .aes import`
   (3 regions): classes are not values, and Pystachy's `dict()` takes no keyword arguments
   (`keyword argument 'ctr' of dict() is not supported`). Without the name in `__all__`,
   `from pyaes.aes import *` still works, here as under CPython.

**Functions as values (M3, [#8](https://github.com/den-run-ai/pystachy/issues/8)).**

4. `aes.py`'s Python 2 shim is left out (1 region):
   ```python
   try:
       xrange
   except Exception:
       xrange = range
       def _string_to_bytes(text): ...   # and _bytes_to_string, _concat_list
   ```
   Pystachy rejects each part of it. The feature test reads a name that is not defined (`name
   'xrange' is not defined`): Pystachy reports at compile time the errors that types rule out
   and CPython raises as it runs, also in a `try` that catches them
   ([docs/language.md](../../docs/language.md#rejected-rather-than-miscompiled)).
   `xrange = range` binds a builtin function as a value (`the builtin 'range' cannot be used as
   a value`), and so would a one-line alias at the top of the module. The three `def`s are
   inside a block of the module's code (`a def statement inside a block of a module's code
   ... is not supported`), and bind again names that the module's own `def`s bound before,
   which M3 is to allow. In place of the alias, `xrange(` is written `range(` on all 21 lines
   that call it, also in `Counter` and the modes of operation, which Pystachy does not compile
   (`Counter` runs under CPython from the port as from upstream). The three helpers convert
   between lists and `bytes` (M7) for the modes of operation; the block cipher does not use
   them.
5. The package no longer imports `blockfeeder` (`Encrypter`, `Decrypter`, `encrypt_stream`,
   `decrypt_stream`, `PADDING_NONE`, `PADDING_DEFAULT`; 1 region of `__init__.py`). The module
   assigns its functions to the mode classes' attributes as it is imported
   (`AESBlockModeOfOperation._can_consume = _block_can_consume`: `function
   'pyaes.blockfeeder._block_can_consume' cannot be used as a value`), and its buffers are
   `bytes` (M7). `util.py`, which it imports, has a shim of the same kind: a feature test that
   reads `xrange`, and `def`s that bind its two helpers again in the `except` block.

**Native standard-library hubs ([#11](https://github.com/den-run-ai/pystachy/issues/11), M6).**

6. `import copy` and `import struct` are dropped (1 region): `module 'copy' is not supported: it
   is not a builtin module (...) and there is no copy.py on the module path`.
7. `t = copy.copy(a)` is `t = list(a)`, in `encrypt` and in `decrypt` (2 regions): `a` is a list
   of four ints, which both copy the same way.
8. `struct.unpack('>i', key[i:i + 4])[0]`, four bytes of the key read as a signed big-endian
   word, is `(_compact_word(key[i:i + 4]) ^ 0x80000000) - 0x80000000` (1 region): the module's
   own `_compact_word`, which reads a block's words, gives the unsigned word, and the XOR and
   the subtraction make it signed, so the round keys hold the values upstream's hold (the test
   prints some). Under CPython it gives what `struct` gives for the four edges (0, 2**31 - 1,
   -2**31, -1) and a million random words, of `bytes` and of lists. `struct` needs `bytes`
   too (M7, [#12](https://github.com/den-run-ai/pystachy/issues/12)).

Native `copy` and `struct` modules would undo 6 and 7, and with `bytes`, 8; classes as
templates would undo 1 and 2.

## What compiles as it is

`AES`'s class attributes: the dict `number_of_rounds` (`{16: 10, 24: 12, 32: 14}`) and 15 tables
of ints, `rcon` (30) and the S-boxes `S` and `Si` and the round tables `T1` to `T8` and `U1` to
`U4` (256 each), read through `self` in the methods; `len(key) not in (16, 24, 32)` and
`raise ValueError(...)`; round keys made by a comprehension of `[0] * 4` lists and filled by
`self._Ke[t // 4][t % 4] = tk[j]`; the key schedule's `while` loops, with `^=` on list items,
shifts and masks; `(s1, s2, s3) = [1, 2, 3]`; slices of a block passed to `_compact_word`, an
unannotated module-level function (a template); the methods' docstrings; and in the package,
`VERSION = [1, 3, 0]` (which 1.6.1 has not updated) and the relative `from .aes import ...`.

## What the port leaves out

- The modes of operation, `AESModeOfOperationECB`, `CBC`, `CFB`, `OFB` and `CTR`, and `Counter`.
  They stay in `aes.py`, unchanged but for `xrange`, and a program that uses one is rejected at
  compile time: `class pyaes.aes.AESModeOfOperationCTR is not supported: class inheritance is
  not supported (...)` (M2), and `Counter`'s `__init__` takes an unannotated `initial_value`.
  They also make properties of lambdas (`value = property(lambda s: s._counter)`, M2 and M3)
  and convert `bytes` (M7). Pystachy compiles a function or class of an imported module only
  where a program uses it, so they do not affect `AES`. A program can build a mode on `AES`, as
  Telethon builds IGE: the test builds counter mode in 11 lines, and its ciphertext of the
  README's example is the one the README lists, as is upstream's `AESModeOfOperationCTR`'s.
- The stream API and its padding (edit 5), and `AESModesOfOperation` (edit 3).
- `bytes`: `pyaes.AES(b"0123456789abcdef")` is a compile-time error (`bytes literals are not
  supported (there is no bytes type)`). Under CPython, the port's `AES` takes a `bytes` key as
  well as a list of ints.
- The range that `bytes` gives a key's ints, 0 to 255: the port does not check it. Upstream's
  key must be `bytes`, which cannot hold other ints (`bytes([256] * 16)` raises `ValueError:
  bytes must be in range(0, 256)`), but a list can, and the port's `AES` takes it without an
  error, here as under CPython. Its round keys then hold more than 32 bits, and such a key can
  act as another: `AES([2 ** 31] + [0] * 15)` encrypts and decrypts as `AES([0] * 16)` does. An
  int of 2**39 or more first in a word of the key overflows here, as in a block (below). Blocks
  are not affected: upstream's `encrypt` and `decrypt` take lists of any ints too.
- Under CPython, the port's modes of operation no longer take `bytes`. Without the shim,
  `aes.py` keeps its Python 2 helpers, which take and give `str` (`_string_to_bytes` is
  `list(ord(c) for c in text)`), so `AESModeOfOperationCTR(key).encrypt(b"hello")` raises
  `TypeError: ord() expected string of length 1, but int found` where upstream returns 5 bytes.

## Deviations it hits

- **`int` is 64-bit** ([docs/language.md](../../docs/language.md#deviations-from-cpython)). For
  keys and blocks of ints from 0 to 255, all that `bytes` can hold, nothing the cipher computes
  needs more than 33 bits. But the block cipher takes any ints, as upstream's does, and
  `_compact_word` shifts the first int of each word (items 0, 4, 8 and 12) left by 24 bits, so
  such an int of 2**39 or more, or below -2**39, overflows: `AES([0] * 16).encrypt([2 ** 39] *
  16)` raises `OverflowError: integer result does not fit in 64 bits` here, where CPython
  returns the encryption of a zero block, `[102, 233, 75, 212, ...]`, as no bit above the 32nd
  reaches the result. The second int of a word overflows at 2**47 and the third at 2**55; the
  last is not shifted. The test's blocks of 256, -1, 2**31, 2**39 - 1 and -129, and of ints just
  inside those limits in each place (2**63 - 1 and -2**63 in the last), give the same in both.
- **`str` is UTF-8 bytes.** The cipher takes no strings, but a program that makes a key or a
  block of text does: iterating a `str` gives its UTF-8 bytes here, so `[ord(c) for c in
  "0123456789abcdé"]` holds 16 ints, ending `195, 169`, and `AES()` takes it as a 128-bit key,
  where CPython's list holds 15 and `AES()` raises `ValueError: Invalid key size`. (Pystachy's
  list holds the bytes a CPython program gets from `"0123456789abcdé".encode()`.) The test
  makes its key and text of ASCII strings, which agree.

## Tests

`tests/port_pyaes_cipher.py` runs the known answers of the standards both ways: FIPS-197's
Appendix C (the key 00 01 02 ... and the block 00 11 22 ... ff, for each key size, with its
number of rounds), and the twelve ECB blocks of NIST SP 800-38A F.1, whose three keys are
FIPS-197's Appendix A examples, with the last round key of each expansion as Appendix A lists
it and the first as signed words (`8e73b0f7` is -1905020681, as `struct.unpack('>i')` reads it).
Then it encrypts a block 20 times over and decrypts it back, for nine keys of the three sizes;
keys whose words read as -1, -2139062144, 2**31 - 1, -2**31 and 0 (the edges of edit 8); blocks
of ints outside 0..255 (256, -1, 2**31, 2**39 - 1 and -129, and ints just inside the 64-bit
limits of each place in a word), which the cipher takes as upstream's does; a key list changed
after `AES()` has read it; counter mode built on `AES`, on the README's example; Telethon's
AES-IGE, on OpenSSL's IGE test vector (`test/igetest.c`) and with a 256-bit key; and the
`ValueError`s for keys of 0, 15, 17 and 33 ints and blocks of 0, 15 and 17. The known answers
are the standards' values, and OpenSSL (through CPython's `cryptography`) gives the same
ciphertexts. pyaes's own tests compare it with PyCrypto on random data, which the port cannot
run.

`tests/run.sh` compares what it prints with CPython's, JIT and AOT. Run under CPython against
the unmodified upstream package, with `AES.__init__` handed `bytes(key)` (upstream reads its key
with `struct.unpack`, which takes `bytes` only; that is the one adaptation), it prints exactly
what it prints against this port. It passes JIT and AOT with `PYSTACHY_IRCHECK=1`, also with the
CPython-hosted compiler and with `PYSTACHY_OPT=-all`.

It is one program rather than two because of its AOT build: building any program that uses
`pyaes.aes` takes 8.2 to 9.1 s of CPU time, where `print("hello")` takes 0.14 s and
`tests/port_iniconfig_api.py` 1.0 s. The time is clang's `-O2` over the module's code that
makes the 15 tables, one function of 3,614 list appends: `pystachy ir` takes 0.02 s, and a
class of the tables alone takes 7.5 to 8.2 s to build. The JIT run takes 0.26 to 0.28 s of CPU
time, and the executable 0.002 s. Under `make verify`'s gc-stress stage (the compiler collecting
every 1,000 allocations, the program at every allocation), the JIT run takes 0.37 to 0.44 s and
the AOT build and run 8.5 to 8.8 s and 0.06 s: 8.9 to 9.3 s of CPU time in all. On this 4-core
VM, running other jobs at a load of 10 to 14, the three steps took 9.2 to 16.3 s of wall-clock
time in four runs, almost all of it the AOT build.

## Speed

The headline workload is counter mode's: for each key size, 200,000 counter blocks encrypted,
with a checksum of the first and last byte of each and every 64th block decrypted back and
compared, 600,000 block encryptions and 9,375 decryptions in all (checksum 795704754 in every
row). Median of 3 runs, with process start-up, on a 4-core x86-64 VM:

| | wall clock | CPU time |
|---|---:|---:|
| Pystachy AOT executable, this port | 0.415 s | 0.278 s |
| CPython 3.13.16, unmodified pyaes 1.6.1 (`bytes` keys) | 14.002 s | 12.292 s |
| CPython 3.13.16, this port | 14.054 s | 11.760 s |
| CPython 3.13.16, `cryptography` 50.0.1 (OpenSSL), one block per call | 0.484 s | 0.394 s |

That is 44 times faster than CPython on upstream in CPU time, and 34 times in wall-clock time;
a second set of runs gave 0.285 s and 12.451 s of CPU time (44 times), and a third, with the
compiler of main at 4dc548a, 0.281 s and 12.190 s (43 times). The VM was running other jobs (a
load of 6 to 14 on its 4 cores), which spreads the wall-clock times; an earlier
measurement of a draft of this port on a quieter VM gave 0.32 s and 12.23 s of wall-clock time
(38 times). pyaes has no C extension: CPython runs it as Python everywhere, and programs that
need fast AES on CPython use a C library instead, such as `cryptography` or `pycryptodome`. For
scale, the last row runs the same loop with OpenSSL's AES through `cryptography`, one 16-byte
block per call: the executable's AES, pure Python compiled, takes less time than CPython
driving OpenSSL block by block.
