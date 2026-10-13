"""cut: print the selected fields or characters of each line, as POSIX cut does (a subset).

usage: python3 cut.py -f LIST [-d DELIM] [-s] [--complement] [--output-delimiter STR] [FILE...]
       python3 cut.py -c LIST [--complement] [FILE...]
       pystachy build cut.py -o cut && ./cut -f 2,5- table.tsv

LIST is one or more ranges separated by commas: N, N-M, N- (to the end) or -M (from the first);
fields and characters are numbered from 1, and a field or character is printed once, in input
order, however many ranges select it. Fields are separated by DELIM (a tab by default), and a
line without DELIM is printed as it is, unless -s. With no FILE, or for a FILE that is -, it reads
standard input. Options may follow the files, as GNU's do: getopt.gnu_getopt() parses them.
"""
import getopt
import sys

USAGE = """usage: cut.py -f LIST [-d DELIM] [-s] [--complement] [--output-delimiter STR] [FILE...]
       cut.py -c LIST [--complement] [FILE...]"""

END = 1 << 40  # the end of an open range (N-)


def parse_list(text: str) -> list[tuple[int, int]]:
    """The ranges of LIST, sorted, with those that overlap or touch merged."""
    ranges: list[tuple[int, int]] = []
    for part in text.split(","):
        lo_text, dash, hi_text = part.partition("-")
        if part == "" or part == "-" or not (lo_text.isdigit() or lo_text == "") or not (hi_text.isdigit() or hi_text == ""):
            raise ValueError(f"invalid field or character list: {text!r}")
        lo = int(lo_text) if lo_text else 1
        hi = (int(hi_text) if hi_text else END) if dash else lo
        if lo == 0 or hi == 0:
            raise ValueError("fields and characters are numbered from 1")
        if hi < lo:
            raise ValueError(f"invalid decreasing range: {part}")
        ranges.append((lo, hi))
    ranges.sort()
    merged: list[tuple[int, int]] = []
    for lo, hi in ranges:
        if merged and lo <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], hi))
        else:
            merged.append((lo, hi))
    return merged


def select(items: list[str], ranges: list[tuple[int, int]], complement: bool) -> list[str]:
    """The items that the ranges select (or, with complement, those they do not), in order."""
    out: list[str] = []
    n = len(items)
    if not complement:
        for lo, hi in ranges:
            if lo > n:
                break
            out.extend(items[lo - 1:min(hi, n)])
        return out
    pos = 1
    for lo, hi in ranges:
        if lo > n:
            break
        if lo > pos:
            out.extend(items[pos - 1:lo - 1])
        pos = max(pos, hi + 1)
    if pos <= n:
        out.extend(items[pos - 1:])
    return out


def cut_line(line: str, ranges: list[tuple[int, int]], fields: bool, delim: str, outdelim: str,
             only_delimited: bool, complement: bool) -> str | None:
    """What cut prints for one line (without its newline), or None for a line -s drops."""
    if not fields:
        return "".join(select(list(line), ranges, complement))
    if delim not in line:
        return None if only_delimited else line
    return outdelim.join(select(line.split(delim), ranges, complement))


def fail(message: str) -> int:
    print(f"cut: {message}", file=sys.stderr)
    print(USAGE, file=sys.stderr)
    return 2


def main(argv: list[str]) -> int:
    try:
        opts, files = getopt.gnu_getopt(argv, "f:c:d:s", ["fields=", "characters=", "delimiter=", "only-delimited",
                                                          "complement", "output-delimiter=", "help"])
    except getopt.GetoptError as e:
        return fail(str(e))
    field_list = ""
    char_list = ""
    delim = "\t"
    outdelim: str | None = None
    only_delimited = False
    complement = False
    for opt, value in opts:
        if opt in ("-f", "--fields"):
            field_list = value
        elif opt in ("-c", "--characters"):
            char_list = value
        elif opt in ("-d", "--delimiter"):
            if len(value) != 1:
                return fail("the delimiter must be a single character")
            delim = value
        elif opt in ("-s", "--only-delimited"):
            only_delimited = True
        elif opt == "--complement":
            complement = True
        elif opt == "--output-delimiter":
            outdelim = value
        elif opt == "--help":
            print(USAGE)
            return 0
    if (field_list == "") == (char_list == ""):
        return fail("give one list, of fields (-f) or of characters (-c)")
    fields = field_list != ""
    if not fields and (only_delimited or outdelim is not None or delim != "\t"):
        return fail("-d, -s and --output-delimiter only make sense with fields (-f)")
    try:
        ranges = parse_list(field_list if fields else char_list)
    except ValueError as e:
        return fail(str(e))
    sep = delim if outdelim is None else outdelim
    out = sys.stdout
    for name in files or ["-"]:
        f = sys.stdin if name == "-" else open(name)
        for line in f:
            text = cut_line(line[:-1] if line.endswith("\n") else line, ranges, fields, delim, sep,
                            only_delimited, complement)
            if text is not None:
                out.write(text + "\n")
        if name != "-":
            f.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
