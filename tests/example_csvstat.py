# examples/csvstat: the statistics of each column of 3,000 generated orders, which csv.writer writes
# to an object of the program's and csv.reader reads back as the lines of a file, as CPython prints
# them; then a file whose rows are shorter and longer than its header
import csv

import csvstat
import gencsv


class Lines:
    # what a writer writes, kept
    def __init__(self) -> None:
        self.parts: list[str] = []

    def write(self, s: str) -> int:
        self.parts.append(s)
        return 0


out = Lines()
gencsv.write(3000, out)
text = "".join(out.parts)
lines = text.splitlines(True)
print(len(out.parts), len(lines), text.count("\r\n"), lines[:3])
columns, count, longer = csvstat.collect(csv.reader(lines))
csvstat.report("orders", columns, count, longer)
csvstat.report_csv(columns)
columns, count, longer = csvstat.collect(csv.reader(["a,b,c", "1,x,", "2", "3,y,z,extra", "", "4.5,w,q\n"]))
csvstat.report("ragged", columns, count, longer)
csvstat.report_csv(columns)
