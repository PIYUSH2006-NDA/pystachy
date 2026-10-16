# How Pystachy works

Pystachy's compiler is written in the typed Python subset it compiles. A CPython-hosted
compiler and a native compiler use the same frontend, typed IR and LLVM lowering.
The runtime combines C with functions written in that subset.

For supported syntax and behavior, read the [language guide](language.md). For the IR's
contracts and passes, read [typed IR](typed-ir.md). The [testing guide](testing.md)
explains differential checks and bootstrap validation.

## Repository layout

| Path | Purpose |
|---|---|
| `pystachy.py` | Compatibility entry point for the hosted and self-hosted compiler |
| [`src/pystachy_compiler/`](../src/README.md) | Lexer, parser, scope checks, module loader, type checker, typed IR, LLVM lowering and driver |
| `runtime.c` | Allocation and collection, container storage, files, numeric support and exception unwinding |
| `runtime.py` | Runtime functions written in the subset; see [runtime in the subset](runtime-in-subset.md) |
| `lib/`, `ports/` | Standard-library modules and adapted third-party packages; see [library support](stdlib.md) |
| `ryu/` | Ryu's float-to-string conversion, with its upstream license; see [Ryu's README](../ryu/README.md) |
| `tests/`, `tools/` | CPython comparisons, rejection cases, IR probes, fuzzers and validation tools |
| `bench/`, `examples/` | Performance workloads and complete applications |
| `pyext.c`, `pyembed.c` | CPython extension glue; see [foreign functions](ffi.md) |

<a id="design-piece-by-piece"></a>

## Compilation pipeline

The frontend runs these stages before LLVM sees the program:

| Stage | Responsibility |
|---|---|
| `Lexer`, `Parser`, `Symtable` | Decode and parse source; check syntax and scope rules, including code that will not be compiled |
| `Loader` | Find imports, qualify module names, and resolve supported import-time decisions |
| `Flow` | Identify reads that need an assignment check |
| `Gen` | Declare interfaces, check and infer types, specialize templates, and build typed IR |
| IR passes and lowering | Compute effects, optimize eligible operations, lower exception handling, and print LLVM IR |

```mermaid
flowchart TD
    src["Python source"] --> frontend["Frontend and typed IR"]
    frontend --> llvm["LLVM IR"]
    llvm --> jit["run: ORC JIT"]
    llvm --> aot["build: native executable"]
    llvm --> ext["ext: CPython extension"]
    runtime["C and subset runtime"] --> object["Cached runtime object"]
    runtime --> bitcode["Cached runtime bitcode"]
    object --> jit
    bitcode --> aot
    bitcode --> ext
```

<a id="modules-by-renaming"></a>
<a id="syntax-first"></a>
<a id="one-pass-from-ast-to-ir"></a>
<a id="templates"></a>
<a id="functions-as-values-and-closures"></a>
<a id="definite-assignment"></a>

## Frontend and specialization

Imports become qualified names in one compiled program, rather than runtime module objects.
Each module has an initialization function that runs its body when first imported.
Definition-time checks preserve the relevant annotation, default-value and import behavior;
see the [module reference](language/modules.md).

`Gen` checks each function while building its IR. Expected types flow into expressions;
inferred types flow out. Static branches determine which bodies need checking, and
unannotated function parameters cause specialization at calls. Constructor-inferred class
templates create ordinary compiled classes for their field types. The
[typing reference](language/typing.md) describes the supported forms and limits.

Ordinary single-inheritance hierarchies carry a class tag. Base-typed instance-method calls
select a concrete implementation, then reuse method specialization for that receiver.
Inherited fields keep the base layout; unrelated classes retain their existing layout.
Explicit base calls and `super()` select a body directly while preserving the receiver.

A known function value can become a direct call. Closures keep captured variables in shared
cells, so `nonlocal` assignments remain visible. A typed `Callable` uses an adapter with a
code pointer and an environment pointer for indirect calls.

The preceding `Flow` pass marks reads it cannot prove initialized. Generated checks then
raise the appropriate error; LLVM can remove checks it proves redundant. Optional-value
narrowing is a separate typing concern.

