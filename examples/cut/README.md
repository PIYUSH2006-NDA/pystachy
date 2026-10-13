# cut: fields and characters of each line, with getopt's option parsing

`cut.py` prints the selected fields or characters of each line of its input, as POSIX `cut`
does: a subset of GNU's, with its long options. It is ordinary Python, which CPython runs as it
is and Pystachy compiles as it is, and its command line is parsed by the standard library's
`getopt.gnu_getopt()` ([`lib/getopt`](../../lib/README.md#getopt-a-port-of-cpythons)), so
options may come after the files, as GNU's may:

```
$ python3 gentable.py 500000 > table.tsv      # id, time, user, service, op, status, ms, message
$ python3 cut.py -f 2,5-7 table.tsv           # CPython
$ pystachy build cut.py -o cut && ./cut table.tsv -f 3 --complement
0	1760000000	queue	put	301	3837	slow read miss
1	1760000003	gateway	get	200	4837	miss partial ok slow
...
$ ./cut -f 8,1 -s --output-delimiter=' | ' table.tsv
$ ./cut -c 1-20 table.tsv
$ ./cut -x table.tsv
cut: option -x not recognized
usage: cut.py -f LIST [-d DELIM] [-s] [--complement] [--output-delimiter STR] [FILE...]
       cut.py -c LIST [--complement] [FILE...]
```

- `-f LIST` (`--fields`) selects fields, separated by `-d DELIM` (`--delimiter`, a tab by default),
  and `-c LIST` (`--characters`) characters. LIST is ranges separated by commas: `N`, `N-M`, `N-`
  or `-M`, numbered from 1; each field or character is printed once, in input order.
- `-s` (`--only-delimited`) drops the lines without a delimiter, which are otherwise printed as they
  are; `--complement` prints what the list does not select; `--output-delimiter STR` joins the
  fields it prints.
- `getopt.gnu_getopt()` takes the short options `f:c:d:s` and the long ones, accepts any unique
  prefix of a long option (`--compl`), and raises `GetoptError` with CPython's message for an
  unknown option or a missing argument, which `cut.py` prints with its usage (exit status 2).

CPython and the executable print the same lines, and the same errors. Past ASCII, `-c` counts a
line's bytes under Pystachy, whose strings are UTF-8, and its characters under CPython: GNU's `-c`
counts bytes too.

## Speed

`bench.py`, on a 4-core x86-64 VM: median wall time of 5 runs with process start-up, peak RSS of
one, a table of 500,000 lines (31 MB). The executable is Pystachy's AOT build of `cut.py`. The
machine ran other jobs at the time: a second run moved cells by up to 0.1 s, and its speedups also
stayed between 1.4x and 1.7x.

| selection | CPython 3.13.16 | Pystachy AOT | speedup | CPython RSS | AOT RSS |
|---|---:|---:|---:|---:|---:|
| `-f 2,5-7` | 0.480 s | 0.376 s | 1.3x | 10.9 MB | 35.4 MB |
| `-f 3 --complement` | 0.545 s | 0.335 s | 1.6x | 10.9 MB | 35.4 MB |
| `-c 1-20` | 0.415 s | 0.270 s | 1.5x | 10.9 MB | 35.9 MB |
| `-s -f 8,1` | 0.393 s | 0.238 s | 1.7x | 11.0 MB | 35.0 MB |

- **Compiled, `cut` is 1.3 to 1.7 times as fast as CPython.** What it does per line is a line
  read, a `split()` and a `join()`, which CPython does in C too; the selection between them, a
  few slices and comparisons, is where the compiled code gains.
- **Option parsing is not where the time goes**: `getopt` runs once, on a handful of arguments.
  What it adds is CPython's behaviour for the command line, prefixes and errors included.
- **Memory stays bounded**, at about 3 times CPython's peak: Pystachy's collector runs when its
  heap has grown, where CPython frees each line as its last reference goes.
- Building the executable takes about 1 s.

## Tests

`tests/example_cut.py` runs `parse_list()` and `select()` on their edge cases, and `main()` on a
generated table with each option, then with each error, and compares what it prints with CPython's
(`tests/example_cut.path` puts this directory on the module path). `bench.py` runs the table above:
`python3 -I bench.py ../../pystachy 5`, from anywhere; it writes its table and executable to
`build/cut/`.
