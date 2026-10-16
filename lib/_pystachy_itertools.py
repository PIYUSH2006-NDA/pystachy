"""Functional tools for creating and using iterators.

Infinite iterators:
count(start=0, step=1) --> start, start+step, start+2*step, ...
cycle(p) --> p0, p1, ... plast, p0, p1, ...
repeat(elem [,n]) --> elem, elem, elem, ... endlessly or up to n times

Iterators terminating on the shortest input sequence:
accumulate(p[, func]) --> p0, p0+p1, p0+p1+p2
batched(p, n) --> [p0, p1, ..., p_n-1], [p_n, p_n+1, ..., p_2n-1], ...
chain(p, q, ...) --> p0, p1, ... plast, q0, q1, ...
chain.from_iterable([p, q, ...]) --> p0, p1, ... plast, q0, q1, ...
compress(data, selectors) --> (d[0] if s[0]), (d[1] if s[1]), ...
dropwhile(predicate, seq) --> seq[n], seq[n+1], starting when predicate fails
groupby(iterable[, keyfunc]) --> sub-iterators grouped by value of keyfunc(v)
filterfalse(predicate, seq) --> elements of seq where predicate(elem) is False
islice(seq, [start,] stop [, step]) --> elements from
       seq[start:stop:step]
pairwise(s) --> (s[0],s[1]), (s[1],s[2]), (s[2], s[3]), ...
starmap(fun, seq) --> fun(*seq[0]), fun(*seq[1]), ...
tee(it, n=2) --> (it1, it2 , ... itn) splits one iterator into n
takewhile(predicate, seq) --> seq[0], seq[1], until predicate fails
zip_longest(p, q, ...) --> (p[0], q[0]), (p[1], q[1]), ...

Combinatoric generators:
product(p, q, ... [repeat=1]) --> cartesian product
permutations(p[, r])
combinations(p, r)
combinations_with_replacement(p, r)
"""
# itertools for Pystachy: CPython builds itertools into its interpreter (Modules/itertoolsmodule.c),
# so Pystachy loads this module for import itertools (specs.STANDINS). Each function's iteration is
# the pure-Python equivalent that CPython 3.13.16's documentation gives for it
# (Doc/library/itertools.rst, "Roughly equivalent to"), on generators; what the C type's
# constructor does is done when the function is called, as there: it checks the arguments with the
# C module's messages, calls iter() of each iterable (the combinatoric functions read the whole of
# theirs), and returns the generator, which does the rest as it is iterated. chain, groupby's
# groups and tee's iterators keep state that more than one iterator shares, so chain and tee's
# iterators are classes (their names are the C types'), and a group is a generator that reads
# its groupby's state. The functions are templates: each call's argument types make their code,
# and a generator's type is Generator[T] of its items (lib/compatibility.md lists what the types
# allow). The docstrings are the C module's.
from typing import Iterator as _Iterator, Self as _Self


def _empty():
    # a generator that yields nothing (chain() and zip_longest() of no iterables)
    return
    yield None


def _ssize(x) -> int:
    # an argument that the C function reads as a Py_ssize_t (PyNumber_AsSsize_t())
    if isinstance(x, int):
        return int(x)
    elif hasattr(x, "__index__"):
        return x.__index__()
    else:
        raise TypeError(f"'{type(x).__name__}' object cannot be interpreted as an integer")


# --- infinite iterators ---

def count(start=0, step=1):
    """Return a count object whose .__next__() method returns consecutive values.

Equivalent to:
    def count(firstval=0, step=1):
        x = firstval
        while 1:
            yield x
            x += step"""
    if not isinstance(start, (int, float)) or not isinstance(step, (int, float)):
        # PyNumber_Check(): an object with the numeric protocol, which counts by its + (no
        # other type compiles)
        if not (isinstance(start, (int, float)) or hasattr(start, "__index__") or hasattr(start, "__int__") or hasattr(start, "__float__")):
            raise TypeError("a number is required")
        elif not (isinstance(step, (int, float)) or hasattr(step, "__index__") or hasattr(step, "__int__") or hasattr(step, "__float__")):
            raise TypeError("a number is required")
        else:
            return _count(start, step)
    elif isinstance(start, bool) and not isinstance(step, float):
        return _count_bool(start, step)
    elif isinstance(start, bool):
        return _count_bool_float(start, step)
    elif isinstance(start, int) and isinstance(step, float):
        return _count_int_float(start, step)
    else:
        return _count(start, step)


