"""topk: the most frequent words of a text and its most frequent pairs of words, picked with
heapq.nlargest(); and its longest and its rarest words.

usage: python3 topk.py TEXT [N] [--sort] [--time]
       pystachy build topk.py -o topk && ./topk TEXT [N] [--sort] [--time]

A word is what str.split() separates, lowercased, without the punctuation around it; a pair is two
words that follow each other in a line. topk counts both in dicts, then picks the N (default 10)
largest counts with heapq.nlargest(n, counts.items(), key=count_of), which keeps a heap of the N
best items so far and compares every other item once with the least of them. Ties keep the order
of the dict, the order in which the text first used the words. --sort picks the same items by
sorting all of them, sorted(..., reverse=True)[:n], as heapq's documentation says nlargest() is
equivalent to, and --time writes how long the counting and the picking took to stderr.
"""
import sys
import time
from heapq import nlargest, nsmallest

PUNCTUATION = ".,;:!?\"'()[]-"


def count(lines, words: dict[str, int], pairs: dict[tuple[str, str], int]) -> int:
    # counts the words and pairs of the lines (a file, or a list of str) into words and pairs, and
    # returns how many words there were
    n = 0
    for line in lines:
        prev = ""
        for w in line.split():
            w = w.strip(PUNCTUATION).lower()
            if w:
                n += 1
                words[w] = words.get(w, 0) + 1
                if prev:
                    pairs[prev, w] = pairs.get((prev, w), 0) + 1
                prev = w
    return n


def count_of(item):
    # the count of a (word, count) or ((word, word), count) item of a dict
    return item[1]


def pick(n, words, pairs, by_sort):
    # the n most frequent words and pairs, the n longest words and the n rarest
    if by_sort:
        return (sorted(words.items(), key=count_of, reverse=True)[:n],
                sorted(pairs.items(), key=count_of, reverse=True)[:n],
                sorted(words, key=len, reverse=True)[:n],
                sorted(words.items(), key=count_of)[:n])
    return (nlargest(n, words.items(), key=count_of),
            nlargest(n, pairs.items(), key=count_of),
            nlargest(n, words, key=len),
            nsmallest(n, words.items(), key=count_of))


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 1:
        print("usage: topk.py TEXT [N] [--sort] [--time]", file=sys.stderr)
        sys.exit(2)
    n = int(args[1]) if len(args) > 1 else 10
    t0 = time.perf_counter()
    words: dict[str, int] = {}
    pairs: dict[tuple[str, str], int] = {}
    with open(args[0]) as f:
        total = count(f, words, pairs)
    t1 = time.perf_counter()
    top_words, top_pairs, longest, rarest = pick(n, words, pairs, "--sort" in sys.argv)
    t2 = time.perf_counter()
    print(f"{total} words, {len(words)} distinct; {len(pairs)} distinct pairs")
    print("most frequent words:")
    for w, c in top_words:
        print(f"{c:9} {w}")
    print("most frequent pairs:")
    for p, c in top_pairs:
        print(f"{c:9} {p[0]} {p[1]}")
    print("longest words:", ", ".join(longest))
    print("rarest words:", ", ".join(f"{w} ({c})" for w, c in rarest))
    if "--time" in sys.argv:
        print(f"count {t1 - t0:.3f} s, pick {t2 - t1:.3f} s", file=sys.stderr)


if __name__ == "__main__":
    main()
