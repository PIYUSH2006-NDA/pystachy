# Execution and expressions

This reference expands the [language guide](../language.md). Types, function specialization,
closures and class fields are described in [typing](typing.md); imports and builtin APIs are in
[modules](modules.md).

## Statements

| Category | Supported statements |
|---|---|
| Assignment | Simple, chained, annotated and augmented assignment; tuple/list unpacking, with one starred target or none, and swaps |
| Control flow | `if` / `elif` / `else`, `while`, `for`, loop `else`, `break`, `continue`, `return` |
| Scope and definitions | `global`, `nonlocal`, `def`, nested function definitions, lambdas, supported class definitions |
| Runtime checks | `assert`, `raise`, `try` / `except` / `else` / `finally` |
| Resources | `with open(...) as f:`, including several file contexts, with or without parentheses |
| Deletion | `del` of a local, list item, dict key or supported object's item |
| Other | Imports, docstrings, `pass` and `...` |

`+=` on a list extends it in place. Object in-place operators use `__iadd__` and the
corresponding methods when supported. Deleting a variable makes later reads raise
`NameError` or `UnboundLocalError`; deleting a global from a function is unsupported.

A starred target, as in `head, *body, tail = xs`, gets a new list of the items the other targets
leave. It takes what a `for` loop iterates, and `range()`, `enumerate()`, `zip()`, `map()`,
`filter()` and generator expressions; every item is taken before the first target is assigned.
Too few items raise CPython's `ValueError`. Of a tuple, the starred list holds its items'
common type; items of types no one type holds need an annotation (`body: list[int | str]`).

Loops can consume ranges, lists, strings, dictionaries, sets, files, homogeneous tuples and
NamedTuples, supported objects, and dictionary `items()`, `keys()` and `values()`.
`enumerate(..., start=...)`, `zip()` and `reversed()` work in supported contexts.
A dictionary or set whose size changes while its iterator is active raises `RuntimeError`.
`zip()` creates its operands' iterators in order, before iteration starts.

Restrictions on nested iterator-like expressions, snapshots and mutation are listed in
[compatibility](compatibility.md).

## Literals and formatting

Numeric literals support decimal, hexadecimal, octal, binary and underscore separators.
Strings support raw and triple-quoted literals, implicit concatenation and escapes other
than `\N{...}`.

F-strings support `!r`, `!s`, `!a`, debug `=`, nested format specifications and the
format-spec mini-language. Replacement fields follow Python 3.12's grammar (PEP 701): they may
reuse the f-string's quote, nest f-strings, and hold backslashes, newlines and comments.

`%` formatting requires a literal format string, or a module global that one module-level
assignment binds to one (`FMT = "%8.3f"`, also `Final`) where nothing else in the program, not
even a function's local, binds its name. It supports `s r a d i u x X o e E f F g G c`, flags,
widths and precisions, but not named substitutions, `*` widths or precisions, or integer
precisions. A variable format string such as `fmt % value` is rejected.

`str.format()` and `str.format_map()` (also `str.format(FMT, ...)`) also require a literal format
string or such a module global, compiled like an f-string: automatic and manual numbering, keyword
fields, `.attr` and `[key]` lookups, `!r`, `!s`, `!a` and nested fields in a spec. The arguments
are evaluated first, then the fields are formatted left to right; a malformed format, mixed
numbering, a missing argument or an unknown conversion raises CPython's error when that field is
reached. `*` unpacks a tuple, or a list after the other positional arguments; `**` unpacks a
function's `**kwargs`, a dict display with string keys or one `dict[str, T]`. `"...".format` can
be `map()`'s function, but neither method is otherwise a value, and `fmt.format(value)` of another
variable format string is rejected.

## Operators and containers

Supported operations include arithmetic, bitwise operations, chained comparisons,
`in` / `not in`, boolean operations returning operands, conditional expressions, negative
indices, string, list and tuple slices with optional steps, and assignment to and deletion
of list slices. Integer `//` and `%` floor as in Python;
true division is correctly rounded, and int/float comparisons are exact within the
supported types.

Container expressions include list, dict, set and tuple displays; list, set and dict
comprehensions; and tuple concatenation or repetition by a constant. Set and frozenset
operations support union, intersection, difference, symmetric difference, subset ordering
and in-place forms.

A comprehension or generator expression may have several `for` and `if` clauses. As in
CPython, its first iterable is evaluated once in the enclosing scope; each later iterable and
condition is evaluated for every item of the clauses before it, and the clauses' variables
belong to the comprehension: a later `for` clause that binds an earlier clause's variable
binds the same variable. A dict comprehension evaluates each key before its value; a repeated
key keeps its first position and takes the last value. A clause or `for` target that reads a
variable which only its own or a later `for` clause binds is rejected (CPython raises
`UnboundLocalError`), as is a rebinding to another type that a clause between the two can read.
A starred item in a list or tuple display, `[a, *xs, *range(n)]`, takes the iterable's items
where it stands. A tuple display whose starred items are tuples is a tuple of their items;
with another iterable, it is a runtime-length tuple.