def _count(n, step):
    # count('ABCD') --> 10 11 12 13 14 ...
    while True:
        yield n
        n += step


def _count_bool(start: bool, step) -> _Iterator[bool | int]:
    # a bool start, whose sums are ints: count(True, 2) --> True 3 5 ...; with a step of 1, the
    # C code counts with a C integer from the start: count(True) --> 1 2 3 ...
    n: bool | int = start
    if step == 1:
        n = int(start)
    while True:
        yield n
        n += step


def _count_bool_float(start: bool, step: float) -> _Iterator[bool | float]:
    n: bool | float = start
    while True:
        yield n
        n += step


def _count_int_float(start: int, step: float) -> _Iterator[int | float]:
    # count(1, 0.5) --> 1 1.5 2.0 ...
    n: int | float = start
    while True:
        yield n
        n += step


def cycle(iterable, /):
    """Return elements from the iterable until it is exhausted. Then repeat the sequence indefinitely."""
    return _cycle(iter(iterable))


def _cycle(iterator):
    # cycle('ABCD') --> A B C D A B C D A B C D ...
    saved = []
    for element in iterator:
        yield element
        saved.append(element)
    while saved:
        for element in saved:
            yield element


def repeat(object, *args, **kwargs):
    """repeat(object [,times]) -> create an iterator which returns the object
for the specified number of times.  If not specified, returns the object
endlessly."""
    # repeat(object, times=<unrepresentable>): CPython tells a times argument, whatever its
    # value, apart from its omission, which the lengths of args and kwargs decide at compile time
    if len(args) == 0 and len(kwargs) == 0:
        return _repeat(object)
    else:
        return _repeat_given(object, *args, **kwargs)


def _repeat_given(object, times):
    return _repeat_times(object, _ssize(times))


def _repeat(object):
    while True:
        yield object


def _repeat_times(object, times: int):
    # repeat(10, 3) --> 10 10 10 (a negative number of times is none, as C's)
    for i in range(times):
        yield object


# --- iterators terminating on the shortest input sequence ---

def accumulate(iterable, func=None, *, initial=None):
    """Return series of accumulated sums (or other binary function results)."""
    if initial is None:
        return _accumulate(iter(iterable), func)
    else:
        return _accumulate_initial(iter(iterable), func, initial)


def _accumulate(iterator, func):
    # accumulate([1,2,3,4,5]) --> 1 3 6 10 15
    # accumulate([1,2,3,4,5], operator.mul) --> 1 2 6 24 120
    for item in iterator:
        break
    else:
        return
    first = item  # (a variable the loop does not bind, whose type decides isinstance() at compile time)
    if not isinstance(first, bool):
        total = first
        yield total
        for element in iterator:
            if func is None:
                total = total + element
            else:
                total = func(total, element)
            yield total
    elif func is None:
        yield from _accumulate_bools(first, iterator)
    else:
        ftotal = first
        yield ftotal
        for element in iterator:
            ftotal = func(ftotal, element)
            yield ftotal


def _accumulate_bools(total: bool | int, iterator) -> _Iterator[bool | int]:
    # the sum of bools is an int: accumulate([True, True]) --> True 2
    yield total
    for element in iterator:
        total = total + element
        yield total


def _accumulate_initial(iterator, func, total):
    # accumulate([1,2,3,4,5], initial=100) --> 100 101 103 106 110 115
    yield total
    for element in iterator:
        if func is None:
            total = total + element
        else:
            total = func(total, element)
        yield total


def batched(iterable, n, *, strict=False):
    """Batch data into tuples of length n. The last batch may be shorter than n.

Loops over the input iterable and accumulates data into tuples
up to size n.  The input is consumed lazily, just enough to
fill a batch.  The result is yielded as soon as a batch is full
or when the input iterable is exhausted.

    >>> for batch in batched('ABCDEFG', 3):
    ...     print(batch)
    ...
    ('A', 'B', 'C')
    ('D', 'E', 'F')
    ('G',)

If "strict" is True, raises a ValueError if the final batch is shorter
than n."""
    size = _ssize(n)
    if size < 1:
        raise ValueError("n must be at least one")
    return _batched(iter(iterable), size, bool(strict))


