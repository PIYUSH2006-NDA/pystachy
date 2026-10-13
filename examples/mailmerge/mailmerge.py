"""mailmerge: a message for each record of a data file, rendered from a string.Template.

usage: python3 mailmerge.py TEMPLATE DATA [--safe | --split] > MBOX
       pystachy build mailmerge.py -o mailmerge && ./mailmerge TEMPLATE DATA > MBOX

TEMPLATE is a message, its headers and its body, with $name or ${name} where a field of a record
goes and $$ for a dollar sign. DATA holds a header line that names the fields, then a record per
line, its fields separated by tabs, which mailmerge reads one at a time. Besides a record's fields,
$seq is the record's number and $count the number of records (a first pass counts them): keyword
arguments of substitute(), which come before the record's fields. The messages go to stdout as a
mailbox (mbox), each after a "From " line (a line of a message that starts with "From " gets a
">"), and their number to stderr.

Before it renders a message, mailmerge checks the template: is_valid(), else the first invalid
placeholder ($ followed by no name, no $ and no braced name), with its line and column as
substitute() reports them; and get_identifiers(), each of which must be a field of the header,
unless --safe, which renders with safe_substitute(): a placeholder without a field stays as it
is. --split renders without Template: the template is split once at its placeholders, and each
message joins the pieces with the fields, the way a program that knows its template is fixed
would render it.
"""
import sys
from string import Template

FROM_LINE = "From billing@example.com Tue Oct 13 00:00:00 2026"
EXTRA = ["seq", "count"]


def parse(names: list[str], line: str, n: int) -> dict[str, str]:
    # the record of line n of DATA, a dict of its fields by the header's names
    fields = line.rstrip("\n").split("\t")
    if len(fields) != len(names):
        raise ValueError(f"line {n}: {len(fields)} fields, where the header names {len(names)}")
    record: dict[str, str] = {}
    for i in range(len(names)):
        record[names[i]] = fields[i]
    return record


def check(t: Template, names: list[str], safe: bool) -> str:
    # what keeps the template from rendering the records ("" if nothing does)
    if not t.is_valid():
        blank: dict[str, str] = {}
        for name in t.get_identifiers():
            blank[name] = ""
        try:
            t.substitute(blank)
        except ValueError as e:
            return str(e)
    missing = [name for name in t.get_identifiers() if name not in names and name not in EXTRA]
    if missing and not safe:
        return "no field " + ", ".join(missing) + " in the data"
    return ""


def render(t: Template, record: dict[str, str], seq: int, count: int, safe: bool) -> str:
    if safe:
        return t.safe_substitute(record, seq=str(seq), count=str(count))
    return t.substitute(record, seq=str(seq), count=str(count))


def split(t: Template) -> tuple[list[str], list[str]]:
    # the text of a valid template between its placeholders, and their names: a message is
    # texts[0], the field of names[0], texts[1], ... texts[-1]
    texts: list[str] = []
    names: list[str] = []
    text = ""
    pos = 0
    for mo in t.pattern.finditer(t.template):
        text += t.template[pos:mo.start()]
        pos = mo.end()
        name = mo.group("named") or mo.group("braced")
        if name is None:
            text += t.delimiter  # ($$)
        else:
            texts.append(text)
            names.append(name)
            text = ""
    texts.append(text + t.template[pos:])
    return texts, names


def render_split(texts: list[str], names: list[str], record: dict[str, str], seq: int, count: int) -> str:
    extra = {"seq": str(seq), "count": str(count)}
    parts = [texts[0]]
    for i in range(len(names)):
        parts.append(extra[names[i]] if names[i] in extra else record[names[i]])
        parts.append(texts[i + 1])
    return "".join(parts)


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        print("usage: mailmerge.py TEMPLATE DATA [--safe | --split] > MBOX", file=sys.stderr)
        sys.exit(2)
    mode = sys.argv[3] if len(sys.argv) > 3 else ""
    with open(args[0]) as f:
        t = Template(f.read())
    with open(args[1]) as f:
        count = sum(1 for _ in f) - 1  # (the header line)
    with open(args[1]) as f:
        names = f.readline().rstrip("\n").split("\t")
        problem = check(t, names, mode == "--safe")
        if problem:
            print(f"mailmerge: {args[0]}: {problem}", file=sys.stderr)
            sys.exit(1)
        texts, fields = split(t) if mode == "--split" else ([], [])
        seq = 0
        for line in f:
            seq += 1
            record = parse(names, line, seq + 1)
            if mode == "--split":
                msg = render_split(texts, fields, record, seq, count)
            else:
                msg = render(t, record, seq, count, mode == "--safe")
            print(FROM_LINE)
            print(msg.replace("\nFrom ", "\n>From "))
    print(f"mailmerge: {seq} messages", file=sys.stderr)


if __name__ == "__main__":
    main()