An assignment expression, `x := v`, assigns `v` to `x` as `x = v` would, in the function or
module code around it, also from a comprehension or generator expression (PEP 572); its value is
`v`. Tests such as `if (m := pattern.match(s)) is not None:` narrow `x` as a test of the name
does. Where the expression may not have run (after `and` or `or`, in one arm of a conditional
expression, in a comprehension over nothing), a later read of `x` raises `UnboundLocalError` or
`NameError`. This also covers assignment expressions in lambda defaults: the defaults run
when the lambda is created. A comprehension's filters run before its element. An unannotated
template parameter specialized to `None` cannot be rebound by a conditional assignment
expression; annotate that parameter as `T | None` to allow both values.

`is` and `is not` are supported for identity-bearing values, not numbers.
Booleans use their two fixed values, so `flag is True` behaves as equality.
Comparisons with `None` are supported where the static types permit them.

## Iterator-like expressions

Generator expressions, `range()`, `reversed()`, `enumerate()`, `zip()`, `map()` and
`filter()` can be direct arguments of `list`, `sorted`, `sum`, `min`, `max`, `any`,
`all`, `math.fsum`, `math.prod`, `str.join` and `list.extend`, those that give key/value pairs
of `dict`, the value assigned to a list slice or to a starred target, or a `*` item of a list
or tuple display, subject to each consumer's item types. `tuple()` also accepts generator
expressions and `range`/`map`/`filter`/`reversed` calls producing supported scalar or optional
scalar items. Direct `enumerate`/`zip` items are tuples; project a scalar in a generator
expression first ([runtime-length tuples](typing.md)).

These expressions are compiled for their consumer rather than creating a general generator.
`map()` and `filter()` evaluate their function before iteration.
`any()` and `all()` stop at the deciding item, including over files.
`list.extend()` appends each generated item as it is produced; a slice assignment takes the
items once the list and the slice's bounds are evaluated.
`x in range(...)` is also supported.