def _batched(iterator, n: int, strict: bool):
    # batched('ABCDEFG', 3) --> ABC DEF G
    while True:
        batch = []
        for item in iterator:
            batch.append(item)
            if len(batch) == n:
                break
        if not batch:
            return
        if strict and len(batch) != n:
            raise ValueError("batched(): incomplete batch")
        yield tuple(batch)


class _chain_type:
    # chain is the one object of this class: calling it makes a generator, as chain(*iterables)
    # makes a chain object in CPython, and its method from_iterable() is the class method of the
    # C type
    def __call__(self, *iterables):
        """Return a chain object whose .__next__() method returns elements from the
first iterable until it is exhausted, then elements from the next
iterable, until all of the iterables are exhausted."""
        if len(iterables) == 0:
            return _empty()
        else:
            return _chain(*iterables)

    def from_iterable(self, iterable, /):
        """Alternative chain() constructor taking a single iterable argument that evaluates lazily."""
        return _from_iterable(iter(iterable))

    def __repr__(self) -> str:
        return "<class 'itertools.chain'>"


chain = _chain_type()


def _chain(*iterables):
    # chain('ABC', 'DEF') --> A B C D E F; each iterable may have a type of its own (a tuple of
    # them is not iterated: one call takes the first and another the rest)
    if len(iterables) == 1:
        yield from iterables[0]
    else:
        yield from iterables[0]
        yield from _chain(*iterables[1:])


def _from_iterable(iterables):
    # chain.from_iterable(['ABC', 'DEF']) --> A B C D E F
    for iterable in iterables:
        yield from iterable


def compress(data, selectors):
    """Return data elements corresponding to true selector elements.

Forms a shorter iterator from selected data elements using the selectors
to choose the data elements."""
    return _compress(iter(data), iter(selectors))


def _compress(data, selectors):
    # compress('ABCDEF', [1,0,1,0,1,1]) --> A C E F
    for datum, selector in zip(data, selectors):
        if selector:
            yield datum


def dropwhile(predicate, iterable, /):
    """Drop items from the iterable while predicate(item) is true.

Afterwards, return every element until the iterable is exhausted."""
    return _dropwhile(predicate, iter(iterable))


def _dropwhile(predicate, iterator):
    # dropwhile(lambda x: x<5, [1,4,6,3,8]) --> 6 3 8
    for x in iterator:
        if not predicate(x):
            yield x
            break
    for x in iterator:
        yield x


def filterfalse(function, iterable, /):
    """Return those items of iterable for which function(item) is false.

If function is None, return the items that are false."""
    return _filterfalse(function, iter(iterable))


def _filterfalse(predicate, iterator):
    # filterfalse(lambda x: x<5, [1,4,6,3,8]) --> 6 8
    for x in iterator:
        if predicate is None:
            if not x:
                yield x
        elif not predicate(x):
            yield x


class _GroupbyState:
    # a groupby's state, which its groups share: Modules/itertoolsmodule.c's groupbyobject (but
    # its keyfunc, which the functions that read the state take), where currkey and currvalue
    # are NULL when has_curr is false, and tgtkey when has_tgt is; grouper counts the groups
    # made, and a group reads only while it is the last one (the C type's currgrouper)
    def __init__(self, it, currkey, currvalue) -> None:
        self.it = it
        self.tgtkey = currkey
        self.currkey = currkey
        self.currvalue = currvalue
        self.has_tgt = False
        self.has_curr = True
        self.grouper = 0


def _groupby_step(st: _GroupbyState, keyfunc) -> bool:
    # the C type's groupby_step(): the next value and its key, False where the iterator has
    # finished
    for newvalue in st.it:
        newkey = keyfunc(newvalue)
        st.currvalue = newvalue
        st.currkey = newkey
        st.has_curr = True
        return True
    return False


def _identity(x):
    # the key of a groupby() without a key function: the item itself
    return x


def _same(a, b) -> bool:
    # PyObject_RichCompareBool(a, b, Py_EQ), which takes an object as equal to itself, as tuple
    # equality does with its items
    return (a,) == (b,)


def groupby(iterable, key=None):
    """make an iterator that returns consecutive keys and groups from the iterable

  iterable
    Elements to divide into groups according to the key function.
  key
    A function for computing the group category for each element.
    If the key function is not specified or is None, the element itself
    is used for grouping."""
    # (key is None decides at compile time but for an object that may be None, such as a
    # callable object in a variable: then its keys must have the items' type)
    if key is None:
        return _groupby(iter(iterable), _identity)
    else:
        return _groupby(iter(iterable), key)


