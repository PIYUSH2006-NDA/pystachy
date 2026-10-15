"""
MathWorld: "Hundred-Dollar, Hundred-Digit Challenge Problems", Challenge #3.
http://mathworld.wolfram.com/Hundred-DollarHundred-DigitChallengeProblems.html

The Computer Language Benchmarks Game
http://benchmarksgame.alioth.debian.org/u64q/spectralnorm-description.html#spectralnorm

Contributed by Sebastien Loisel
Fixed by Isaac Gouy
Sped up by Josh Goldfoot
Dirtily sped up by Simon Descarpentries
Concurrency by Jason Stitt
"""

# Pystachy port: pyperf is not imported; the main below replaces pyperf.Runner.


DEFAULT_N = 130


def eval_A(i, j):
    return 1.0 / ((i + j) * (i + j + 1) // 2 + i + 1)


def eval_times_u(func, u):
    return [func((i, u)) for i in range(len(list(u)))]


def eval_AtA_times_u(u):
    return eval_times_u(part_At_times_u, eval_times_u(part_A_times_u, u))


def part_A_times_u(i_u):
    i, u = i_u
    partial_sum = 0.0  # Pystachy port: a float; a variable keeps its type in a loop
    for j, u_j in enumerate(u):
        partial_sum += eval_A(i, j) * u_j
    return partial_sum


def part_At_times_u(i_u):
    i, u = i_u
    partial_sum = 0.0  # Pystachy port: a float; a variable keeps its type in a loop
    for j, u_j in enumerate(u):
        partial_sum += eval_A(j, i) * u_j
    return partial_sum


def bench_spectral_norm(loops):
    range_it = list(range(loops))  # Pystachy port: a list; a range is not a value
    # t0 = pyperf.perf_counter()  # Pystachy port: the main times the loops

    for _ in range_it:
        u = [1.0] * DEFAULT_N  # Pystachy port: floats; u keeps its type in the loop

        for dummy in range(10):
            v = eval_AtA_times_u(u)
            u = eval_AtA_times_u(v)

        vBv = vv = 0.0  # Pystachy port: floats; they keep their type in the loop

        for ue, ve in zip(u, v):
            vBv += ue * ve
            vv += ve * ve

    return vBv / vv  # Pystachy port: the result, for the checksum; the main times the loops


if __name__ == "__main__":
    # Pystachy port: a deterministic main replaces pyperf.Runner: argv[1] is the
    # number of loops; the result is printed, and the time to stderr.
    import sys
    import time
    loops = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    t0 = time.perf_counter()
    result = bench_spectral_norm(loops)
    print("seconds", time.perf_counter() - t0, file=sys.stderr)
    print("spectral_norm", loops, result)
