#!/usr/bin/env python
"""
The Computer Language Benchmarks Game
http://benchmarksgame.alioth.debian.org/

regex-dna Python 3 #5 program:
contributed by Dominique Wahli
2to3
modified by Justin Peel

fasta Python 3 #3 program:
modified by Ian Osgood
modified again by Heinrich Acker
modified by Justin Peel
Modified by Christopher Sean Forgeron
"""

import bisect
import re

# Pystachy port: pyperf is not imported; the main below replaces pyperf.Runner.


# Pystachy port: there are no bytes or bytearray: the sequence is a str (ASCII), the
# generator builds lists of str, and the patterns are str patterns. Each edit is marked.

DEFAULT_INIT_LEN = 100000
DEFAULT_RNG_SEED = 42

ALU = ('GGCCGGGCGCGGTGGCTCACGCCTGTAATCCCAGCACTTTGG'
       'GAGGCCGAGGCGGGCGGATCACCTGAGGTCAGGAGTTCGAGA'
       'CCAGCCTGGCCAACATGGTGAAACCCCGTCTCTACTAAAAAT'
       'ACAAAAATTAGCCGGGCGTGGTGGCGCGCGCCTGTAATCCCA'
       'GCTACTCGGGAGGCTGAGGCAGGAGAATCGCTTGAACCCGGG'
       'AGGCGGAGGTTGCAGTGAGCCGAGATCGCGCCACTGCACTCC'
       'AGCCTGGGCGACAGAGCGAGACTCCGTCTCAAAAA')

IUB = list(zip('acgtBDHKMNRSVWY', [0.27, 0.12, 0.12, 0.27] + [0.02] * 11))

HOMOSAPIENS = [
    ('a', 0.3029549426680),
    ('c', 0.1979883004921),
    ('g', 0.1975473066391),
    ('t', 0.3015094502008),
]


def make_cumulative(table):
    P = []
    C = []
    prob = 0.
    for char, p in table:
        prob += p
        P += [prob]
        C += [char]  # Pystachy port: the char, for a str line (was ord(char))
    return (P, C)


def repeat_fasta(src, n, nprint):
    width = 60

    is_trailing_line = False
    count_modifier = 0.0

    len_of_src = len(src)
    ss = src + src + src[:n % len_of_src]
    # CSF - It's faster to work with a bytearray than a string
    s = ss  # Pystachy port: the str (was bytearray(ss, encoding='utf8'))

    if n % width:
        # We don't end on a 60 char wide line
        is_trailing_line = True
        count_modifier = 1.0

    # CSF - Here we are stuck with using an int instead of a float for the loop,
    # but testing showed it still to be faster than a for loop
    count = 0
    end = (n / float(width)) - count_modifier
    while count < end:
        i = count * 60 % len_of_src
        nprint(s[i:i + 60] + '\n')  # Pystachy port: str
        count += 1
    if is_trailing_line:
        nprint(s[-(n % width):] + '\n')  # Pystachy port: str


def random_fasta(table, n, seed, nprint):
    width = 60
    r = list(range(width))  # Pystachy port: a list; a range is not a value
    bb = bisect.bisect

    # If we don't have a multiple of the width, then we will have a trailing
    # line, which needs a slightly different approach
    is_trailing_line = False
    count_modifier = 0.0

    line = [''] * (width + 1)  # Pystachy port: a list of str (was bytearray(width + 1))

    probs, chars = make_cumulative(table)

    # pRNG Vars
    im = 139968.0
    seed = float(seed)

    if n % width:
        # We don't end on a 60 char wide line
        is_trailing_line = True
        count_modifier = 1.0

    # CSF - Loops with a high iteration count run faster as a while/float loop.
    count = 0.0
    end = (n / float(width)) - count_modifier
    while count < end:
        # CSF - Low iteration count loops may run faster as a for loop.
        for i in r:
            # CSF - Python is faster for all float math than it is for int, on my
            # machine at least.
            seed = (seed * 3877.0 + 29573.0) % 139968.0
            # CSF - While real values, not variables are faster for most things, on my
            # machine, it's faster to have 'im' already in a var
            line[i] = chars[bb(probs, seed / im)]

        line[60] = '\n'   # End of Line  # Pystachy port: str (was 10)
        nprint(''.join(line))  # Pystachy port: the line's str
        count += 1.0

    if is_trailing_line:
        for i in range(n % width):
            seed = (seed * 3877.0 + 29573.0) % 139968.0
            line[i] = chars[bb(probs, seed / im)]

        nprint(''.join(line[:i + 1]) + "\n")  # Pystachy port: str

    return seed