def _groupby(iterator, keyfunc):
    # [k for k, g in groupby('AAAABBBCCDAABBB')] --> A B C D A B
    # [list(g) for k, g in groupby('AAAABBBCCD')] --> AAAA BBB CC D
    # the C type's groupby_next(), whose first step makes the state (its value and key type it)
    for value in iterator:
        break
    else:
        return
    st = _GroupbyState(iterator, keyfunc(value), value)
    while True:
        st.grouper += 1  # (currgrouper = NULL)
        while True:
            if not st.has_curr:
                pass
            elif not st.has_tgt:
                break
            elif not _same(st.tgtkey, st.currkey):
                break
            if not _groupby_step(st, keyfunc):
                return
        st.tgtkey = st.currkey
        st.has_tgt = True
        yield (st.currkey, _grouper(st, keyfunc, st.tgtkey, st.grouper))


def _grouper(st: _GroupbyState, keyfunc, tgtkey, grouper: int):
    # the C type _grouper's _grouper_next()
    while st.grouper == grouper:
        if not st.has_curr:
            if not _groupby_step(st, keyfunc):
                return
        if not _same(tgtkey, st.currkey):
            return
        r = st.currvalue
        st.has_curr = False
        yield r


_STOP = "Stop argument for islice() must be None or an integer: 0 <= x <= sys.maxsize."
_INDICES = "Indices for islice() must be None or an integer: 0 <= x <= sys.maxsize."
_STEP = "Step for islice() must be a positive integer or None."
_MAXSIZE = 9223372036854775807


def _is_none(a) -> bool:
    return a is None


def _islice_index(a) -> int:
    # PyNumber_AsSsize_t() of an argument of islice() that is not None, -1 where it is no
    # integer (the C code clears that TypeError)
    if a is None:
        return -1  # (never: the type of an optional int)
    elif isinstance(a, int):
        return int(a)
    elif hasattr(a, "__index__"):
        return a.__index__()
    else:
        return -1


def islice(iterable, *args):
    """islice(iterable, stop) --> islice object
islice(iterable, start, stop[, step]) --> islice object

Return an iterator whose next() method returns selected values from an
iterable.  If start is specified, will skip all preceding elements;
otherwise, start defaults to zero.  Step defaults to one.  If
specified as another value, step determines how many values are
skipped between successive calls.  Works like a slice() on a list
but returns an iterator."""
    # the C type's islice_new(); stop is -1 for None
    if len(args) == 0 or len(args) > 3:
        raise TypeError(f"islice expected {'at least' if len(args) == 0 else 'at most'} {2 if len(args) == 0 else 4} arguments, got {len(args) + 1}")
    start = 0
    stop = -1
    step = 1
    if len(args) == 1:
        if not _is_none(args[0]):
            stop = _islice_index(args[0])
            if stop == -1:
                raise ValueError(_STOP)
    else:
        if not _is_none(args[0]):
            start = _islice_index(args[0])
        if not _is_none(args[1]):
            stop = _islice_index(args[1])
            if stop == -1:
                raise ValueError(_STOP)
    if start < 0 or stop < -1:
        raise ValueError(_INDICES)
    if len(args) == 3:
        if not _is_none(args[2]):
            step = _islice_index(args[2])
    if step < 1:
        raise ValueError(_STEP)
    return _islice(iter(iterable), start, stop, step)


def _islice(it, nxt: int, stop: int, step: int):
    # islice('ABCDEFG', 2) --> A B
    # islice('ABCDEFG', 2, 4) --> C D
    # islice('ABCDEFG', 2, None) --> C D E F G
    # islice('ABCDEFG', 0, None, 2) --> A C E G
    # the C type's islice_next(): it reads the items before the next one it returns, and none
    # past stop
    cnt = 0
    while True:
        while cnt < nxt:
            for item in it:
                break
            else:
                return
            cnt += 1
        if stop != -1 and cnt >= stop:
            return
        for item in it:
            break
        else:
            return
        cnt += 1
        if nxt > _MAXSIZE - step or (stop != -1 and nxt + step > stop):
            nxt = stop
        else:
            nxt += step
        yield item


