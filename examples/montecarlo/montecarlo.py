"""montecarlo: Monte Carlo estimates drawn from a seeded random.Random.

usage: python3 montecarlo.py [SEED [N]]
       pystachy build montecarlo.py -o montecarlo && ./montecarlo [SEED [N]]

From random.Random(SEED) (default 42), with N samples (default 1,000,000), it estimates:
- pi, from the share of N points of the unit square (random()) inside the quarter circle;
- the mean squared distance from the start of N // 1000 walks of 1000 steps on a square grid,
  each step a choice() of the four directions: 1000 for a walk of 1000 steps;
- the chance that two of 23 people share a birthday (randrange(365)) in N // 100 groups, which
  is 0.5072972343239857;
- a 95% interval of the mean of 200 gamma(2, 1.5) variates (gammavariate(); mean 3.0) by the
  bootstrap: the 2.5th and 97.5th percentiles of the means of N // 1000 resamples (choices()).
A seed draws the same numbers in every run, under CPython and compiled alike.
"""
import sys
from random import Random
from statistics import fmean

STEPS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def estimate_pi(rng: Random, n: int) -> float:
    inside = 0
    for _ in range(n):
        x = rng.random()
        y = rng.random()
        if x * x + y * y < 1.0:
            inside += 1
    return 4.0 * inside / n


def walk_distance(rng: Random, walks: int, steps: int) -> float:
    # the mean squared distance from the start after the steps of each walk
    total = 0
    for _ in range(walks):
        x = 0
        y = 0
        for _ in range(steps):
            dx, dy = rng.choice(STEPS)
            x += dx
            y += dy
        total += x * x + y * y
    return total / walks


def shared_birthday(rng: Random, groups: int, people: int) -> float:
    # the share of the groups in which two people have the same birthday
    shared = 0
    for _ in range(groups):
        seen: set[int] = set()
        for _ in range(people):
            day = rng.randrange(365)
            if day in seen:
                shared += 1
                break
            seen.add(day)
    return shared / groups


def exact_birthday(people: int) -> float:
    p = 1.0
    for i in range(people):
        p *= (365 - i) / 365
    return 1.0 - p


def bootstrap_mean(rng: Random, data: list[float], resamples: int) -> tuple[float, float]:
    # the 2.5th and 97.5th percentiles of the means of resamples of data, drawn with replacement
    means = [fmean(rng.choices(data, k=len(data))) for _ in range(resamples)]
    means.sort()
    return means[int(0.025 * resamples)], means[int(0.975 * resamples)]


def main(args: list[str]) -> int:
    if len(args) > 2:
        print("usage: montecarlo.py [SEED [N]]", file=sys.stderr)
        return 2
    seed = int(args[0]) if args else 42
    n = int(args[1]) if len(args) > 1 else 1000000
    if n < 1000:
        print("montecarlo.py: N must be at least 1000", file=sys.stderr)
        return 2
    rng = Random(seed)
    print(f"seed {seed}, N {n}")
    print("pi:", estimate_pi(rng, n))
    print("mean squared distance of 1000 steps:", walk_distance(rng, n // 1000, 1000))
    print("shared birthday among 23:", shared_birthday(rng, n // 100, 23), "exact",
          exact_birthday(23))
    data = [rng.gammavariate(2.0, 1.5) for _ in range(200)]
    low, high = bootstrap_mean(rng, data, n // 1000)
    print(f"mean of 200 gamma(2, 1.5) variates: {fmean(data):.4f}, 95% interval {low:.4f} to {high:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
