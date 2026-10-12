# Foreign functions: C, and CPython in both directions

Status: **prototype**, proposed as the decision record that issue
[#4](https://github.com/den-run-ai/pystachy/issues/4) §4 asks for (see
[history.md](history.md#open)). One of the three directions is built, calling C; the other two
are designed [below](#next-cpython-calls-pystachy-pystachy-ext) and come next. Nothing here
changes a program that does not use it: such a program compiles to the same LLVM IR, byte for
byte, as without this work (`make irsame`).

| direction | how | tiers |
|---|---|---|
| Pystachy calls C | `@ffi.extern("lib")` on a typed `...` stub, looked up in the library's own handle as ctypes does | JIT and AOT, from the same IR |
| Pystachy calls CPython (next) | `lib/pyobj.py`: CPython's stable ABI through `@ffi.extern`, CPython embedded | JIT and AOT (AOT the reference) |
| CPython calls Pystachy (next) | `pystachy ext NAME.py`: an abi3 or abi3t extension module of `@ffi.export` functions | AOT only |

Each direction keeps Pystachy's contract: a program prints what CPython prints, or is rejected
at compile time with `file:line: error`. CPython's side is defined by *twins*: the
`tools/rt_cpython` directory holds a plain-Python `ffi.py` (ctypes for `extern`), so every file
that uses the FFI also runs under CPython, and that run is the oracle:

    PYTHONPATH=$PYSTACHY_HOME/tools/rt_cpython python3 prog.py   # what prog.py must print

The twins are the specification: the native code makes the twins' checks with the twins'
messages, and a program may use only what the twins offer (anything else is a compile-time
error). What still differs is listed under [Deviations](#deviations).

## Why this design

- **Calls out work in both tiers, calls in only AOT.** A call from Pystachy to C goes through an
  address the program looks up itself, and lib/pyobj.py's calls to CPython bind to the libpython
  that lli loads or the linker links, so `pystachy run` and `pystachy build` run the same IR.
  CPython, though, imports only shared objects, and `pystachy run` is a separate lli process. A
  JIT inside CPython does work (LLVM's ORC through libLLVM's C API, or llvmlite), but it would
  load a 117–123 MB libLLVM, or llvmlite's LLVM 22 (about 170 MiB installed, for IR written for
  LLVM 18), into every process that imports a module, through an LLJIT C API whose header says it
  is not stable; an extension module imports in under a millisecond. A compile-on-import cache,
  still AOT underneath, can give a quick edit loop later.
- **Typed stubs, not C headers.** The compiler reads no header, which would take libclang, a second
  toolchain. LLVM IR does not lower C's calling conventions for aggregates, so what crosses is C
  integers of a stated width, `double`, pointers and strings; a struct, varargs or a callback goes
  through a small C shim. Codon, Julia's `@ccall` and LPython declare C functions the same way.
- **Looked up when the `def` runs, as ctypes does.** Nothing is linked: the library is opened with
  `dlopen` and the symbol found in its own handle, so `pystachy run`, an AOT build and CPython with
  the twin call the same function, and lli's own libraries cannot shadow it.
- **CPython's stable ABI, declared by hand.** Every C API operation the glue needs is an exported
  stable-ABI function (`Py_IncRef`, `PyObject_Vectorcall`, `PyErr_GetRaisedException`, ...), so the
  glue declares them itself instead of including `Python.h`: the ABI is what the glue declares, and
  building needs no Python. abi3 serves CPython 3.12+ GIL builds and abi3t (PEP 803) 3.15+ GIL and
  free-threaded builds, from the same program IR. HPy is no longer maintained, and PEP 809's new
  stable ABI is still a draft.
- **Wrappers now, a typed-IR lowering later.** [typed-ir.md](typed-ir.md) §7.4's CPython lowering
  (containers as Python objects, references counted from liveness) needs the IR's step 16 and
  recoverable elaboration first. Here Pystachy keeps its own values and runtime and converts at the
  boundary, behind the same `@export` entry points, which §7.4 can lower another way later.
- **Scalars and str first.** As [#108](https://github.com/den-run-ai/pystachy/issues/108) and #4 §4
  ask, no container is copied across: a copy would lose identity and shared mutation, which need an
  explicit contract first.

## Calling C: `@ffi.extern`

    from ffi import extern, string_at, c_int, c_uint, c_size_t, c_void_p

    @extern("libz.so.1")
    def adler32(adler: c_uint, buf: str, n: c_uint) -> c_uint: ...

    @extern("")                      # the process's own libraries (libc, libm)
    def strdup(s: str) -> c_void_p: ...

    @extern("", "free")              # a C symbol under another Python name
    def c_free(p: c_void_p) -> None: ...

    p = strdup("Wikipedia")
    print(string_at(p, 9), adler32(1, "Wikipedia", 9))
    c_free(p)

`extern(lib, symbol="")` takes the library and the C symbol as string literals, by position or
keyword as the twin's signature takes them (`@extern(lib="libm.so.6")`,
`@extern("", symbol="free")`); a symbol left out or empty is the function's own name, as the
twin's `symbol or f.__name__` is.

When the `def` statement runs, the C function is looked up as `ctypes.CDLL(lib or None)` finds
it: `dlopen(lib, RTLD_NOW | RTLD_LOCAL)`, then `dlsym` in that handle (`pys_c_bind`), and the
stub calls it through the address it stored. A missing library raises `OSError` there, and a
missing symbol `AttributeError`, each with `dlerror()`'s text, as ctypes does. The library is a
platform soname or a path, passed as it is to dlopen and to ctypes; nothing is linked. Under
`pystachy run` the process is lli, whose own libraries (LLVM's dependencies: libz, libzstd,
libedit, libffi, libxml2, ...) are in the global scope; the handle lookup does not see them, and
the library is opened with `RTLD_DEEPBIND` there, so that its own calls bind as in an AOT build.

| annotation | C type | checks |
|---|---|---|
| `ffi.c_int` | `int` (32 bits, sign-extended) | `OverflowError` outside [-2**31, 2**31) |
| `ffi.c_uint` | `unsigned int` (zero-extended) | `OverflowError` outside [0, 2**32) |
| `ffi.c_int64`, `ffi.c_ssize_t` | `int64_t`, `ssize_t` | |
| `ffi.c_uint64`, `ffi.c_size_t` | `uint64_t`, `size_t` | an argument must be >= 0; a result must be below 2**63 |
| `ffi.c_void_p` | a pointer, carried as an int (NULL is 0) | |
| `float` | `double`, as it is (the sign of zero, infinities and NaN too) | |
| `str` | `const char *` to the str's UTF-8 bytes, NUL-terminated, valid during the call | `ValueError` for a NUL in it |
| `ffi.c_buf` (argument) | the same pointer, NULs allowed (pass the length separately) | |
| `str` (result) | a `char *` copied into a new str | `ValueError` for NULL |
| `str \| None` (result) | the same, NULL is `None` | |
| `None` (result) | `void` | |

A call binds its arguments as the `def`'s own parameters do: by position or keyword, with the
defaults it declares (the twin binds them with `inspect.signature`). `ffi.string_at(addr, n)`
copies n bytes at addr into a str (`ValueError` for n < 0, where ctypes would read up to a NUL).
In the C stub's own types, `c_int` and friends are `int`, so a C integer is an ordinary int
everywhere else.

Rejected at compile time, each with its own message (tests/ffi/errors): a bare `int` (say
which C integer type: without the header the compiler cannot know its width), `bool`,
containers, classes and other optionals; a body other than `...`; a parameter without an
annotation, or `*args`; a library or symbol that is not a string literal, or that has a NUL
character in it (ctypes raises `ValueError: embedded null byte` for the library's, and would
look the symbol up only as far as the NUL); arguments that `extern(lib, symbol="")` does not
take, with CPython's `TypeError` message (an unknown keyword, a second value for `lib` or
`symbol`, a third argument, no library); `@extern` on a method; one C symbol declared twice
with different types, or with other types than the runtime's own declaration of it (`memchr`,
`fabs`, ...); and a reserved symbol (`pys_*`, `pyx_*`, `PyInit_*`, `PyModExport_*`, `main`).
Structs by value, varargs and callbacks are not offered: write a small C shim with scalar
arguments and put it in a library.

A call of an `@extern` function may do anything as far as the compiler knows (every effect;
inside a `try` it is an `invoke`). A C++ exception or a `longjmp` across Pystachy frames, a C
function that keeps a str's pointer after it returns, or a declaration whose widths are not
the C prototype's, are undefined behaviour, as with ctypes. Once a C function has been looked
up, Pystachy writes and reads floats in the C locale whatever `setlocale` a C function calls.

A program's own `ffi.py` (or `ffi/` package) on its module path comes first, as under CPython:
Pystachy's builtin `ffi` is then not used (tests/ffi_own.py).

## Next: CPython calls Pystachy (`pystachy ext`)

Not built yet; designed and prototyped as follows. `pystachy ext NAME.py` compiles a module whose
public functions are `@ffi.export` (positional `int`, `float`, `bool` and `str` in, one of those or
`None` out) into an extension module: `NAME.abi3.so` for CPython 3.12+ GIL builds, or
`NAME.abi3t.so` (PEP 803, entry `PyModExport_NAME` of PEP 793) for 3.15+ GIL and free-threaded
builds, from the same program IR. The program, the runtime and a header-free C glue (`pyext.c`)
become one module whose only visible symbol is the entry. Every entry ends in a catch-all landing
pad, so no Pystachy exception unwinds through CPython's frames; the outermost entry's frame bounds
the collector's stack scan; only the importing thread may call; `print()` and `input()` go through
the host's `sys.stdout` and `sys.stdin`. The twin `ffi.export` is a wrapper with the same checks, so
the module's source run under CPython is the oracle.

## Next: Pystachy calls CPython (`lib/pyobj.py`)

Not built yet; designed and prototyped as follows. `pyobj` is plain subset code (`lib/pyobj.py`)
that declares about 35 functions of CPython's stable ABI with `@extern("python")`, where `python`
means the libpython named by `$PYSTACHY_LIBPYTHON` (CPython 3.12 or later): `pystachy run` loads it
into lli (`-dlopen`), and an AOT build links it. Its API is `Object` (`attr`, `call`, `[]`, `len`,
`to_int`, `to_float`, `str`, `repr`, `close`), `import_module`, `of_int`, `of_float`, `of_str` and
`of_list`, and its twin `tools/rt_cpython/pyobj.py` is the same API over live objects. CPython starts
as `python3` starts it (PEP 538 and 540), Pystachy's and Python's output and input are one stream in
order, a Python exception arrives as the nearest class Pystachy has, an `Object` owns one reference,
and a dropped one is released after a collection (each counted with its `sys.getsizeof()`, so
dropped large objects start collections), or at exit, when CPython is finalized.

## Deviations

Against CPython running the same files with the twins (tools/rt_cpython):

- **str** is byte-indexed UTF-8 inside Pystachy, in either direction (the existing deviation,
  [language.md](language.md#deviations-from-cpython)). A C string that is not valid UTF-8, from
  `string_at` or a `-> str` result, is read as it is, where the twin's decode raises
  `UnicodeDecodeError` (as files are read).
- **Which process looks a symbol up.** `@extern("")` means the process's own libraries:
  python3 links libz and libexpat, lli has LLVM's dependencies loaded, and an AOT build has only
  libc and libm (`zlibVersion` is found by the twin and by `pystachy run`, and is an
  `AttributeError` at the `def` of an AOT build). Name the library. Likewise, a library's own
  calls of a function that the process's global scope also defines may bind differently in
  python3's process (its libz) than in an AOT build; `pystachy run` binds them as an AOT build
  does.
- **C's stdio** output from an `@extern` function interleaves with `print()` only as the two
  buffers are flushed.
- **Float text** is the C locale's whatever a C function's `setlocale` says, as CPython's own
  float conversions are; format type `'n'`, which CPython takes from the locale, is the C
  locale's too.

## Limitations

- **Platforms:** x86-64 Linux (LP64, Itanium unwinding, glibc) is what is tested. macOS has no
  `RTLD_DEEPBIND`; Windows is out of scope.
- **Not yet:** structs by value, varargs and callbacks into Pystachy from C (write a small C shim
  with scalar arguments).

## Invariants for maintainers

- **Pay for use.** `@extern` is opt-in: `-ldl` is linked only into programs that look C
  functions up, and the C locale for floats stays unset otherwise, at the cost of a test of a
  null pointer per conversion. `make irsame` against the commit before the FFI must find every
  corpus program identical; `ffi` is left out of the missing-module message for that reason.
- **No Python to build.** Nothing includes `Python.h`, and the driver never runs python3, so the
  Python-free stage of `make verify` still rebuilds everything.
- **The twins are the API.** A change to a check, a message or a name changes the twin and the
  native code together; `tests/ffi/run.sh` compares them against output CPython recorded with
  the twin.
- **One thread.** The runtime is single-threaded and has no TLS (lli cannot relocate native TLS
  in an extra object); a C library's own threads must not touch Pystachy's memory.

## Tests

| command | what it checks |
|---|---|
| `make test-ffi` (`tests/ffi/run.sh`) | `tests/ffi/c_*.py` JIT and AOT against output CPython recorded with the twin (a test library, `tests/ffi/ffitest.c`, whose names lli's libraries also define; a missing library and symbol), under GC stress; `tests/ffi/errors/*.py` rejected with their messages |
| `make test` | `tests/ffi_own.py`: a program's own `ffi` module comes first |
