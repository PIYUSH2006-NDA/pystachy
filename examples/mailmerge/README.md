# mailmerge: a message for each record of a data file, with string.Template

`mailmerge.py` renders a message template, its headers and body, for each record of a
tab-separated data file, and writes the messages as a mailbox (mbox) that a mail client opens: the
renewal notices of a billing system, an announcement to a list of members, any letter that differs
only in its fields. It is ordinary Python, which CPython runs as it is and Pystachy compiles as it
is, with [`lib/string`](../../lib/README.md#string-a-port-of-cpythons)'s `Template`: CPython's,
edited where the subset does not reach.

```
$ cat notice.txt
From: Billing <billing@example.com>
To: $name <$email>
Subject: Your $plan plan renews on $due

Dear $name,

your $plan plan (account $account) renews on ${due}. We will charge $$$amount
...
This is message $seq of $count.
$ python3 gendata.py 100000 > data.tsv      # name<TAB>email<TAB>account<TAB>plan<TAB>amount ...
$ python3 mailmerge.py notice.txt data.tsv > notices.mbox             # CPython
$ pystachy build mailmerge.py -o mailmerge && ./mailmerge notice.txt data.tsv > notices.mbox
mailmerge: 100000 messages
$ head -6 notices.mbox
From billing@example.com Tue Oct 13 00:00:00 2026
From: Billing <billing@example.com>
To: Niklaus Wirth <niklaus.wirth0@example.com>
Subject: Your Standard plan renews on 2026-11-17

Dear Niklaus Wirth,
```

CPython and the executable write the same mailbox. A record's fields are a dict, the mapping of
`substitute()`, and `$seq` and `$count`, the record's number and the number of records, its keyword
arguments, which come first. Before it renders a message, mailmerge checks the template with
`is_valid()` and `get_identifiers()`: an invalid placeholder (`5$ a month`) is reported with its
line and column, as `substitute()` reports it, and a placeholder that names no field of the data
ends the program, unless `--safe`, which renders with `safe_substitute()` and leaves such a
placeholder as it is. `--split` renders without `Template`: it splits the template once at its
placeholders, with `Template.pattern`, and joins each message of the pieces and the fields, the
way a program that knows its template is fixed renders it. `gendata.py` makes the records from a
linear congruential generator, so that the data is the same on every run.

## What Template costs

`bench.py`, on a 4-core x86-64 VM: median wall time of 7 runs with process start-up, and the peak
RSS of one run, on 100,000 records (7.9 MB of data, 47 MB of mailbox):

| mode | CPython 3.13.16 | Pystachy AOT | speedup | CPython RSS | AOT RSS |
|---|---:|---:|---:|---:|---:|
| `substitute()` | 1.265 s | 0.969 s | 1.30x | 10.9 MB | 36.5 MB |
| `--safe`, `safe_substitute()` | 1.249 s | 0.933 s | 1.34x | 11.0 MB | 36.5 MB |
| `--split` | 0.389 s | 0.292 s | 1.33x | 11.0 MB | 36.2 MB |

- **`Template` is most of the time, compiled or not**: `substitute()` scans the 430-character
  template with its regular expression at each call and calls back for each of its 14
  placeholders, which takes about 7 µs of each message's 10 µs in the executable (9 of 13 in
  CPython); splitting the template once renders 3.3 times as fast in both.
- **Compiled, each mode is 1.3 times as fast as CPython.** `lib/re`'s engine, the subset's port of
  `_sre`, scans the template more slowly than CPython's C engine (a `substitute()` of a dict alone
  takes 5.8 µs, against CPython's 4.6 µs), but a call with keyword arguments is faster (6.1 µs,
  against 7.3 µs), as the port looks a name up in the keywords, then in the dict, where CPython
  builds a `collections.ChainMap` of the two at each call; reading, splitting and writing the
  records are faster too.
- **Memory stays bounded**, as mailmerge reads one record at a time (a version that read every
  record into a list first was slower than CPython compiled, 2.1 s against 1.4 s, as the
  collector scanned the growing heap); the executable's peak is 3 times CPython's, Pystachy's
  collector running when its heap has grown.
- Building the executable takes about 3 s, most of it `lib/re` (3,500 lines of the subset).

## Tests

`tests/example_mailmerge.py` renders 150 generated records in-process with `substitute()`,
`safe_substitute()` and the split template, checks a valid template, an invalid one and one that
names a missing field, and compares the messages and the reports with CPython's
(`tests/example_mailmerge.path` puts this directory on the module path). `bench.py` runs the table
above: `python3 -I bench.py ../../pystachy 7`, from anywhere; it writes its data and executable to
`build/mailmerge/`.
