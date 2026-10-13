"""genvocab: a synthetic vocabulary, and a text with misspellings of its words, for suggest.py; the
same on every run.

usage: python3 genvocab.py vocab N > VOCABULARY
       python3 genvocab.py text N M > TEXT
The vocabulary holds N distinct words made of syllables. The text has M lines of 6 to 14 of those
words, capitalized at the start of a sentence and with punctuation, about one word in 12
misspelled: a letter replaced, dropped, doubled or swapped with the next one.
"""
import sys

SYLLABLES = ["ka", "to", "ri", "men", "sa", "lo", "ve", "nu", "dar", "pe", "chi", "on", "ba", "tel",
             "mi", "gu", "res", "fa", "zo", "lin", "qua", "be", "do", "ster", "ya", "ex", "pli", "cor"]
LETTERS = "abcdefghijklmnopqrstuvwxyz"

seed = 20261013


def rand(n: int) -> int:
    # an int in [0, n): a 31-bit linear congruential generator (glibc's constants), whose products
    # stay in 64 bits, as Pystachy's ints do
    global seed
    seed = (seed * 1103515245 + 12345) % 2147483648
    return (seed >> 8) % n


def vocabulary(n: int) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    while len(out) < n:
        word = "".join([SYLLABLES[rand(len(SYLLABLES))] for _ in range(1 + rand(4))])
        if word not in seen:
            seen.add(word)
            out.append(word)
    return out


def misspell(word: str) -> str:
    k = rand(len(word))
    kind = rand(4)
    if kind == 0:
        return word[:k] + LETTERS[rand(26)] + word[k + 1:]
    if kind == 1 and len(word) > 3:
        return word[:k] + word[k + 1:]
    if kind == 2:
        return word[:k] + word[k] + word[k:]
    if k + 1 < len(word):
        return word[:k] + word[k + 1] + word[k] + word[k + 2:]
    return word + LETTERS[rand(26)]


def text(vocab: list[str], m: int) -> list[str]:
    lines: list[str] = []
    for _ in range(m):
        words: list[str] = []
        start = True
        for _ in range(6 + rand(9)):
            word = vocab[min(rand(len(vocab)), rand(len(vocab)))]
            if rand(12) == 0:
                word = misspell(word)
            if start:
                word = word[0].upper() + word[1:]
            start = rand(8) == 0
            words.append(word + "." if start else word + "," if rand(10) == 0 else word)
        lines.append(" ".join(words))
    return lines


def main() -> None:
    vocab = vocabulary(int(sys.argv[2]))
    if sys.argv[1] == "vocab":
        for w in vocab:
            print(w)
    else:
        for line in text(vocab, int(sys.argv[3])):
            print(line)


if __name__ == "__main__":
    main()
