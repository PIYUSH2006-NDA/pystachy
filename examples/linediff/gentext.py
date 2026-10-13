"""gentext: two versions of a synthetic text for linediff.py, the same on every run.

usage: python3 gentext.py N old > OLD
       python3 gentext.py N new > NEW
OLD has N lines of 4 to 12 words. NEW is OLD edited about once every 40 lines: a line deleted, a
new line inserted, a word of a line replaced or a line split in two, and one block of 20 lines
moved towards the end, as a revision of a document would be.
"""
import sys

WORDS = ["the", "of", "and", "to", "in", "is", "that", "for", "it", "as", "was", "with", "be", "by",
         "on", "not", "this", "are", "at", "from", "his", "an", "which", "or", "data", "model", "value",
         "result", "table", "error", "system", "first", "second", "time", "number", "file", "change",
         "line", "set", "case", "point", "order", "state", "test", "output", "input", "cache", "rule"]

seed = 20261013


def rand(n: int) -> int:
    # an int in [0, n): a 31-bit linear congruential generator (glibc's constants), whose products
    # stay in 64 bits, as Pystachy's ints do
    global seed
    seed = (seed * 1103515245 + 12345) % 2147483648
    return (seed >> 8) % n


def sentence() -> str:
    return " ".join([WORDS[rand(len(WORDS))] for _ in range(4 + rand(9))])


def versions(n: int) -> tuple[list[str], list[str]]:
    old = [f"{i + 1}. {sentence()}" for i in range(n)]
    new: list[str] = []
    for line in old:
        r = rand(160)
        if r == 0:
            continue  # deleted
        if r == 1:
            new.append(sentence())  # inserted before
        if r == 2:
            words = line.split()
            words[rand(len(words))] = "CHANGED"
            new.append(" ".join(words))
        elif r == 3:
            words = line.split()
            k = 1 + rand(len(words) - 1)
            new.append(" ".join(words[:k]))
            new.append(" ".join(words[k:]))
        else:
            new.append(line)
    if len(new) > 100:
        start = len(new) // 3
        block = new[start:start + 20]
        new = new[:start] + new[start + 20:]
        at = len(new) * 3 // 4
        new = new[:at] + block + new[at:]
    return old, new


def main() -> None:
    old, new = versions(int(sys.argv[1]))
    for line in (old if sys.argv[2] == "old" else new):
        print(line)


if __name__ == "__main__":
    main()
