# Documented deviations of lib/csv (Pystachy's csv, after CPython 3.13's Modules/_csv.c and
# Lib/csv.py) from CPython 3.13.
import csv

# A reader parses all of its input when its iteration starts (CPython's reader is an iterator,
# which parses a row at each step): an error in the data is raised before the loop sees a row, and
# line_num is the last line's during the loop. CPython prints 0, ['a', 'b'], ['c', 'd'], then the
# error with line_num 3; and ['x'] 1, ['y'] 2, ['z'] 3
r = csv.reader(["a,b", "c,d", '"e'], strict=True)
print(r.line_num)
try:
    for row in r:
        print(row)
except csv.Error as e:
    print("Error:", e, r.line_num)
r = csv.reader(["x", "y", "z"])
for row in r:
    print(row, r.line_num)

# Once its first iteration has begun, a reader has no rows left for another one, also where that
# iteration stopped early. CPython prints ['h1', 'h2'] [['1', '2'], ['3', '4']]
r = csv.reader(["h1,h2", "1,2", "3,4"])
header: list[str] = []
for header in r:
    break
print(header, [row for row in r])

# A row is a list[str]: QUOTE_NONNUMERIC and QUOTE_STRINGS, whose reader makes floats of the
# unquoted fields, are refused when the reader is made, and QUOTE_NOTNULL's None of an empty
# unquoted field raises where its row ends. CPython prints [[1.0, 'a', 2.5]], [[1.0, 'a', None]]
# and [['a', None, '', 'b']]
try:
    print(list(csv.reader(['1,"a",2.5'], quoting=csv.QUOTE_NONNUMERIC)))
except NotImplementedError as e:
    print("NotImplementedError:", e)
try:
    print(list(csv.reader(['1,"a",'], quoting=csv.QUOTE_STRINGS)))
except NotImplementedError as e:
    print("NotImplementedError:", e)
try:
    print(list(csv.reader(['a,,"",b'], quoting=csv.QUOTE_NOTNULL)))
except NotImplementedError as e:
    print("NotImplementedError:", e)

# A DictReader's row is a dict[str, str]: the fields of a row longer than fieldnames (a list under
# restkey) and the restval None of a short row raise. CPython prints
# [{'a': '1', 'b': '2', None: ['3']}] and [{'a': '1', 'b': '2', 'c': None}]
try:
    print(list(csv.DictReader(["a,b", "1,2,3"])))
except NotImplementedError as e:
    print("NotImplementedError:", e)
try:
    print(list(csv.DictReader(["a,b,c", "1,2"])))
except NotImplementedError as e:
    print("NotImplementedError:", e)

# A DictReader reads its rows, and its header, when it is made: line_num is then the header's,
# fieldnames assigned afterwards renames the fields of the rows after the header, and an error in
# the data is raised by the constructor. CPython prints 0,
# [{'H1': 'h1', 'H2': 'h2'}, {'H1': '1', 'H2': '2'}] and made
dr = csv.DictReader(["h1,h2", "1,2"])
print(dr.line_num)
dr.fieldnames = ["H1", "H2"]
print(list(dr))
try:
    csv.DictReader(["a,b", '"c'], strict=True)
    print("made")
except csv.Error as e:
    print("Error:", e)

# excel, excel_tab and unix_dialect are Dialect objects (CPython's are classes, subclasses of
# csv.Dialect), and a Dialect's fields can be assigned (CPython's _csv.Dialect is read-only).
# CPython prints False and AttributeError: attribute 'delimiter' of '_csv.Dialect' objects is not
# writable
print(isinstance(csv.excel, csv.Dialect))
d = csv.get_dialect("unix")
try:
    d.delimiter = ";"
    print("assigned", csv.get_dialect("unix").delimiter)
    d.delimiter = ","
except AttributeError as e:
    print("AttributeError:", e)

# csv.Error is the class of module csv, which an uncaught error names; CPython's is _csv.Error
print(list(csv.reader(['"x'], strict=True)))
