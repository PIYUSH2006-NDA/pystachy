# linediff: unified and word diffs from difflib's SequenceMatcher

`linediff.py` prints the differences between two text files: a unified diff, as `diff -u` and
difflib's `unified_diff()` print it, or the new text with each change marked word by word, as
`wdiff` and `git diff --word-diff` do. It is ordinary Python, which CPython runs as it is and
Pystachy compiles as it is, and both come from the opcodes of the standard library's
`difflib.SequenceMatcher` ([`lib/difflib`](../../lib/README.md#difflib-a-port-of-cpythons)):

```
$ python3 gentext.py 50000 old > old.txt    # a text, and a revision of it: lines deleted,
$ python3 gentext.py 50000 new > new.txt    # inserted, edited, split, and a block moved
$ python3 linediff.py old.txt new.txt       # CPython
$ pystachy build linediff.py -o linediff && ./linediff -U 1 old.txt new.txt
--- old.txt
+++ new.txt
@@ -128,2 +128,3 @@
 128. or order state the test test was in
+result system be it state line set for not rule output
 129. the point this from and
@@ -154,3 +155,3 @@
 154. time output and set second to be line an
-155. at is test is the of the data at
+155. at is test is CHANGED of the data at
...
$ ./linediff --words old.txt new.txt
...
{+result system be it state line set for not rule output+}
...
155. at is test is [-the-] {+CHANGED+} of the data at
...
[-299. be which his file it with or line by-]
...
$ ./linediff -q --words old.txt new.txt
50000 and 50270 lines, ratio 0.9782: 958 removed, 1228 added; words: 3397 removed, 2997 added
```

- The unified diff is grouped into hunks with `-U N` lines of context (3 by default), with
  `unified_diff()`'s headers and ranges: under CPython, `linediff.unified()` returns what
  `unified_diff(..., lineterm="")` yields, line for line, each line without its line break.
  `unified_diff()` itself is a generator, which Pystachy does not compile yet, so `linediff` groups
  the opcodes itself.
- Lines are compared with their line breaks, which `linediff` reads as they are
  (`open(path, newline="")`), as `diff` compares them: a file whose last line has no newline, or
  whose lines end in `\r\n`, differs from one whose lines end in `\n`, and the unified diff marks a
  last line without a newline with `\ No newline at end of file`, as `diff -u` does.
- `--words` compares the lines first, then the words of each group of lines that one replaces:
  over a whole text, the autojunk heuristic of a `SequenceMatcher` would ignore the common words,
  which appear in more than 1% of a long sequence, and nothing would line up. It prints the new
  text's lines, each change marked on its line.
- `-q` prints the similarity ratio of the two lists of lines, and the counts of lines (and, with
  `--words`, words) removed and added. The exit status is 0 if the files are the same, 1 if they
  differ and 2 on an error, as `diff`'s.

CPython and the executable print the same diffs.

## Speed

`bench.py`, on a 4-core x86-64 VM: median wall time of 5 runs with process start-up, peak RSS of
one, two texts of 50,000 lines (2.3 MB each). The executable is Pystachy's AOT build of
`linediff.py`.

| mode | CPython 3.13.16 | Pystachy AOT | speedup | CPython RSS | AOT RSS |
|---|---:|---:|---:|---:|---:|
| unified | 0.167 s | 0.079 s | 2.1x | 35.0 MB | 51.4 MB |
| `--words` | 0.190 s | 0.086 s | 2.2x | 35.0 MB | 54.9 MB |
| `-q` | 0.161 s | 0.076 s | 2.1x | 35.2 MB | 51.3 MB |

- **Compiled, a diff takes half CPython's time.** Timed alone (best of 5), the `SequenceMatcher`
  of the two lists of 50,000 lines takes 124 ms under CPython and 39 ms compiled: its work is
  `find_longest_match()`'s loops over dicts keyed by the lines (`b2j`, and a new `j2len` dict for
  each line of the old text), whose dicts CPython runs in C, and whose loops the executable
  compiles. The rest of a run is start-up and reading the files.
- **Small matchers gain more:** the word diffs of the 1,217 groups of changed lines take 11.6 ms
  under CPython and 1.8 ms compiled, where each `SequenceMatcher` is made, filled and walked on a
  few words.
  [`examples/suggest`](../suggest/README.md), which matches one word against a vocabulary at a
  time, is 4 to 5 times as fast as CPython.
- **Memory stays bounded**, at about 1.5 times CPython's peak: both hold the two texts and the
  matcher's tables.
- Building the executable takes about 3 s.

## Tests

`tests/example_linediff.py` runs `span()`, `groups()`, `marked()`, `unified()` and `worddiff()` on
their edge cases (line breaks, lines split and reflowed), then the unified diffs (with 3, 1 and 0
lines of context), the word diff and the summary of two generated versions of a 400-line text, and
`main()` with each mode, on files that differ in their line breaks, and with its errors, and
compares what it prints with CPython's (`tests/example_linediff.path` puts this directory on the module path).
`bench.py` runs the table above: `python3 -I bench.py ../../pystachy 5`, from anywhere; it writes
its texts and executable to `build/linediff/`.