def pairwise(iterable, /):
    """Return an iterator of overlapping pairs taken from the input iterator.

    s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    return _pairwise(iter(iterable))


def _pairwise(iterator):
    # pairwise('ABCDEFG') --> AB BC CD DE EF FG
    for a in iterator:
        break
    else:
        return
    for b in iterator:
        yield (a, b)
        a = b


def starmap(function, iterable, /):
    """Return an iterator whose values are returned from the function evaluated with an argument tuple taken from the given sequence."""
    return _starmap(function, iter(iterable))


def _starmap(function, iterator):
    # starmap(pow, [(2,5), (3,2), (10,3)]) --> 32 9 1000
    for args in iterator:
        yield function(*args)


def takewhile(predicate, iterable, /):
    """Return successive entries from an iterable as long as the predicate evaluates to true for each entry."""
    return _takewhile(predicate, iter(iterable))


def _takewhile(predicate, iterator):
    # takewhile(lambda x: x<5, [1,4,6,3,8]) --> 1 4
    for x in iterator:
        if not predicate(x):
            break
        yield x


# tee(): the C module's teedataobject, a link of up to LINKCELLS values read from the iterator,
# which its tee iterators share, each at its own index in its own link; a link that every
# iterator has passed is garbage
_LINKCELLS = 57


class _tee_dataobject:
    def __init__(self, it, values) -> None:
        self.it = it
        self.values = values  # (empty)
        self.running = False
        self.nextlink: "_Self | None" = None

    def jumplink(self) -> "_Self":
        link = self.nextlink
        if link is None:
            link = _tee_dataobject(self.it, self.values[:0])
            self.nextlink = link
        return link

    def getitem(self, i: int):
        if i < len(self.values):
            return self.values[i]
        # this is the lead iterator, so fetch more data
        if self.running:
            raise RuntimeError("cannot re-enter the tee iterator")
        self.running = True
        try:
            value = next(self.it)
        finally:
            self.running = False
        self.values.append(value)
        return value


class _tee:
    """Iterator wrapped to make it copyable."""

    def __init__(self, dataobj, index: int) -> None:
        self.dataobj = dataobj
        self.index = index

    def __iter__(self):
        return self

    def __next__(self):
        if self.index >= _LINKCELLS:
            self.dataobj = self.dataobj.jumplink()
            self.index = 0
        value = self.dataobj.getitem(self.index)
        self.index += 1
        return value

    def __copy__(self) -> "_Self":
        """Returns an independent iterator."""
        return _tee(self.dataobj, self.index)


def _tee_fromiterable(iterable):
    return _tee_from(iter(iterable))


def _tee_from(it):
    # tee_fromiterable(): a copy of a tee iterator, which shares its links, else a tee iterator
    # over the iterator
    if it is None:
        raise TypeError("'NoneType' object is not iterable")  # (never: it tells the compiler that isinstance() decides)
    if isinstance(it, _tee):
        return it.__copy__()
    else:
        return _tee(_tee_dataobject(it, [next(it) for i in range(0)]), 0)  # (an empty list of the items' type)


def tee(iterable, *args):
    """Returns a tuple of n independent iterators."""
    if len(args) > 1:
        raise TypeError(f"tee expected at most 2 arguments, got {len(args) + 1}")
    if len(args) == 0:
        to = _tee_fromiterable(iterable)
        return (to, to.__copy__())
    else:
        # Pystachy: a list of the n iterators, where CPython gives a tuple, as a tuple's length is
        # its type's here (lib/compatibility.md)
        n = _ssize(args[0])
        if n < 0:
            raise ValueError("n must be >= 0")
        result = [_tee_fromiterable(iterable) for i in range(0)]  # (types the list)
        if n == 0:
            return result
        to = _tee_fromiterable(iterable)
        result.append(to)
        for i in range(1, n):
            result.append(to.__copy__())
        return result


def zip_longest(*iterables, fillvalue=None):
    """Return a zip_longest object whose .__next__() method returns a tuple where
