# csvstat: the statistics of each column of a CSV file

`csvstat.py` reads a CSV file whose first row names its columns, and prints for each column the
type its values have (int, float or text), the count of values, of empty fields and of distinct
values, the most common value, the smallest and largest value, and for a number column its mean,
median and standard deviation; `--csv` writes the same statistics as CSV. It is ordinary Python,
which CPython runs as it is and Pystachy compiles as it is, with Pystachy's own `csv`
([`lib/csv.py`](../../lib/README.md#csv-pystachys-own)): `csv.reader` reads the file, `csv.writer`
writes `--csv`'s table, and `gencsv.py` writes its input with `csv.writer` too.

```
$ python3 gencsv.py 200000 > orders.csv        # 16 MB: order,date,customer,city,product,...
$ head -3 orders.csv
order,date,customer,city,product,quantity,unit_price,discount,status,note
1,2026-06-18,"García, Mateo","Washington, D.C.","Cable, 2 m",6,89.36,,delivered,
2,2026-01-24,"Smith, Farah",New York,Lamp,3,200.13,0.15,returned,
$ python3 csvstat.py orders.csv                # CPython
$ pystachy build csvstat.py -o csvstat && ./csvstat orders.csv
orders.csv: 200000 rows, 10 columns
  1. order
         type: int
       values: 200000
        empty: 0
     distinct: 200000
          min: 1
          max: 200000
         mean: 100000
       median: 100000
        stdev: 57735.2
          top: 1
    top count: 1
  ...
  7. unit_price
         type: float
       values: 200000
  ...
$ ./csvstat orders.csv --csv
column,type,values,empty,distinct,min,max,mean,median,stdev,top,top count
order,int,200000,0,200000,1,200000,100000,100000,57735.2,1,1
date,text,200000,0,365,2026-01-01,2026-12-31,,,,2026-02-17,657
customer,text,200000,0,298,"Dubois, Ana","Tanaka, Tariq",,,,"Smith, Ines",1976
...
```

CPython and the executable print the same report. The orders hold what makes CSV more than
`line.split(",")`: a customer is `"Last, First"`, some cities and products hold commas or quotes
(`"Ruler 12"""`), and a tenth of the orders has a note, some of which span lines. `gencsv.py`
draws them from a linear congruential generator, so the file is the same on every run, and the
executable it compiles to writes the same bytes.

## What compiling buys

`bench.py`, on a 4-core x86-64 VM shared with other work: the median wall time of 11 runs of
csvstat, with process start-up, and the peak RSS of one, on the 200,000 orders (16.1 MB); and the
medians of 11 runs of `rwbench.py`'s times per row for `csv.reader` reading the file and parsing
its lines already in memory, and for `csv.writer` writing the rows to a file:

| | CPython 3.13.16 | Pystachy AOT | speedup |
|---|---:|---:|---:|
| `csvstat.py orders.csv` | 0.825 s | 0.414 s | 2.0× |
| `csvstat.py orders.csv --csv` | 0.774 s | 0.373 s | 2.1× |
| peak RSS | 65.7 MB | 162.2 MB | |
| `csv.reader`, from the file | 1.333 µs/row | 0.850 µs/row | 1.6× |
| `csv.reader`, from lines in memory | 1.221 µs/row | 0.713 µs/row | 1.7× |
| `csv.writer`, to a file | 1.207 µs/row | 0.755 µs/row | 1.6× |

- **Compiled, csvstat is twice as fast as CPython.** Of its 2.1 µs a row, `csv.reader` takes 0.85
  (0.71 of them parsing the lines, the rest reading them); the rest is csvstat's own work per
  field: a dict of each column's values, `int()` and `float()` of the numbers, and sorting each
  number column for its median.
- **The csv module reads and writes 1.6 to 1.7 times as fast as CPython's C one**: `_csv` adds a
  field's characters one by one to a buffer, where Pystachy's state machine takes each run of plain
  characters as one slice of the line, found with `str.find()`, and the writer joins a line's
  pieces once.
- **The executable's peak memory is about 2.5 times CPython's**: Pystachy's reader parses the
  whole file when its iteration starts and holds its rows in a list, where CPython's parses a row
  at each step and frees it once used ([`lib/README.md`](../../lib/README.md#csv-pystachys-own)), and
  Pystachy's collector runs when its heap has grown.
- On this VM, a run's times can differ from another's by 20% or more, which the medians of 11 runs
  smooth; CPython's and the executable's runs are taken in turn, after an untimed one of each.
  Building the executable takes under 2 s.

## Tests

`tests/example_csvstat.py` writes 3,000 orders with `gencsv.write()` to an object of its own,
reads them back with `csv.reader` as the lines of a file, and prints csvstat's report and CSV
table, then those of a file with rows shorter and longer than its header, as CPython prints them
(`tests/example_csvstat.path` puts this directory on the module path). `bench.py` runs the table
above: `python3 -I bench.py ../../pystachy 11`, from anywhere; it writes the file and the
executables to `build/csvstat/`.