def init_benchmarks(n, rng_seed):
    result: list[str] = []  # Pystachy port: a list of str (was bytearray())
    nprint = result.append  # Pystachy port: (was result.extend)
    nprint('>ONE Homo sapiens alu\n')  # Pystachy port: str
    repeat_fasta(ALU, n * 2, nprint=nprint)

    # We need to keep track of the state of 'seed' so we pass it in, and return
    # it back so our output can pass the diff test
    nprint('>TWO IUB ambiguity codes\n')  # Pystachy port: str
    seed = random_fasta(IUB, n * 3, seed=rng_seed, nprint=nprint)

    nprint('>THREE Homo sapiens frequency\n')  # Pystachy port: str
    random_fasta(HOMOSAPIENS, n * 5, seed, nprint=nprint)

    return ''.join(result)  # Pystachy port: str (was bytes(result))


# Pystachy port: str patterns (were bytes)
VARIANTS = (
    'agggtaaa|tttaccct',
    '[cgt]gggtaaa|tttaccc[acg]',
    'a[act]ggtaaa|tttacc[agt]t',
    'ag[act]gtaaa|tttac[agt]ct',
    'agg[act]taaa|ttta[agt]cct',
    'aggg[acg]aaa|ttt[cgt]ccct',
    'agggt[cgt]aa|tt[acg]accct',
    'agggta[cgt]a|t[acg]taccct',
    'agggtaa[cgt]|[acg]ttaccct',
)

# Pystachy port: str patterns (were bytes)
SUBST = (
    ('B', '(c|g|t)'), ('D', '(a|g|t)'), ('H', '(a|c|t)'),
    ('K', '(g|t)'), ('M', '(a|c)'), ('N', '(a|c|g|t)'),
    ('R', '(a|g)'), ('S', '(c|g)'), ('V', '(a|c|g)'),
    ('W', '(a|t)'), ('Y', '(c|t)'),
)


def run_benchmarks(seq):
    ilen = len(seq)

    seq = re.sub('>.*\n|\n', '', seq)  # Pystachy port: str patterns
    clen = len(seq)

    results = []
    for f in VARIANTS:
        results.append(len(re.findall(f, seq)))

    for f, r in SUBST:
        seq = re.sub(f, r, seq)

    return results, ilen, clen, len(seq)


def bench_regex_dna(loops, seq, expected_res):
    range_it = list(range(loops))  # Pystachy port: a list; a range is not a value
    # t0 = pyperf.perf_counter()  # Pystachy port: the main times the loops

    for i in range_it:
        res = run_benchmarks(seq)

    # dt = pyperf.perf_counter() - t0  # Pystachy port: (see above)
    if (expected_res is not None) and (res != expected_res):
        raise Exception("run_benchmarks() error")

    return res  # Pystachy port: the results, for the checksum; the main times the loops


def add_cmdline_args(cmd, args):
    cmd.extend(("--fasta-length", str(args.fasta_length),
                "--rng-seed", str(args.rng_seed)))


if __name__ == '__main__':
    # Pystachy port: a deterministic main replaces pyperf.Runner: argv[1] is the
    # number of loops, argv[2] the fasta length; the results are printed, and the
    # time of the loops goes to stderr.
    import sys
    import time
    loops = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    fasta_length = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_INIT_LEN
    expected_len: int | None = None
    expected_res: tuple[list[int], int, int, int] | None = None
    if fasta_length == 100000:
        expected_len = 1016745
        expected_res = ([6, 26, 86, 58, 113, 31, 31, 32, 43],
                        1016745, 1000000, 1336326)

    seq = init_benchmarks(fasta_length, DEFAULT_RNG_SEED)
    if (expected_len is not None) and (len(seq) != expected_len):
        raise Exception("init_benchmarks() error")

    t0 = time.perf_counter()
    result = bench_regex_dna(loops, seq, expected_res)
    print("seconds", time.perf_counter() - t0, file=sys.stderr)
    print("regex_dna", loops, fasta_length, result)
