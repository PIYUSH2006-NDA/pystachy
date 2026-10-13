# s.split(...)[0] of a str makes its first part alone (Gen.index, runtime.py's pys_str_split_first):
# no list, no other part. split_first.calls pins that these functions call pys_str_split_first and
# no pys_str_split, but where another item, or another class's split, is indexed.
class Record:
    def __init__(self, text: str) -> None:
        self.text = text

    def key(self) -> str:
        return self.text.split("=", 1)[0]  # an attribute's str


class Parts:
    def split(self, sep: str) -> list[str]:
        return [sep]


def name(line: str) -> str:
    return line.split("\t", 1)[0]


def word(s: str) -> str:
    return s.split()[0]


def field(s: str, sep: str | None, n: int) -> str:
    return s.split(sep, n)[0]  # (sep None: the first word)


def trimmed(s: str) -> str:
    return s.strip().split(",")[0]  # a call's str


def second(s: str) -> str:
    return s.split(",")[1]  # another item: the list


def other(p: Parts) -> str:
    return p.split(",")[0]  # another class's split


print(name("a\tb"), word(" c d"), field("e,f", ",", 1), trimmed(" g,h "), second("i,j"), other(Parts()), Record("k=l").key())
