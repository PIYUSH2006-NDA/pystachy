"""linediff: the differences between two text files, from difflib's SequenceMatcher.

usage: python3 linediff.py [-U N] [--words] [-q] OLD NEW
       pystachy build linediff.py -o linediff && ./linediff OLD NEW

By default it prints the files' differences as a unified diff (as diff -u and difflib's
unified_diff() do) with N lines of context (3 by default), from the opcodes SequenceMatcher finds
between the two lists of lines. --words prints the new text with each change marked word by word,
as wdiff and git diff --word-diff do: [-removed-] and {+added+}. It compares the lines first, then
the words of each group of lines that one replaces, so that common words, which SequenceMatcher's
autojunk heuristic ignores in a long sequence, still match within a line. -q prints only the
similarity ratio of the lines and how many lines (and, with --words, words) changed. The exit
status is 0 if the files are the same, 1 if they differ and 2 on an error.
"""
import sys
from difflib import SequenceMatcher


def groups(codes: list[tuple[str, int, int, int, int]], n: int) -> list[list[tuple[str, int, int, int, int]]]:
    """The opcodes in hunks, with up to n equal lines of context around each change."""
    if not codes:
        return []
    codes = list(codes)
    tag, i1, i2, j1, j2 = codes[0]
    if tag == "equal":  # only the last n lines of a leading run of equal lines
        codes[0] = (tag, max(i1, i2 - n), i2, max(j1, j2 - n), j2)
    tag, i1, i2, j1, j2 = codes[-1]
    if tag == "equal":  # and the first n of a trailing one
        codes[-1] = (tag, i1, min(i2, i1 + n), j1, min(j2, j1 + n))
    out: list[list[tuple[str, int, int, int, int]]] = []
    group: list[tuple[str, int, int, int, int]] = []
    for tag, i1, i2, j1, j2 in codes:
        if tag == "equal" and i2 - i1 > 2 * n:
            # a long run of equal lines ends this hunk and starts the next
            group.append((tag, i1, i1 + n, j1, j1 + n))
            out.append(group)
            group = []
            i1, j1 = i2 - n, j2 - n
        group.append((tag, i1, i2, j1, j2))
    if group and not (len(group) == 1 and group[0][0] == "equal"):
        out.append(group)
    return out


def span(start: int, stop: int) -> str:
    # a hunk header's range, as unified_diff() writes it: the first line (from 1) and the length
    length = stop - start
    if length == 1:
        return str(start + 1)
    return f"{start if length == 0 else start + 1},{length}"


def unified(old: list[str], new: list[str], n: int, old_name: str, new_name: str) -> list[str]:
    """The unified diff of two lists of lines (without their newlines)."""
    out: list[str] = []
    for group in groups(SequenceMatcher(None, old, new).get_opcodes(), n):
        if not out:
            out.append(f"--- {old_name}")
            out.append(f"+++ {new_name}")
        out.append(f"@@ -{span(group[0][1], group[-1][2])} +{span(group[0][3], group[-1][4])} @@")
        for tag, i1, i2, j1, j2 in group:
            if tag == "equal":
                out.extend([" " + line for line in old[i1:i2]])
                continue
            out.extend(["-" + line for line in old[i1:i2]])
            out.extend(["+" + line for line in new[j1:j2]])
    return out


def marked(old: list[str], new: list[str]) -> tuple[str, int, int]:
    """The new words with each change marked [-removed-] and {+added+}, and the counts of words
    removed and added."""
    out: list[str] = []
    removed = 0
    added = 0
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, old, new).get_opcodes():
        if tag == "equal":
            out.extend(new[j1:j2])
            continue
        if i1 < i2:
            out.append("[-" + " ".join(old[i1:i2]) + "-]")
            removed += i2 - i1
        if j1 < j2:
            out.append("{+" + " ".join(new[j1:j2]) + "+}")
            added += j2 - j1
    return " ".join(out), removed, added


def worddiff(old: list[str], new: list[str]) -> tuple[list[str], int, int]:
    """The new lines, each change marked word by word, and the counts of words removed and added."""
    out: list[str] = []
    removed = 0
    added = 0
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, old, new).get_opcodes():
        if tag == "equal":
            out.extend(new[j1:j2])
            continue
        text, r, a = marked(" ".join(old[i1:i2]).split(), " ".join(new[j1:j2]).split())
        out.append(text)
        removed += r
        added += a
    return out, removed, added


def summary(old: list[str], new: list[str], words: bool) -> str:
    s = SequenceMatcher(None, old, new)
    removed = 0
    added = 0
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag != "equal":
            removed += i2 - i1
            added += j2 - j1
    text = f"{len(old)} and {len(new)} lines, ratio {s.ratio():.4f}: {removed} removed, {added} added"
    if words:
        _, removed_words, added_words = worddiff(old, new)
        text += f"; words: {removed_words} removed, {added_words} added"
    return text


def read(path: str) -> str:
    with open(path) as f:
        return f.read()


def main(argv: list[str]) -> int:
    context = 3
    words = False
    quiet = False
    files: list[str] = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "-U" and i + 1 < len(argv) and argv[i + 1].isdigit():
            context = int(argv[i + 1])
            i += 1
        elif arg == "--words":
            words = True
        elif arg == "-q":
            quiet = True
        elif arg.startswith("-") and arg != "-":
            print(f"linediff: unknown option {arg}", file=sys.stderr)
            return 2
        else:
            files.append(arg)
        i += 1
    if len(files) != 2:
        print("usage: linediff.py [-U N] [--words] [-q] OLD NEW", file=sys.stderr)
        return 2
    a = read(files[0])
    b = read(files[1])
    old = a.splitlines()
    new = b.splitlines()
    if quiet:
        print(summary(old, new, words))
    elif words:
        for line in worddiff(old, new)[0]:
            print(line)
    else:
        for line in unified(old, new, context, files[0], files[1]):
            print(line)
    return 0 if old == new else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
