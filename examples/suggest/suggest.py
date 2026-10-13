"""suggest: corrections for the unknown words of a text, from a vocabulary, as a spelling checker
offers them, with difflib's get_close_matches().

usage: python3 suggest.py [-n N] [-c CUTOFF] VOCABULARY [TEXT...]
       pystachy build suggest.py -o suggest && ./suggest words.txt essay.txt

VOCABULARY holds one word per line. Each word of the TEXT files (standard input without one) is
lowercased and stripped of the punctuation around it; for each one that is not in the vocabulary
it prints its line and column, the word, and up to N (3) words of the vocabulary whose similarity
ratio with it is at least CUTOFF (0.75), best first, which get_close_matches() finds with a
SequenceMatcher: a cheap upper bound of the ratio first, then the ratio itself.
"""
import sys
from difflib import get_close_matches

PUNCTUATION = ".,;:!?\"'()[]{}-"


def words(line: str) -> list[tuple[int, str]]:
    """The words of a line, lowercased and stripped of punctuation, with their columns (from 1)."""
    out: list[tuple[int, str]] = []
    col = 0
    for part in line.split(" "):
        word = part.strip(PUNCTUATION).lower()
        if word:
            out.append((col + 1 + part.lower().find(word), word))
        col += len(part) + 1
    return out


def check(lines: list[str], vocabulary: list[str], n: int, cutoff: float) -> list[str]:
    """A report line for each unknown word of the lines."""
    known = set(vocabulary)
    report: list[str] = []
    for lineno, line in enumerate(lines, 1):
        for col, word in words(line):
            if word not in known and not word.isdigit():
                matches = get_close_matches(word, vocabulary, n, cutoff)
                report.append(f"{lineno}:{col}: {word}: {', '.join(matches) if matches else '(no suggestion)'}")
    return report


def main(argv: list[str]) -> int:
    n = 3
    cutoff = 0.75
    args: list[str] = []
    i = 0
    while i < len(argv):
        if argv[i] in ("-n", "-c") and i + 1 < len(argv):
            try:
                if argv[i] == "-n":
                    n = int(argv[i + 1])
                else:
                    cutoff = float(argv[i + 1])
            except ValueError as e:
                print(f"suggest: {argv[i]}: {e}", file=sys.stderr)
                return 2
            i += 2
            continue
        args.append(argv[i])
        i += 1
    if not args:
        print("usage: suggest.py [-n N] [-c CUTOFF] VOCABULARY [TEXT...]", file=sys.stderr)
        return 2
    with open(args[0]) as f:
        vocabulary = [w.strip().lower() for w in f if w.strip()]
    lines: list[str] = []
    for name in args[1:] or ["-"]:
        if name == "-":
            lines.extend([line.rstrip("\n") for line in sys.stdin])
        else:
            with open(name) as f:
                lines.extend([line.rstrip("\n") for line in f])
    try:
        report = check(lines, vocabulary, n, cutoff)
    except ValueError as e:
        print(f"suggest: {e}", file=sys.stderr)
        return 2
    for line in report:
        print(line)
    print(f"{len(report)} unknown words in {len(lines)} lines, {len(vocabulary)} words in the vocabulary")
    return 1 if report else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
