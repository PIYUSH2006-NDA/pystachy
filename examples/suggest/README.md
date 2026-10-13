# suggest: spelling corrections from a vocabulary, with difflib's get_close_matches()

`suggest.py` checks a text against a vocabulary, as a spelling checker does: for each word of the
text that the vocabulary lacks, it prints where it is and the closest words of the vocabulary,
which the standard library's `difflib.get_close_matches()` finds
([`lib/difflib`](../../lib/README.md#difflib-a-port-of-cpythons)). It is ordinary Python, which
CPython runs as it is and Pystachy compiles as it is:

```
$ python3 genvocab.py vocab 20000 > vocab.txt          # 20,000 words made of syllables
$ python3 genvocab.py text 20000 25 > text.txt         # 25 lines of them, 1 word in 12 misspelled
$ head -2 text.txt
Beriito fareslinmen gucorbee pliberes lomidaron quabaquasa bestergu
Vebemifa. Menzonuya menexpli tocorlinto mizoster beexsa
$ python3 suggest.py vocab.txt text.txt                # CPython
$ pystachy build suggest.py -o suggest && ./suggest vocab.txt text.txt
1:1: beriito: berito, miberito, exberito
1:21: gucorbee: gucorbepe, guzocorbe, begucorbe
4:81: ridzo: ridozo, rizo, rido
5:31: resbnau: resbanu, resbagu, resnu
...
17 unknown words in 25 lines, 20000 words in the vocabulary
```

- A word is lowercased and stripped of the punctuation around it; numbers are not checked.
- `get_close_matches(word, vocabulary, n, cutoff)` keeps the `n` (`-n`, 3) words whose similarity
  ratio with the word is at least `cutoff` (`-c`, 0.75), best first. For each word of the
  vocabulary it sets one `SequenceMatcher`'s first sequence and tries two cheap upper bounds of the
  ratio (`real_quick_ratio()`, from the lengths, and `quick_ratio()`, from the letters as a
  multiset) before computing the ratio itself from the matching blocks.
- The exit status is 1 if the text has unknown words, 0 if not, and 2 on an error: an `-n` or `-c`
  that is not a number, or a `cutoff` outside [0, 1] (get_close_matches()'s `ValueError`).

CPython and the executable print the same report.

## Speed

`bench.py`, on a 4-core x86-64 VM: median wall time of 5 runs with process start-up, peak RSS of
one, a vocabulary of 20,000 words and texts of 25 and 100 lines. The executable is Pystachy's AOT
build of `suggest.py`.

| text | unknown words | CPython 3.13.16 | Pystachy AOT | speedup | CPython RSS | AOT RSS |
|---|---:|---:|---:|---:|---:|---:|
| 25 lines | 17 | 0.425 s | 0.119 s | 3.6x | 13.7 MB | 40.2 MB |
| 100 lines | 72 | 1.686 s | 0.331 s | 5.1x | 13.7 MB | 41.1 MB |

- **Compiled, a lookup is about 6 times as fast as CPython's**: from the two rows, each unknown
  word costs CPython about 23 ms and the executable about 3.9 ms, the 20,000 bounds and ratios of
  `get_close_matches()`, whose `SequenceMatcher` is pure Python in CPython too. The rest, which
  reads the vocabulary and makes its set, takes about 0.035 s under CPython and 0.054 s compiled.
- **Memory stays bounded**, at about 3 times CPython's peak: Pystachy's collector runs when its
  heap has grown.
- Building the executable takes about 3 s.

## Tests

`tests/example_suggest.py` runs `words()` on punctuation and spacing, `check()` on a generated
text of 30 lines against a generated vocabulary of 3,000 words and on small cases, and `main()`
with its options and errors, and compares what it prints with CPython's
(`tests/example_suggest.path` puts this directory on the module path). `bench.py` runs the table
above: `python3 -I bench.py ../../pystachy 5`, from anywhere; it writes its files and executable
to `build/suggest/`.