<a id="the-typed-ir"></a>
<a id="ssa-by-delegation"></a>

## Typed IR and LLVM

The IR contains one `IFn` per compiled function, with basic blocks, instructions, loop
metadata and exception-handler metadata. Runtime signatures and effects come from the
`RUNTIME` table. Whole-program effect summaries support list-read and dictionary-lookup
optimizations and identify calls that need exceptional edges.

This separation is already used by JIT and AOT. It is incomplete: most loads, stores and
arithmetic remain `raw` instructions containing LLVM text. There is no second backend yet.
See [typed IR](typed-ir.md) for the exact boundary between shipped machinery and future work.

Locals start in entry-block `alloca` slots. LLVM's `mem2reg` builds SSA form; expression joins
also use explicit `phi` instructions. Each function's typed IR is released after lowering,
while its effect summary remains available.

<a id="one-value-model"></a>
<a id="type-descriptors"></a>
<a id="memory"></a>
<a id="python-semantics-in-the-runtime"></a>
<a id="a-runtime-partly-written-in-the-subset"></a>

## Values and runtime

Scalars use LLVM's `i64`, `double` and `i1`; strings, containers and objects use pointers.
Container elements occupy uniform eight-byte slots, allowing one runtime implementation to
serve multiple static element types. Optional reference values use null for `None`; optional
numbers use boxes. Integers use checked 64-bit arithmetic rather than CPython's arbitrary
precision.