the i-th element comes from the i-th iterable argument.  The .__next__()
method continues until the longest iterable in the argument sequence
is exhausted and then it raises StopIteration.  When the shorter iterables
are exhausted, the fillvalue is substituted in their place.  The fillvalue
defaults to None or can be specified by a keyword argument.
"""
    if len(iterables) == 0:
        return _empty()
    else:
        return _zip_longest(_ZipState(len(iterables)), fillvalue, *_iters(*iterables))


def _iters(*iterables):
    # a tuple of the iterators of iterables, made in order
    if len(iterables) == 1:
        return (iter(iterables[0]),)
    else:
        first = iter(iterables[0])
        return (first,) + _iters(*iterables[1:])


class _ZipState:
    # which iterators of a zip_longest() have finished (NULL in the C type's ittuple)
    def __init__(self, n: int) -> None:
        self.active = [True] * n
        self.numactive = n


def _zip_get(st: _ZipState, i: int, it, fillvalue):
    # the i-th item of a row: the next item of the i-th iterator, or the fill value once it has
    # finished
    if st.active[i]:
        for item in it:
            return item
        st.active[i] = False
        st.numactive -= 1
    return fillvalue


def _zip_row(st: _ZipState, fillvalue, i: int, *its):
    if len(its) == 1:
        return (_zip_get(st, i, its[0], fillvalue),)
    else:
        first = _zip_get(st, i, its[0], fillvalue)
        return (first,) + _zip_row(st, fillvalue, i + 1, *its[1:])


def _zip_longest(st: _ZipState, fillvalue, *its):
    # zip_longest('ABCD', 'xy', fillvalue='-') --> Ax By C- D-
    while True:
        row = _zip_row(st, fillvalue, 0, *its)
        if st.numactive == 0:
            return
        yield row


# --- combinatoric iterators ---

def product(*iterables, **kwargs):
    """Cartesian product of input iterables.  Equivalent to nested for-loops.

For example, product(A, B) returns the same as:  ((x,y) for x in A for y in B).
The leftmost iterators are in the outermost for-loop, so the output tuples
cycle in a manner similar to an odometer (with the rightmost element changing
on every iteration).

To compute the product of an iterable with itself, specify the number
of repetitions with the optional repeat keyword argument. For example,
product(A, repeat=4) means the same as product(A, A, A, A).

product('ab', range(3)) --> ('a',0) ('a',1) ('a',2) ('b',0) ('b',1) ('b',2)
product((0,1), (0,1), (0,1)) --> (0,0,0) (0,0,1) (0,1,0) (0,1,1) (1,0,0) ..."""
    # product(*iterables, repeat=1): without repeat (which the length of kwargs decides at compile
    # time), each tuple has an item of each iterable, of its type; with it, the tuples' length is
    # known as the program runs, so their items have one type
    if len(kwargs) == 0:
        if len(iterables) == 0:
            return _product0()
        else:
            return _product(*_pools_fixed(*iterables))
    else:
        return _product_repeat(*iterables, **kwargs)


def _product_repeat(*iterables, repeat):
    n = _ssize(repeat)
    if n < 0:
        raise ValueError("repeat argument cannot be negative")
    if len(iterables) == 0:
        return _product0()
    if n == 0:
        # the C code reads none of the iterables
        return _product_pools([list(iterables[0]) for i in range(0)], 0)
    if len(iterables) > _MAXSIZE // 8 // n:
        raise OverflowError("repeat argument too large")
    return _product_pools(_pools(*iterables), n)


def _pools(*iterables):
    # a list of the iterables' items, each read into a list, in order
    if len(iterables) == 1:
        return [list(iterables[0])]
    else:
        first = list(iterables[0])
        return [first] + _pools(*iterables[1:])


def _pools_fixed(*iterables):
    # a tuple of the iterables' items, each read into a list, in order
    if len(iterables) == 1:
        return (list(iterables[0]),)
    else:
        first = list(iterables[0])
        return (first,) + _pools_fixed(*iterables[1:])


def _product0():
    yield ()


def _product(*pools):
    # product('ABCD', 'xy') --> Ax Ay Bx By Cx Cy Dx Dy
    if len(pools) == 1:
        for x in pools[0]:
            yield (x,)
    elif len(pools) == 2:
        for x in pools[0]:
            for y in pools[1]:
                yield (x, y)
    elif len(pools) == 3:
        for x in pools[0]:
            for y in pools[1]:
                for z in pools[2]:
                    yield (x, y, z)
    else:
        for x in pools[0]:
            for rest in _product(*pools[1:]):
                yield (x,) + rest


def _product_pools(pools, repeat: int):
    # product(range(2), repeat=3) --> 000 001 010 011 100 101 110 111: the C type's
    # product_next(), an odometer over repeat copies of the pools
    pools = pools * repeat
    npools = len(pools)
    for pool in pools:
        if len(pool) == 0:
            return
    indices = [0] * npools
    result = [pool[0] for pool in pools]
    yield tuple(result)
    while True:
        i = npools - 1
        while i >= 0:
            pool = pools[i]
            indices[i] += 1
            if indices[i] == len(pool):
                indices[i] = 0
                result[i] = pool[0]
                i -= 1
            else:
                result[i] = pool[indices[i]]
                break
        if i < 0:
            return
        yield tuple(result)


def permutations(iterable, r=None):
    """Return successive r-length permutations of elements in the iterable.

