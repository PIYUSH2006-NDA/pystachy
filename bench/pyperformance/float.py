"""
Artificial, floating point-heavy benchmark originally used by Factor.
"""
# Pystachy port: pyperf is not imported; the main below replaces pyperf.Runner.

from math import sin, cos, sqrt


POINTS = 100000


class Point(object):
    __slots__ = ('x', 'y', 'z')

    def __init__(self, i: int):  # Pystachy port: annotated
        x = sin(i)  # Pystachy port: for 'self.x = x = sin(i)', to annotate the field
        self.x: float = x
        self.y: float = cos(i) * 3  # Pystachy port: annotated
        self.z: float = (x * x) / 2  # Pystachy port: annotated

    def __repr__(self):
        return "<Point: x=%s, y=%s, z=%s>" % (self.x, self.y, self.z)

    def normalize(self):
        x = self.x
        y = self.y
        z = self.z
        norm = sqrt(x * x + y * y + z * z)
        self.x /= norm
        self.y /= norm
        self.z /= norm

    def maximize(self, other):
        self.x = self.x if self.x > other.x else other.x
        self.y = self.y if self.y > other.y else other.y
        self.z = self.z if self.z > other.z else other.z
        return self


def maximize(points):
    next = points[0]
    for p in points[1:]:
        next = next.maximize(p)
    return next


def benchmark(n):
    points: list[Point | None] = [None] * n  # Pystachy port: annotated
    for i in range(n):
        points[i] = Point(i)
    for p in points:
        p.normalize()
    return maximize(points)


if __name__ == "__main__":
    # Pystachy port: a deterministic main replaces pyperf.Runner: argv[1] is the
    # number of runs, argv[2] the number of points; the result is printed, and the
    # time to stderr.
    import sys
    import time
    loops = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    n = int(sys.argv[2]) if len(sys.argv) > 2 else POINTS
    t0 = time.perf_counter()
    for _ in range(loops):
        result = benchmark(n)
    print("seconds", time.perf_counter() - t0, file=sys.stderr)
    print("float", loops, n, result)
