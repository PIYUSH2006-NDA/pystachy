"""Simple, brute-force N-Queens solver."""

# Pystachy port: pyperf is not imported; the main below replaces pyperf.Runner.

__author__ = "collinwinter@google.com (Collin Winter)"


# Pure-Python implementation of itertools.permutations().
# Pystachy port: there are no generator functions; permutations() and n_queens()
# return lists of the values they yielded.
def permutations(iterable, r=None):
    """permutations(range(3), 2) --> (0,1) (0,2) (1,0) (1,2) (2,0) (2,1)"""
    result = []  # Pystachy port: the yielded values
    pool = tuple(iterable)
    n = len(pool)
    if r is None:
        r = n
    indices = list(range(n))
    cycles = list(range(n - r + 1, n + 1))
    cycles.reverse()  # Pystachy port: for [::-1]; a slice step is not supported
    result.append(tuple([pool[i] for i in indices[:r]]))  # Pystachy port: for yield; tuple() of a list
    while n:
        for i in reversed(range(r)):
            cycles[i] -= 1
            if cycles[i] == 0:
                indices = indices[:i] + indices[i + 1:] + indices[i:i + 1]  # Pystachy port: no slice assignment
                cycles[i] = n - i
            else:
                j = cycles[i]
                indices[i], indices[-j] = indices[-j], indices[i]
                result.append(tuple([pool[i] for i in indices[:r]]))  # Pystachy port: for yield; tuple() of a list
                break
        else:
            return result  # Pystachy port: the values
    return result  # Pystachy port: the values


# From http://code.activestate.com/recipes/576647/
def n_queens(queen_count):
    """N-Queens solver.

    Args:
        queen_count: the number of queens to solve for. This is also the
            board size.

    Yields:
        Solutions to the problem. Each yielded value is looks like
        (3, 8, 2, 1, 4, ..., 6) where each number is the column position for the
        queen, and the index into the tuple indicates the row.
    """
    cols = list(range(queen_count))  # Pystachy port: a list; a range is not a value
    solutions = []  # Pystachy port: the yielded values
    for vec in permutations(cols):
        if (queen_count == len(set(vec[i] + i for i in cols))
                        == len(set(vec[i] - i for i in cols))):
            solutions.append(vec)  # Pystachy port: for yield
    return solutions  # Pystachy port: the values


def bench_n_queens(queen_count):
    return list(n_queens(queen_count))  # Pystachy port: returned, for the checksum


if __name__ == "__main__":
    # Pystachy port: a deterministic main replaces pyperf.Runner: argv[1] is the
    # number of runs, argv[2] the board size; the solutions are counted, and the
    # time goes to stderr.
    import sys
    import time
    loops = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    queen_count = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    t0 = time.perf_counter()
    for _ in range(loops):
        solutions = bench_n_queens(queen_count)
    print("seconds", time.perf_counter() - t0, file=sys.stderr)
    print("nqueens", loops, queen_count, len(solutions), solutions[0], solutions[-1])