permutations(range(3), 2) --> (0,1), (0,2), (1,0), (1,2), (2,0), (2,1)"""
    pool = list(iterable)
    if r is None:
        return _permutations(pool, len(pool))
    elif not isinstance(r, int):
        raise TypeError("Expected int as r")
    else:
        if r < 0:
            raise ValueError("r must be non-negative")
        return _permutations(pool, int(r))


def _permutations(pool, r: int):
    # permutations('ABCD', 2) --> AB AC AD BA BC BD CA CB CD DA DB DC
    # permutations(range(3)) --> 012 021 102 120 201 210
    # the documentation's equivalent, with the C type's permutations_next() in place: a
    # rotation moves the indices one by one, and the result changes from the leftmost index
    # that changed
    n = len(pool)
    if r > n:
        return
    indices = list(range(n))
    cycles = list(range(n, n - r, -1))
    result = pool[:r]
    yield tuple(result)
    if n == 0:
        return
    while True:
        i = r - 1
        while i >= 0:
            cycles[i] -= 1
            if cycles[i] == 0:
                # indices[i:] = indices[i+1:] + indices[i:i+1]
                index = indices[i]
                for j in range(i, n - 1):
                    indices[j] = indices[j + 1]
                indices[n - 1] = index
                cycles[i] = n - i
            else:
                j = cycles[i]
                index = indices[i]
                indices[i] = indices[n - j]
                indices[n - j] = index
                for k in range(i, r):
                    result[k] = pool[indices[k]]
                break
            i -= 1
        if i < 0:
            return
        yield tuple(result)


def combinations(iterable, r):
    """Return successive r-length combinations of elements in the iterable.

combinations(range(4), 3) --> (0,1,2), (0,1,3), (0,2,3), (1,2,3)"""
    size = _ssize(r)
    pool = list(iterable)
    if size < 0:
        raise ValueError("r must be non-negative")
    return _combinations(pool, size)


def _combinations(pool, r: int):
    # combinations('ABCD', 2) --> AB AC AD BC BD CD
    # combinations(range(4), 3) --> 012 013 023 123
    # the documentation's equivalent, with the C type's combinations_next() in place
    n = len(pool)
    if r > n:
        return
    indices = list(range(r))
    result = pool[:r]
    yield tuple(result)
    while True:
        # the rightmost index that is not at its maximum (i + n - r)
        i = r - 1
        while i >= 0 and indices[i] == i + n - r:
            i -= 1
        if i < 0:
            return
        indices[i] += 1
        for j in range(i + 1, r):
            indices[j] = indices[j - 1] + 1
        for j in range(i, r):
            result[j] = pool[indices[j]]
        yield tuple(result)


def combinations_with_replacement(iterable, r):
    """Return successive r-length combinations of elements in the iterable allowing individual elements to have successive repeats.

combinations_with_replacement('ABC', 2) --> ('A','A'), ('A','B'), ('A','C'), ('B','B'), ('B','C'), ('C','C')"""
    size = _ssize(r)
    pool = list(iterable)
    if size < 0:
        raise ValueError("r must be non-negative")
    return _combinations_with_replacement(pool, size)


def _combinations_with_replacement(pool, r: int):
    # combinations_with_replacement('ABC', 2) --> AA AB AC BB BC CC
    # the documentation's equivalent, with the C type's cwr_next() in place
    n = len(pool)
    if not n and r:
        return
    indices = [0] * r
    result = [pool[0] for i in range(r)]
    yield tuple(result)
    while True:
        # the rightmost index that is not at its maximum (n - 1)
        i = r - 1
        while i >= 0 and indices[i] == n - 1:
            i -= 1
        if i < 0:
            return
        index = indices[i] + 1
        elem = pool[index]
        for j in range(i, r):
            indices[j] = index
            result[j] = elem
        yield tuple(result)