Some consumers materialize input before processing it; see the
[evaluation-order differences](compatibility.md#containers-and-evaluation-order).

## Iterators

`iter(x)` returns an iterator object that shares its position with every use, as CPython's:

```python
it = iter(lines)
header = next(it)
for line in it:  # the lines after the header
    print(line)
```

`iter()` accepts lists, strings, homogeneous tuples, dictionaries and their `keys()`,
`values()` and `items()`, sets, `range(...)`, files and objects with `__iter__`. A file is its
own iterator. A builtin container's iterator is an object of a class in
[`lib/_pystachy_iterators.py`](../../lib/_pystachy_iterators.py): it reads a list's current
length at each step, fails if a dictionary or set changes size, and stays exhausted once
`StopIteration` is raised. `next(it)` calls `it.__next__()` (a file's next line);
`next(it, default)` returns the default instead of raising `StopIteration`, and has the type
of both, such as `T | None` for a `None` default. `iter(callable, sentinel)` and `iter()` of
`enumerate()`, `zip()`, `map()`, `filter()`, `reversed()` or a generator expression are
unsupported.

An iterator's type is its class. `Iterator[T]` and `Iterable[T]` annotations (`typing`'s or
`collections.abc`'s) therefore type nothing, as a class template's name does: a function with
such a parameter or return is compiled for each call's argument types, a class whose
`__init__` takes one or calls `iter()` is a class template, and an annotated variable or field
has its value's type. A `Generic[T]` class's `Iterable[T]` parameter binds `T` to the items.

## Generators

A function or method whose body contains `yield` or `yield from` is a generator function.
Calling one runs none of its body: it makes a generator object, which runs to its next `yield`
each time a consumer asks for an item. Generator functions that yield one type share one static
type (`Generator[T]` in messages). A generator function's return annotation is `Iterator[T]`,
`Iterable[T]` or `Generator[Y, None, R]`, from `typing` or `collections.abc`; elsewhere
`Iterator[T]` and `Iterable[T]` type nothing (see [iterators](#iterators)), so a parameter
annotated so takes generators as well as iterator objects, and `Generator[T, None, None]` names
a generator's type (`holder: list[Generator[int, None, None]] = []`). An unannotated generator
function is a template: its first `yield` gives the type for each call's argument types. An
`__iter__` or `__reversed__` that yields makes the generator that iterates its object.

| Use | Behavior |
|---|---|
| `for` loops, `enumerate()`, `zip()`, comprehensions | Each item as the generator yields it; a finished generator yields nothing |
| `next(g)`, `next(g, default)`, `g.__next__()` | The next item; `StopIteration` (or the default) once it has finished |
| `iter(g)`, `g.__iter__()`, `iter(o)` | `g` itself; the generator `o.__iter__()` makes |
| `sum`, `min`, `max`, `any`, `all`, `math.fsum`, `math.prod` | The items as they come; `any()` and `all()` stop at the deciding item |
| `list`, `tuple`, `sorted`, `set`, `frozenset`, `str.join`, `list.extend` | All the items |
| `x in g` | Iterates until an item equals `x` |
| `a, b = g`, `a, *rest = g` | One item for each target, then one more step that must find `g` finished; with a starred target, all the items |
| `yield from x` | Each item of `x`; for a generator, delegation, and `r = yield from g()` is `g`'s return value |

A generator expression that no consumer takes directly, such as one stored in a variable or
returned, is an anonymous generator: its first iterable is evaluated where it is written and
the rest as it runs. Globals are read when it runs. Variables of the enclosing function that it
reads must not be bound again (and must be assigned) where it is written: it reads their values
then.

A `for` loop over a generator that its iterable expression has just made (a call of a generator
function, or of an `__iter__` or `__reversed__` that yields, also inside `enumerate()`, `zip()`
or `reversed()`) closes the generator when the loop is left by its
end, `break`, `return` or an exception, before the code after the loop runs. Closing raises
`GeneratorExit` at the suspended `yield`, so `finally` blocks, `with` blocks and
`except GeneratorExit` run, as in CPython. What the close raises, and a `yield` after
`GeneratorExit`, are reported on stderr as CPython reports exceptions it ignores, and the loop's
exit goes on. Exceptions raised in a loop's body never enter the generator. An exception that
leaves a generator's body finishes the generator; a `StopIteration` becomes
`RuntimeError: generator raised StopIteration` (PEP 479). A generator that resumes itself raises
`ValueError: generator already executing`.

`send()`, `throw()`, `close()`, the value of a `yield` expression, `async` generators and frame
introspection are not supported. A generator the program drops while it is suspended is not
closed (see [deviations](compatibility.md#memory-and-resource-lifetime)).

## Object protocols

Object operations use the following methods. In supported ordinary hierarchies, instance-method
overrides dispatch on the concrete receiver; the static type still controls which operations
and fields are available. See [single inheritance](typing.md#single-inheritance).

| Operation | Methods |
|---|---|
| Binary operators `+ - * / // % @ & \| ^ << >>` | `__add__` and the corresponding methods |
| In-place operators | `__iadd__` and counterparts, otherwise the binary method |
| Unary `-`, `+`, `~` | `__neg__`, `__pos__`, `__invert__` |
| `abs(o)`, `divmod(o, x)` | `__abs__`, `__divmod__` |
| Equality and ordering | `__eq__`, `__ne__` and rich comparisons |
| Truth and length | `__bool__`, `__len__` |
| Representation | `__str__`, `__repr__`, `__format__` |
| Call, indexing, assignment, deletion | `__call__`, `__getitem__`, `__setitem__`, `__delitem__` |
| Membership and iteration | `__contains__`, or supported `__iter__` |
| `reversed()` | Supported `__reversed__` |

Rich comparisons use reflection, such as trying `b.__gt__(a)` for `a < b`.
Reflected arithmetic methods such as `__radd__` and `__rdivmod__`, and object `__pow__`, are
unsupported.
Objects in containers compare, sort and print through their methods.
Lists and tuples test items with equality before ordering them, then compare length if all
common items are equal. Sorting and `min()` use `<`; `max()` uses `>`.

Object calls accept the keyword and default arguments of `__call__`.
For `o[k] += value`, both indexing and assignment methods are used.
Membership uses `__contains__`, taking its result's truth; without it, membership searches
the supported iterator.

An `__iter__` returns an iterator object: its own object or another class's object with a
`__next__` method, whose return type gives the items. Its return annotation may be omitted
(the returns decide it), name the class (`-> "C"`, `-> Self`) or be `Iterator[T]`. Loops,
comprehensions, unpacking, `x in o`, `math.dist()` and the consumers above call `__next__`
until it raises `StopIteration` or a subclass, also from a nested `next()`; any other
exception propagates.
`__iter__` runs once before the loop, and `__next__` once per item. A comprehension also calls
the iterator's own `__iter__`, as CPython 3.13 does. `any()`, `all()`, `sum()`, `min()`,
`max()` and `in` take items as they come; `list()`, `tuple()`, `sorted()`, `str.join()` and
`set()` take them all first. `list()`, `tuple()`, `sorted()` and `list.extend()` call the
iterable's `__len__`, if present, as a length hint; a slice assignment does not, as in CPython.

An `__iter__` annotated `-> Iterator[T]` or `-> Iterable[T]` whose returns are all `iter(xs)`
of a list, tuple, string or object with such an `__iter__` keeps a faster form: a loop
steps through that list directly. A supported `__reversed__` has that form, or returns
`reversed(xs)`, whose items it copies when it returns; every consumer of `reversed(o)` steps
through the iterator it returns. Calling `o.__iter__()` is unsupported. Generator
implementations are unsupported.

A missing protocol method produces a compilation error using CPython's message.
An object that is `None` when the operation executes raises the corresponding runtime error.

## Exceptions

### Builtin exceptions

`try` supports `except`, `else` and `finally` in CPython's combinations, except
`except*`. Handlers can name a builtin or user exception class, a tuple of classes, or use
a bare `except:`, with or without `as name`.

Handlers follow CPython 3.13's hierarchy: `LookupError` catches `KeyError`, whereas
`Exception` does not catch `SystemExit`. `IOError` is an alias for `OSError`.
Handlers catch runtime failures, explicitly raised exceptions, failures from another
function or module, and failures in callbacks such as a sort comparison.

An exception class is looked up when the handler is reached or before the exception is
constructed. If its class statement has not executed, lookup raises `NameError`.
The `as` binding is cleared on every exit from its handler and can have another type before
or after that handler.

Calling a builtin exception class produces an exception value. Values can be stored,
printed, converted to `str` / `repr`, formatted, raised, compared by identity, and tested
with `isinstance()` or `type(e).__name__`. An annotation such as `Exception` names the
builtin exception value type; it does not accept arbitrary user exception objects.

`OSError(errno, strerror[, filename])` selects the subclass associated with the errno.
`UnicodeDecodeError(encoding, object, start, end, reason)` (of a bytes object) and
`UnicodeEncodeError(...)` (of a str, whose characters `start` and `end` count) take CPython's
five arguments and give its message, which names the byte or character at `start` or the range
to `end`. `ImportError`, `AttributeError` and `NameError` accept their supported keyword
arguments. Exception attributes such as `args` are unsupported.

### Control flow

`finally` runs on normal completion, exceptions, `return`, `break` and `continue`.
A return value is computed before `finally`; a return, break or continue in `finally`
discards the exception in flight.

Bare `raise` re-raises the currently handled exception, with the prior handler restored
when an inner handler exits. `raise ... from ...` evaluates and validates its cause, but
the abbreviated error output does not show exception chaining. A cause that is not an
exception raises `TypeError`.

An exception leaving a file context closes the file. If closing fails, its `OSError`
replaces the exception being handled. A failed Python-module import leaves its imported
names unbound and is retried on a later import; see [module initialization](modules.md).

Actual memory exhaustion, native stack exhaustion and Ctrl-C bypass ordinary handlers and
cleanup. Uncaught exceptions have abbreviated output. These are documented in
[errors and control flow](compatibility.md#errors-and-control-flow).

### User exception classes

A user exception class has one base: a supported builtin exception class or another
exception class in the program. It supports fields, constructors, class-body defaults,
methods, docstrings and custom `__str__` / `__repr__`.

A subclass inherits fields and methods and can override `__init__`, `__str__` and
`__repr__`. String conversion and uncaught error output use the object's actual class.
`super().__init__`, `super().__str__`, `super().__repr__`, explicit base calls and
`super(E, self)` are supported within the documented restrictions.

Positional constructor arguments are retained for default string and repr output.
`super().__init__(...)` resets them. Without a constructor in the user class or a user
base, positional arguments are forwarded to the builtin base. An `OSError` or `SystemExit`
subclass with its own constructor keeps no builtin args (and `SystemExit` code is `None`)
until `super().__init__` is called.

An `except E as e` binding uses the nearest common user exception base of the handler's
classes, otherwise the builtin exception type. An uncaught user exception prints
`module.E: message` (`E` in the main program) and exits with status 1; a `SystemExit`
subclass exits using its code. Exception values keep identity when raised.

Additional inheritance, constructor and attribute restrictions are in
[exception restrictions](compatibility.md#exceptions-and-exception-classes).

## Syntax errors

Source checks apply to the whole file, including unused templates, imported definitions and
branches dropped at compile time. Pystachy checks tokenization, grammar, name binding and
statement placement, aiming to match CPython's error location and message.

Checks include bracket and indentation limits, unterminated literals, invalid targets,
argument-list errors, invalid `global` / `nonlocal`, misplaced control-flow statements,
late future imports and excessive statically nested blocks. Error selection follows the
parser, tokenizer where reached, symbol table, then compiler checks.

Some messages fall back to `invalid syntax` where CPython is more specific.
Patterns inside `match` statements are not checked, and the supported source syntax has
[additional restrictions](compatibility.md#source-text).
`tools/syntax_sweep.py` compares `pystachy check` with CPython's `compile()`;
`pystachy check` checks parsing and syntax, not whether a program can compile.