Generic operations such as comparison, hashing, representation and sorting receive a compact
type descriptor. The runtime interprets nested container descriptors and calls generated helpers
for supported object methods. A dict's or set's descriptor of its keys tells objects hashed by
identity (their addresses, which the non-moving collector keeps stable) from those hashed by
their class's `__hash__`; a dict of the latter keeps CPython's hashes and an index of CPython's
size (other dicts' have twice the slots), so that its lookups probe CPython's slots in CPython's
order and call `__eq__` as often. Specialized code still has static types; these descriptors
do not introduce a dynamic `Any` type.

The collector is conservative, non-moving mark-and-sweep. It scans stack/register roots and
registered program globals; buffers that cannot contain pointers are not scanned. Unreachable
files close during collection or at program exit. Supported Python operations are checked
against CPython; the [compatibility reference](language/compatibility.md) lists deviations.

`runtime.py` is compiled in a restricted runtime mode using `_rt` primitives, then linked with
`runtime.c`. This reuses the compiler for string methods, formatting and numeric helpers.
The [runtime guide](runtime-in-subset.md) covers those primitives and their constraints.

<a id="reflection"></a>

## Reflection

Reflection (`reflection.py`; the language rules are in [reflection](language/semantics.md#reflection))
is decided at compile time wherever the static types decide it, and costs nothing where it is not
used. `getattr`, `setattr` and `hasattr` with a literal name become the attribute access they name;
a loop over a constant set of names (a display, a variable bound once and only iterated, `dir(x)`,
`dataclasses.fields(X)`, `vars(x).items()`) is unrolled, its body compiled once per name with the
name substituted as a literal, under a budget of 256 copies; `dataclasses.asdict()`/`astuple()`
are synthesized per class; `type(x).__name__` of a value whose class is fixed is a constant. A
program that uses none of these constructs compiles to the IR it compiled to before.

Where a run-time choice remains, the code dispatches on the value's exact type, the way method
calls already do: None first (where it may be), then a union's member tag, then an object's class
tag (`refl_split`). Each concrete class's arm then reads the class's **reflection record**, an
internal constant global that is emitted only for classes that reach such a site:

| Word | Contents |
|---|---|
| 0, 1, 2 | the class's `__name__`, `__qualname__` and `__module__` (string constants) |
| 3 | flags: has an instance `__dict__`, dataclass, frozen, in a hierarchy, builtin type |
| 4, 5 | the number of names and the **name table**: `{name, kind}` pairs sorted by their bytes, every name `dir()` lists (a field, a field that may be unassigned, a class attribute, a property, a method, a static or class method, an attribute of the object or its type, a slot never assigned) |
| 6, 7 | the number of fields and the **field table**: `{name, type descriptor, byte offset, offset of the "is assigned" flag or -1}` in the order CPython inserts them into the instance `__dict__` |

`@pys.refl.c.<Class>` is a class's record and `@pys.refl.b.<type>` a builtin type's
(`int`, `list`, `NoneType`, ...); a specialization of a class template has its own record for its
layout, while its identity is its template's (the class CPython has). The tables are separate
internal constants (`<record>.names`, `<record>.fields`), null until a site needs them: a record
made for `type(x).__name__` carries only its names. They are `Data` records (`classrec`,
`classnames`, `classfields`) that `lower_module.py` alone lays out, and the field table's offsets
are LLVM constant expressions over the class's `%C.<Class>` layout, so the compiler holds no
layout arithmetic. No new IR operation is needed: a site uses `phi`/`select` of record addresses
(`%ptr`), `mach.load` of a word, `scalar.cmp` of two addresses and two runtime calls.

| Construct | Lowering |
|---|---|
| `type(x).__name__` in a hierarchy or union | the dispatch's `phi` of record addresses, then a load of word 0, 1 or 2 |
| `type(a) == type(b)`, `type(a) is C` | a comparison of record addresses: the record is the class's identity |
| `str(vars(x))` | `pys_refl_vars(record, object)`: the runtime walks the field table, formatting each assigned field by its descriptor through the generic `repr` |
| `hasattr(o, name)`, the text of `getattr(o, name)`, `setattr(o, name, v)` with a run-time name | `pys_refl_find(record, name)`, a binary search of the name table, then a switch on the index at the site, whose arms do what CPython's lookup does for that name |

LLVM does the rest: `simplifycfg` turns the tag and index chains into `switch` instructions and,
where every arm yields a constant (most of `hasattr()`'s, the names of `type(x)`), into lookup
tables; a load from a record selected among constants folds into a select of the strings; string
constants are shared (`sconst`); and since records and tables are internal, `globaldce` (JIT) and
`llvm-link --only-needed` with `-O2` (AOT) drop those no code references, so a binary holds records
only for classes that reach a reflective site. `RUNTIME` declares `refl.find` without effects
and `refl.vars` with `A I rO rL rD U` (a field's `__repr__` may run user code).

**The extension path.** The record is the one per-class table format that #485's later steps
reuse instead of inventing their own:

- **Interface values (#488)**: an erased `{table, data}` pair for a `Protocol`-typed slot. Its
  table is a constant per (class, protocol) pair that flows into the slot; it starts with the
  address of the class's reflection record (so `type(x)`, `isinstance()` against a class and
  `type(x).__name__` of an erased value read it as here) and continues with the protocol's
  method specializations. Emission on demand, internal linkage and the "which classes reach this
  site" decision are `refl_record`'s; #488 adds the whole-program flow of classes into slots.
- **Object boxes (#487)**: a box `{descriptor, payload}` whose descriptor is the record of the
  payload's exact type (`@pys.refl.b.int`, `@pys.refl.c.Point`, ...), extended with the existing
  type descriptor string for builtin containers. `type(v).__name__` is word 0, `isinstance()`
  compares records (and a hierarchy's class tag), `repr()` uses the descriptor, and a run-time
  `getattr()` whose value is used becomes `pys_refl_find` plus a load through the field table's
  offset and descriptor into a new box: the value-free consumers of #489's first version are the
  same lookup with the value formatted at once.
- **`Any` and dynamic values**: a dynamic value is such a box; attribute access, method calls by
  name and `vars()` dispatch through the name table, whose method entries #488's tables supply,
  and properties through getter and setter thunks added to the name table's entries. As now,
  only classes whose values reach such a site get records, never every class of the program.

<a id="checked-arithmetic-cheap-errors"></a>
<a id="exceptions-by-table-driven-unwinding"></a>

## Errors and cleanup

Overflow, invalid receivers and uninitialized reads branch to shared cold error blocks.
For programs that use `try` or `with`, exception lowering gives may-raise calls explicit
unwind edges to LLVM landing pads. The runtime unwinds through native frames using its own
personality routine; local raises can branch directly to their handler.

Handlers match exception classes and rethrow unmatched exceptions. `finally` and `with`
cleanup run on the relevant normal and exceptional exits. Nested `finally` handling avoids
exponential duplication. The C runtime is compiled with exception support in both tiers.

Iterator objects are ordinary class objects. A loop, `in`, unpacking or `next(it, default)`
over one calls its `__next__` in a block whose landing pad catches only `StopIteration`
(and its subclasses), restores the exception being handled and leaves the loop; the loop
body itself stays outside that handler. `iter()` of a builtin container makes an object of a
class template in `lib/_pystachy_iterators.py`, which the loader adds to a program that calls
`iter()` and whose classes compile only when specialized.

<a id="whole-program-optimization"></a>
<a id="two-tiers"></a>

## JIT, AOT and runtime caching

`run` favors startup latency. LLVM removes unused internal functions, optionally inlines the
program's own functions, performs SSA cleanup, then ORC JIT runs with the cached runtime
object. The default inlining threshold is 20,000 lines of generated IR; larger programs skip
that pass. The precompiled runtime is not inlined into JIT code.

`build` links the runtime bitcode with the program and applies clang's `-O2` optimization
pipeline, allowing optimization across that boundary. `ext` builds a shared CPython module
with its boundary wrappers; see the [FFI guide](ffi.md).

Cached runtime artifacts depend on the runtime sources, included Ryu files, compiler,
LLVM tools and compilation flags. Changes invalidate the relevant cache. Builds use private
temporary files and publish reusable artifacts only after checking their inputs stayed stable.

<a id="bootstrap"></a>

## Bootstrap validation

CPython runs the compiler as stage 0. That compiler builds stage 1, and stage 1 builds stage 2.
The bootstrap checks that all three emit identical LLVM IR for the compiler and `runtime.py`.
This fixed point catches disagreements that affect self-compilation; differential tests
provide the broader behavior check. See [testing](testing.md) for the commands.

## Environment variables

| Variable | Effect |
|---|---|
| `PYSTACHY_LLVM` | Override the LLVM tool directory (Linux 18, macOS 20); standard apt/Homebrew locations are discovered before falling back to `PATH` |
| `PYSTACHY_HOME` | Directory holding the runtime and `lib/`; set by the installed launcher |
| `PYSTACHY_CACHE` | Runtime cache directory; checkout default is `build/`, installed default is `${XDG_CACHE_HOME:-$HOME/.cache}/pystachy` |
| `PYSTACHY_PATH` | Additional import directories, separated by `:` |
| `PYSTACHY_CFLAGS` | Extra clang flags for runtime compilation and AOT linking; part of the cache key |
| `PYSTACHY_IRCHECK=1` | Verify typed IR before lowering and after transforming passes |
| `PYSTACHY_IRFX=1` | Print function effect summaries to stderr |
| `PYSTACHY_OPT` | Disable named optimizations with `-name`, comma-separated, or all with `-all`; see [IR passes](typed-ir.md#optimizations) |
| `PYSTACHY_JIT_INLINE=N` | IR-line threshold for JIT inlining; `0` disables it |
| `PYSTACHY_GC_STRESS=N` | Collect every N allocations |
| `PYSTACHY_GC_STRESS_PROGRAM=N` | Apply the stress interval to the program run by JIT or the test runner, separately from its compiler |
| `PYSTACHY_GC` | `off` disables collection; `stats` prints a summary at exit |
| `PYSTACHY_JOBS` | Parallelism for the test runner and IR tools |

For AddressSanitizer builds, set `ASAN_OPTIONS=detect_stack_use_after_return=0`: its fake stack
is outside the collector's scanned stack. Sanitizer flags instrument the C runtime and final
link; they do not directly instrument the generated code of `runtime.py`.
