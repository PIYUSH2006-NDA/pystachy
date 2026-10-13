"""csvstat: the statistics of each column of a CSV file.

usage: python3 csvstat.py FILE [-d DELIMITER] [--csv]
       pystachy build csvstat.py -o csvstat && ./csvstat FILE [-d DELIMITER] [--csv]

The first row names the columns. A column's type is int where each of its values (its fields that
are not empty) is an int, else float where each is a number, else text. For each column it prints
the count of values and of empty fields, the count of distinct values, the most common value, and
the smallest and largest value: for a number column by number, with the mean, the median and the
standard deviation (of a sample); for a text column by the order of the characters. An int column
keeps its values as ints, so its least and largest are exact also past 2**53. A row shorter
than the header leaves the columns it lacks empty, and a row longer than it is counted.

--csv writes the statistics as CSV instead, one row per column, with csv.writer.
"""

import csv
import math
import sys


class Column:
    # the statistics of one column so far
    def __init__(self, name: str) -> None:
        self.name = name
        self.empty = 0
        self.counts: dict[str, int] = {}  # each distinct value, and how often it occurs
        self.isint = True
        self.isnumber = True
        self.ints: list[int] = []  # the values, while they are ints
        self.numbers: list[float] = []  # the values, while they are numbers and not all ints

    def add(self, value: str) -> None:
        if value == "":
            self.empty += 1
            return
        self.counts[value] = self.counts.get(value, 0) + 1
        if self.isint:
            try:
                self.ints.append(int(value))
                return
            except ValueError:
                self.isint = False
                self.numbers = [float(x) for x in self.ints]
                self.ints = []
        if self.isnumber:
            try:
                self.numbers.append(float(value))
            except ValueError:
                self.isnumber = False
                self.numbers = []

    def kind(self) -> str:
        if len(self.counts) == 0:
            return "empty"
        return "int" if self.isint else "float" if self.isnumber else "text"


def collect(rows) -> tuple[list[Column], int, int]:
    # the columns of rows, which a header row begins; the count of rows after it, and of those
    # longer than it
    columns: list[Column] = []
    header = True
    count = 0
    longer = 0
    for row in rows:
        if header:
            for name in row:
                columns.append(Column(name))
            header = False
            continue
        count += 1
        if len(row) > len(columns):
            longer += 1
        for i in range(len(columns)):
            columns[i].add(row[i] if i < len(row) else "")
    return columns, count, longer


def moments(xs: list[float]) -> tuple[float, float, float]:
    # the mean, the median and the standard deviation (of a sample) of sorted numbers
    n = len(xs)
    mean = math.fsum(xs) / n
    half = n // 2
    median = xs[half] if n % 2 == 1 else (xs[half - 1] + xs[half]) / 2
    stdev = 0.0
    if n > 1:
        stdev = math.sqrt(math.fsum([(x - mean) ** 2 for x in xs]) / (n - 1))
    return mean, median, stdev


def statistics(c: Column) -> list[str]:
    # type, values, empty, distinct, min, max, mean, median, stdev, top, top count
    values = 0
    top = ""
    most = 0
    for value, n in c.counts.items():
        values += n
        if n > most:
            top = value
            most = n
    out = [c.kind(), str(values), str(c.empty), str(len(c.counts))]
    if values > 0 and c.isint:
        # the least and largest exactly, and the others from each value's distance to the least,
        # which a float holds exactly while the column's range fits in its 53 bits (an int past
        # 2**53 does not fit in one)
        ints = sorted(c.ints)
        base = ints[0]
        mean, median, stdev = moments([float(x - base) for x in ints])
        out += [str(ints[0]), str(ints[-1]), f"{base + mean:.6g}", f"{base + median:.6g}", f"{stdev:.6g}"]
    elif values > 0 and c.isnumber:
        xs = sorted(c.numbers)
        mean, median, stdev = moments(xs)
        out += [f"{xs[0]:.6g}", f"{xs[-1]:.6g}", f"{mean:.6g}", f"{median:.6g}", f"{stdev:.6g}"]
    elif values > 0:
        out += [min(c.counts), max(c.counts), "", "", ""]
    else:
        out += ["", "", "", "", ""]
    return out + [top, str(most)]


NAMES = ["type", "values", "empty", "distinct", "min", "max", "mean", "median", "stdev", "top",
         "top count"]


def report(title: str, columns: list[Column], count: int, longer: int) -> None:
    more = f", {longer} rows longer than the header" if longer > 0 else ""
    print(f"{title}: {count} rows, {len(columns)} columns{more}")
    for i in range(len(columns)):
        stats = statistics(columns[i])
        print(f"{i + 1:3}. {columns[i].name}")
        for j in range(len(NAMES)):
            # (a text column's min, max and top as their repr: they may hold line breaks)
            if stats[j] != "" and stats[0] == "text" and j in [4, 5, 9]:
                print(f"{NAMES[j]:>13}: {stats[j]!r}")
            elif stats[j] != "":
                print(f"{NAMES[j]:>13}: {stats[j]}")


def report_csv(columns: list[Column]) -> None:
    w = csv.writer(sys.stdout, lineterminator="\n")
    w.writerow(["column"] + NAMES)
    for c in columns:
        w.writerow([c.name] + statistics(c))


def main() -> None:
    as_csv = False
    delimiter = ","
    paths: list[str] = []
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--csv":
            as_csv = True
        elif sys.argv[i] == "-d" and i + 1 < len(sys.argv):
            delimiter = sys.argv[i + 1]
            i += 1
        else:
            paths.append(sys.argv[i])
        i += 1
    if len(paths) != 1:
        print("usage: csvstat.py FILE [-d DELIMITER] [--csv]", file=sys.stderr)
        sys.exit(2)
    with open(paths[0], newline="") as f:
        columns, count, longer = collect(csv.reader(f, delimiter=delimiter))
    if as_csv:
        report_csv(columns)
    else:
        report(paths[0], columns, count, longer)


if __name__ == "__main__":
    main()
