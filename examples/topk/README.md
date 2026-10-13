# topk: the most frequent words of a text, picked with heapq

`topk.py` counts the words of a text and its pairs of adjacent words, then prints the most frequent
of each, picked with `heapq.nlargest(n, counts.items(), key=count_of)`, the longest words
(`nlargest(n, words, key=len)`) and the rarest (`nsmallest()`): the last step of a word-frequency
report, a log summary or any count of many keys, where a few of hundreds of thousands are wanted.
It is ordinary Python, which CPython runs as it is and Pystachy compiles as it is, with
[`lib/heapq`](../../lib/README.md#heapq-with-nlargest-and-nsmallest-ported)'s `nlargest()` and
`nsmallest()`: CPython's, edited where the subset has no iterators.

```
$ python3 gentext.py 1000000 > text.txt     # Rukavofe of the vonequzo the lozokami nerunelo, ...
$ python3 topk.py text.txt                   # CPython
$ pystachy build topk.py -o topk && ./topk text.txt
1000002 words, 98644 distinct; 675477 distinct pairs
most frequent words:
    58500 the
    29605 and
    29285 of
    ...
most frequent pairs:
     3101 the the
     1616 the and
     ...
longest words: qulorudaka, xivozozoka, damisaneka, xifefemika, jijimisaka, peguloneka, ...
rarest words: vonequzo (1), rupequru (1), xivozozoka (1), xifefemika (1), davodape (1), ...
```

CPython and the executable print the same report. `nlargest()` keeps a heap of the n best items so
far and compares each other item with the least of them: few beat it, and only those go into the
heap. Ties keep the dict's order, the order in which the text first used the words. `--sort` picks the same items by
sorting all of them, `sorted(..., reverse=True)[:n]`, which heapq's documentation gives as
`nlargest()`'s equivalent, and `--time` writes how long the counting and the picking took to
stderr.

`gentext.py` writes a text whose words follow Zipf's law, as a language's do: the word of rank r
comes up about 1/(r + 1) times as often as the commonest, from a linear congruential generator, so
that the text is the same on every run. The 48 commonest words are English's; the others are made
of syllables. Its words are drawn independently, so the commonest pair is the commonest word twice.

## What the heap buys

`bench.py`, on a 4-core x86-64 VM shared with other jobs: median wall time of 7 runs with process
start-up, the median of the picking times the runs report (`--time`), and the peak RSS of one run,
on a text of 1,000,000 words (6.4 MB; 98,644 distinct words, 675,477 distinct pairs) and one of
4,000,000 (26 MB; 2,353,431 distinct pairs):

| text | picking | CPython 3.13.16 | Pystachy AOT | picking, CPython | picking, AOT | CPython RSS | AOT RSS |
|---|---|---:|---:|---:|---:|---:|---:|
| 1M words | `nlargest()` | 0.769 s | 0.520 s | 0.062 s | 0.013 s | 120.6 MB | 115.3 MB |
| 1M words | `--sort` | 0.988 s | 0.564 s | 0.218 s | 0.088 s | 172.2 MB | 146.1 MB |
| 4M words | `nlargest()` | 3.446 s | 2.493 s | 0.156 s | 0.038 s | 399.9 MB | 402.1 MB |
| 4M words | `--sort` | 3.934 s | 2.641 s | 0.640 s | 0.342 s | 579.8 MB | 483.8 MB |

- **The heap is the speedup of the picking, compiled or not**: it picks in a quarter of the time of
  sorting in CPython, and in a seventh to a ninth compiled, where the comparison of a count with the
  heap's least is an int comparison in the loop's code.
- **Compiled, the picking is 4 to 5 times as fast as CPython's**: 13 ms against 62 ms for the four
  picks of the 1M-word text. `nlargest()` of the 675,477 pairs itself takes about 2 ms of them;
  most of the rest is making `words.items()` and `pairs.items()`, which are lists in Pystachy, of a
  new tuple for each item, where CPython's are views.
- **The program as a whole is 1.4 to 1.8 times as fast**, as reading, splitting and counting the
  words take most of its time (0.4 s of the executable's 0.52 s for 1M words): `str.split()`,
  `strip()`, `lower()` and dict updates, which CPython does in C too.
- Memory is about the same with the heap; sorting the 2.35M pairs takes CPython more than it takes
  the executable. Building the executable takes about 1.3 s.

## Tests

`tests/example_topk.py` counts a generated text of 300 sentences in-process, picks with `nlargest()`
and `nsmallest()` and by sorting, for n from 0 to more than the distinct words, and compares the
counts and the picks with CPython's (`tests/example_topk.path` puts this directory on the module
path). `bench.py` runs the table above: `python3 -I bench.py ../../pystachy 7`, from anywhere; it
writes its texts and executable to `build/topk/`.
